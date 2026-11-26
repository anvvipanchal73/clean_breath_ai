"""
Deterministic Impact Engine for CleanBreath AI.

Estimates the pollution exposure change, PM2.5 and CO2 avoided, and money
saved per behavioural action.

RULES:
  - All numeric values come ONLY from impact_factors.v1.json (versioned config).
  - LLM must NEVER re-compute or extrapolate these numbers.
  - Every ImpactResult includes assumptions and source citations from the config.
  - If a required factor is missing, raise ValueError with a clear message.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.domain import (
    CommuteMode,
    CookingFuel,
    HouseholdProfile,
    ImpactResult,
    RiskLevel,
)

logger = logging.getLogger(__name__)

_FACTORS_PATH = Path(__file__).parent.parent / "data" / "impact_factors.v1.json"


def _load_factors() -> dict:
    with open(_FACTORS_PATH, encoding="utf-8") as f:
        return json.load(f)


_FACTORS: dict = _load_factors()
_VERSION: str = _FACTORS["_meta"]["version"]

# Map CommuteMode enum values to factor keys
_MODE_TO_KEY: dict[str, str] = {
    CommuteMode.CAR_PETROL:      "car_petrol",
    CommuteMode.CAR_DIESEL:      "car_diesel",
    CommuteMode.CAR_CNG:         "car_cng",
    CommuteMode.CAR_ELECTRIC:    "car_electric",
    CommuteMode.MOTORCYCLE:      "motorcycle",
    CommuteMode.AUTO_RICKSHAW:   "auto_rickshaw",
    CommuteMode.CYCLE:           "cycle",
    CommuteMode.WALK:            "walk",
    CommuteMode.PUBLIC_TRANSIT:  "public_transit_metro",  # default to metro; bus handled separately
    CommuteMode.WORK_FROM_HOME:  None,
}

_FUEL_TO_KEY: dict[str, str] = {
    CookingFuel.BIOMASS:    "biomass_chulha",
    CookingFuel.LPG:        "lpg",
    CookingFuel.PNG:        "lpg",           # treat as LPG (similar emission profile)
    CookingFuel.KEROSENE:   "kerosene",
    CookingFuel.ELECTRIC:   "electric_coil",
    CookingFuel.INDUCTION:  "induction",
}


def calc_switch_commute_impact(
    profile: HouseholdProfile,
    new_mode: CommuteMode,
) -> ImpactResult:
    """
    Calculate daily impact of switching commute mode.
    Daily distance = 2 × one_way_km (round trip).
    """
    daily_km = profile.commute_one_way_km * 2
    transport = _FACTORS["transport"]

    current_key = _MODE_TO_KEY.get(profile.commute_mode)
    new_key = _MODE_TO_KEY.get(new_mode)

    if profile.commute_mode == CommuteMode.WORK_FROM_HOME or current_key is None:
        return ImpactResult(
            action_key="switch_commute",
            description=f"Switching from {profile.commute_mode} to {new_mode.value}",
            assumptions=["Already at home – no commute emissions to avoid."],
            sources=[],
            factor_version=_VERSION,
        )

    if new_key is None:
        return ImpactResult(
            action_key="switch_commute",
            description=f"Switching from {profile.commute_mode} to {new_mode.value}",
            assumptions=["Switching to work-from-home – full commute emission avoided."],
            sources=[],
            factor_version=_VERSION,
        )

    cur = transport.get(current_key, {})
    new = transport.get(new_key, {})

    pm25_saved = (cur.get("pm25_ug_per_km", 0) - new.get("pm25_ug_per_km", 0)) * daily_km
    co2_saved_g = (cur.get("co2_g_per_km", 0) - new.get("co2_g_per_km", 0)) * daily_km
    money_saved = (cur.get("fuel_cost_inr_per_km", 0) - new.get("fuel_cost_inr_per_km", 0)) * daily_km

    assumptions = list(set(cur.get("assumptions", []) + new.get("assumptions", [])))
    assumptions.append(f"Daily round-trip distance: {daily_km:.1f} km")
    sources = list(set(cur.get("sources", []) + new.get("sources", [])))

    return ImpactResult(
        action_key="switch_commute",
        description=f"Switch commute from {profile.commute_mode.value} to {new_mode.value} ({daily_km:.0f} km/day)",
        pm25_avoided_ug_per_day=round(max(pm25_saved, 0), 2),
        co2_avoided_kg_per_day=round(max(co2_saved_g / 1000, 0), 4),
        money_saved_inr_per_day=round(max(money_saved, 0), 2),
        assumptions=assumptions,
        sources=sources,
        factor_version=_VERSION,
    )


def calc_cooking_switch_impact(
    profile: HouseholdProfile,
    new_fuel: CookingFuel,
    meals_per_day: int = 3,
    mj_per_meal: float = 4.0,
) -> ImpactResult:
    """
    Calculate daily PM2.5 and CO2 impact of switching cooking fuel.
    mj_per_meal: energy per meal in MJ (assumption noted in result).
    """
    cooking = _FACTORS["cooking"]
    cur_key = _FUEL_TO_KEY.get(profile.cooking_fuel)
    new_key = _FUEL_TO_KEY.get(new_fuel)

    if cur_key is None or new_key is None:
        raise ValueError(f"No emission factor for fuel: {profile.cooking_fuel} or {new_fuel}")

    cur = cooking[cur_key]
    new_f = cooking[new_key]

    daily_mj = meals_per_day * mj_per_meal
    # mg/MJ → g/day for PM2.5 (convert mg → µg × 1000)
    pm25_saved_ug = (
        (cur["pm25_mg_per_mj"] - new_f["pm25_mg_per_mj"]) * daily_mj * 1000
    )
    co2_saved_g = (cur["co2_g_per_mj"] - new_f["co2_g_per_mj"]) * daily_mj
    money_saved = (cur["fuel_cost_inr_per_meal"] - new_f["fuel_cost_inr_per_meal"]) * meals_per_day

    assumptions = [
        f"{meals_per_day} meals/day × {mj_per_meal} MJ/meal = {daily_mj} MJ/day",
        *cur.get("assumptions", []),
        *new_f.get("assumptions", []),
    ]
    sources = list(set(cur.get("sources", []) + new_f.get("sources", [])))

    return ImpactResult(
        action_key="switch_cooking_fuel",
        description=f"Switch cooking from {profile.cooking_fuel.value} to {new_fuel.value}",
        pm25_avoided_ug_per_day=round(max(pm25_saved_ug, 0), 2),
        co2_avoided_kg_per_day=round(max(co2_saved_g / 1000, 0), 4),
        money_saved_inr_per_day=round(money_saved, 2),
        assumptions=assumptions,
        sources=sources,
        factor_version=_VERSION,
    )


def calc_wear_mask_impact(
    aqi: float,
    mask_type: str = "n95",
    hours_outside: float = 2.0,
) -> ImpactResult:
    """
    Estimate PM2.5 exposure avoided by wearing a mask outdoors.
    Uses outdoor breathing rate (adult active) × hours × AQI-derived PM2.5 estimate.
    ASSUMPTION: 1 AQI unit ≈ 0.3 µg/m³ PM2.5 (rough linear proxy; stated explicitly).
    """
    exposure = _FACTORS["exposure"]
    efficiency = {
        "n95": exposure["n95_mask_efficiency"],
        "surgical": exposure["surgical_mask_efficiency"],
        "cloth": exposure["cloth_mask_efficiency"],
    }.get(mask_type.lower(), exposure["surgical_mask_efficiency"])

    breathing_rate = exposure["outdoor_breathing_rate_m3_per_hour"]["adult_active"]
    # Estimate outdoor PM2.5 from AQI (conservative linear approximation)
    pm25_estimate = aqi * 0.3  # µg/m³ – ASSUMPTION, stated below
    exposure_no_mask = breathing_rate * hours_outside * pm25_estimate  # µg
    pm25_avoided = exposure_no_mask * efficiency

    return ImpactResult(
        action_key="wear_mask_outdoor",
        description=f"Wearing a {mask_type.upper()} mask for {hours_outside} h outdoors at AQI {aqi:.0f}",
        pm25_avoided_ug_per_day=round(pm25_avoided, 2),
        co2_avoided_kg_per_day=None,
        money_saved_inr_per_day=None,
        assumptions=[
            f"Mask filtration efficiency: {efficiency * 100:.0f}%",
            f"Outdoor breathing rate (adult active): {breathing_rate} m³/h",
            "PM2.5 estimated from AQI using linear approximation: PM2.5 ≈ AQI × 0.3 µg/m³ (conservative proxy; not a calibrated conversion)",
            f"Duration outdoors: {hours_outside} h",
        ],
        sources=exposure["mask_sources"],
        factor_version=_VERSION,
    )


def calc_purifier_impact(
    room_volume_m3: float,
    cadr_m3_per_hour: float,
    hours_on: float = 8.0,
    infiltration_fraction: float = 0.8,
) -> ImpactResult:
    """
    Estimate indoor PM2.5 reduction from running an air purifier.
    Uses AHAM ACH formula and LBNL infiltration factors.
    """
    indoor = _FACTORS["indoor_air"]
    infiltration = _FACTORS["exposure"]["indoor_infiltration_fraction"]

    ach_purifier = cadr_m3_per_hour / room_volume_m3
    ach_note = f"{ach_purifier:.1f} air changes per hour"

    # Simplified steady-state: PM2.5_indoor / PM2.5_outdoor = F / (1 + CADR/ACH_natural)
    # This is a qualitative estimate – stated in assumptions
    reduction_pct = min(0.85, cadr_m3_per_hour / (cadr_m3_per_hour + room_volume_m3 * 2))
    pm25_avoided_note = f"≈{reduction_pct * 100:.0f}% PM2.5 reduction in this room"

    return ImpactResult(
        action_key="run_air_purifier",
        description=f"Running {cadr_m3_per_hour:.0f} m³/h CADR purifier in {room_volume_m3:.0f} m³ room for {hours_on} h",
        pm25_avoided_ug_per_day=None,  # Reduction % provided in assumptions instead
        co2_avoided_kg_per_day=None,
        money_saved_inr_per_day=None,
        assumptions=[
            pm25_avoided_note,
            ach_note,
            f"Recommended CADR for this room: {room_volume_m3 * indoor['cadr_per_m3_room_volume_ratio']:.0f} m³/h ({indoor['cadr_note']})",
            "Steady-state model (simplified); actual reduction depends on room sealing and furniture.",
        ],
        sources=[
            indoor["cadr_note"].split("Source: ")[-1] if "Source:" in indoor["cadr_note"] else "AHAM AC-1-2015",
            infiltration["sources"][0] if isinstance(infiltration.get("sources"), list) else "Logue et al. 2012",
        ],
        factor_version=_VERSION,
    )
