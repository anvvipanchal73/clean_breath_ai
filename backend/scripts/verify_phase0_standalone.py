"""
Standalone Phase 0 verification – runs WITHOUT pydantic/fastapi installed.
Tests the pure-logic functions extracted from risk_classifier.py and
impact_engine.py using only Python stdlib.

Usage:  python3 tests/test_phase0_standalone.py
"""
import json
import math
import sys
from pathlib import Path

PASS = 0
FAIL = 0
ERRORS: list[str] = []


def ok(name: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ PASS  {name}")


def fail(name: str, detail: str) -> None:
    global FAIL
    FAIL += 1
    ERRORS.append(f"{name}: {detail}")
    print(f"  ❌ FAIL  {name} – {detail}")


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        ok(name)
    else:
        fail(name, detail or "assertion failed")


# ---------------------------------------------------------------------------
# Inline copies of the pure functions (no Pydantic, identical logic)
# ---------------------------------------------------------------------------

THRESHOLDS = [(50.0, "Green"), (100.0, "Yellow"), (150.0, "Orange"), (200.0, "Red")]
TIER_ORDER = ["Green", "Yellow", "Orange", "Red", "Maroon"]


def base_risk_level(aqi: float) -> str:
    for threshold, level in THRESHOLDS:
        if aqi <= threshold:
            return level
    return "Maroon"


def shift_one_tier_stricter(level: str) -> str:
    idx = TIER_ORDER.index(level)
    return TIER_ORDER[min(idx + 1, len(TIER_ORDER) - 1)]


def pm25_to_aqi_approx(pm25: float) -> float:
    breakpoints = [
        (0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200), (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500),
    ]
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo, 1)
    return 500.0


def coarse_coords(lat: float, lon: float, decimals: int = 2):
    factor = 10 ** decimals
    return math.floor(lat * factor) / factor, math.floor(lon * factor) / factor


# Load impact factors
FACTORS_PATH = Path(__file__).parent.parent / "app" / "data" / "impact_factors.v1.json"


def load_factors() -> dict:
    with open(FACTORS_PATH, encoding="utf-8") as f:
        return json.load(f)


def calc_commute_impact_simple(
    factors: dict,
    current_mode: str,
    new_mode: str,
    daily_km: float,
) -> dict:
    t = factors["transport"]
    cur = t.get(current_mode, {})
    new = t.get(new_mode, {})
    pm25_saved = max((cur.get("pm25_ug_per_km", 0) - new.get("pm25_ug_per_km", 0)) * daily_km, 0)
    co2_saved_g = max((cur.get("co2_g_per_km", 0) - new.get("co2_g_per_km", 0)) * daily_km, 0)
    money = max((cur.get("fuel_cost_inr_per_km", 0) - new.get("fuel_cost_inr_per_km", 0)) * daily_km, 0)
    return {"pm25": pm25_saved, "co2_kg": co2_saved_g / 1000, "money": money}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

print("\n=== CleanBreath AI Phase 0 – Standalone Verification ===\n")
print("--- Risk Classifier ---")

# AQI breakpoints
for aqi, expected in [
    (0, "Green"), (25, "Green"), (50, "Green"),
    (51, "Yellow"), (100, "Yellow"),
    (101, "Orange"), (150, "Orange"),
    (151, "Red"), (200, "Red"),
    (201, "Maroon"), (500, "Maroon"),
]:
    check(f"AQI {aqi} → {expected}", base_risk_level(aqi) == expected,
          f"got {base_risk_level(aqi)}")

# Sensitive group shift
for aqi, expected_base, expected_eff in [
    (50, "Green", "Yellow"), (100, "Yellow", "Orange"),
    (150, "Orange", "Red"), (200, "Red", "Maroon"),
    (300, "Maroon", "Maroon"),  # capped
]:
    base = base_risk_level(aqi)
    eff = shift_one_tier_stricter(base)
    check(f"Sensitive shift AQI {aqi}: {expected_base}→{expected_eff}",
          base == expected_base and eff == expected_eff,
          f"base={base} eff={eff}")

# PM2.5 → AQI
print("\n--- PM2.5 → AQI approximation ---")
for pm25, lo, hi in [
    (5.0, 0, 50), (20.0, 51, 100), (45.0, 101, 150),
    (90.0, 151, 200), (160.0, 201, 300), (300.0, 301, 500),
]:
    aqi_val = pm25_to_aqi_approx(pm25)
    check(f"PM2.5={pm25} → AQI in [{lo},{hi}]", lo <= aqi_val <= hi, f"got {aqi_val}")

# Coarse coordinates
print("\n--- Coordinate coarsening ---")
c_lat, c_lon = coarse_coords(28.6139, 77.2090)
check("coarse_lat precision ≤ 2 dp", len(str(c_lat).split(".")[-1]) <= 2, f"got {c_lat}")
check("coarse_lon precision ≤ 2 dp", len(str(c_lon).split(".")[-1]) <= 2, f"got {c_lon}")

# ---------------------------------------------------------------------------
# Impact Engine
# ---------------------------------------------------------------------------
print("\n--- Impact Engine (factor file) ---")

factors = load_factors()
check("factors file loads", bool(factors), "empty JSON")
check("version field present", "_meta" in factors and "version" in factors["_meta"])
check("transport key present", "transport" in factors)
check("cooking key present", "cooking" in factors)
check("indoor_air key present", "indoor_air" in factors)

# car_petrol → metro savings
result = calc_commute_impact_simple(factors, "car_petrol", "public_transit_metro", 30.0)
check("car→metro PM2.5 saved > 0", result["pm25"] > 0, f"pm25={result['pm25']}")
check("car→metro CO2 saved > 0", result["co2_kg"] > 0, f"co2={result['co2_kg']}")
check("car→metro money saved > 0", result["money"] > 0, f"money={result['money']}")

# cycle has zero emissions
cycle = factors["transport"]["cycle"]
check("cycle PM2.5 = 0", cycle["pm25_ug_per_km"] == 0.0)
check("cycle CO2 = 0", cycle["co2_g_per_km"] == 0.0)

# biomass >> LPG emissions
biomass_pm = factors["cooking"]["biomass_chulha"]["pm25_mg_per_mj"]
lpg_pm = factors["cooking"]["lpg"]["pm25_mg_per_mj"]
check("biomass PM2.5/MJ >> LPG", biomass_pm > lpg_pm * 10, f"biomass={biomass_pm} lpg={lpg_pm}")

# CADR formula
room_vol = 50.0
min_cadr = room_vol * factors["indoor_air"]["cadr_per_m3_room_volume_ratio"]
check("CADR formula: 50m³ room → ≥37 m³/h", min_cadr >= 37, f"got {min_cadr}")

# Corsi-Rosenthal
cr = factors["indoor_air"]["corsi_rosenthal_box"]
check("Corsi-Rosenthal CADR ≥ 200", cr["estimated_cadr_m3_per_hour"] >= 200)
check("Corsi-Rosenthal PM2.5 reduction > 0", cr["pm25_reduction_pct_in_room"] > 0)

# Assumptions / sources present
for mode in ["car_petrol", "car_diesel", "car_cng", "car_electric", "motorcycle", "cycle"]:
    entry = factors["transport"].get(mode, {})
    check(f"transport.{mode} has sources", bool(entry.get("sources")))

# ---------------------------------------------------------------------------
# Impact factors JSON schema check
# ---------------------------------------------------------------------------
print("\n--- JSON schema checks ---")
required_transport_keys = {"pm25_ug_per_km", "co2_g_per_km", "fuel_cost_inr_per_km"}
for mode, entry in factors["transport"].items():
    if mode.startswith("_"):
        continue
    missing = required_transport_keys - set(entry.keys())
    check(f"transport.{mode} has required keys", not missing, f"missing {missing}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed")
if ERRORS:
    print("\nFailed tests:")
    for e in ERRORS:
        print(f"  ❌ {e}")
print()
sys.exit(0 if FAIL == 0 else 1)
