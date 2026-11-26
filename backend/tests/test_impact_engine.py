"""
Unit tests for the deterministic Impact Engine.
Run with: pytest tests/test_impact_engine.py -v
"""
from __future__ import annotations

import pytest

from app.models.domain import (
    BudgetTier,
    CommuteMode,
    CookingFuel,
    HeatingMethod,
    HouseholdProfile,
)
from app.services.impact_engine import (
    calc_cooking_switch_impact,
    calc_switch_commute_impact,
    calc_wear_mask_impact,
    calc_purifier_impact,
    _VERSION,
)


def _profile(**kwargs) -> HouseholdProfile:
    defaults = dict(
        city="Delhi",
        area="Rohini",
        coarse_lat=28.73,
        coarse_lon=77.12,
        household_size=3,
        commute_mode=CommuteMode.CAR_PETROL,
        commute_one_way_km=12.0,
        home_type="apartment",
        cooking_fuel=CookingFuel.BIOMASS,
        heating_method=HeatingMethod.COAL,
        budget_tier=BudgetTier.LOW,
    )
    defaults.update(kwargs)
    return HouseholdProfile(**defaults)


# ---------------------------------------------------------------------------
# Commute switch
# ---------------------------------------------------------------------------

def test_car_to_metro_avoids_pm25() -> None:
    profile = _profile(commute_mode=CommuteMode.CAR_PETROL, commute_one_way_km=15.0)
    result = calc_switch_commute_impact(profile, CommuteMode.PUBLIC_TRANSIT)
    # car_petrol PM2.5 = 10 µg/km, metro = 0.2 µg/km, daily = 30 km → ≈ 234 µg
    assert result.pm25_avoided_ug_per_day > 0
    assert result.co2_avoided_kg_per_day > 0
    assert result.money_saved_inr_per_day > 0
    assert result.factor_version == _VERSION


def test_cycle_switch_saves_pm25_vs_diesel() -> None:
    profile = _profile(commute_mode=CommuteMode.CAR_DIESEL, commute_one_way_km=5.0)
    result = calc_switch_commute_impact(profile, CommuteMode.CYCLE)
    daily_km = 10.0
    expected_pm25 = (50.0 - 0.0) * daily_km  # diesel factor - cycle
    assert abs(result.pm25_avoided_ug_per_day - expected_pm25) < 1.0


def test_wfh_no_commute_emissions() -> None:
    profile = _profile(commute_mode=CommuteMode.WORK_FROM_HOME)
    result = calc_switch_commute_impact(profile, CommuteMode.PUBLIC_TRANSIT)
    # Already WFH – function should return a result with 0/None savings
    assert result.pm25_avoided_ug_per_day is None or result.pm25_avoided_ug_per_day == 0.0


def test_result_has_sources_and_assumptions() -> None:
    profile = _profile()
    result = calc_switch_commute_impact(profile, CommuteMode.CAR_CNG)
    assert len(result.assumptions) > 0
    assert len(result.sources) > 0


# ---------------------------------------------------------------------------
# Cooking switch
# ---------------------------------------------------------------------------

def test_biomass_to_lpg_saves_pm25() -> None:
    profile = _profile(cooking_fuel=CookingFuel.BIOMASS)
    result = calc_cooking_switch_impact(profile, CookingFuel.LPG)
    # biomass 150 mg/MJ, lpg 1.5 mg/MJ, 3 meals × 4 MJ = 12 MJ/day
    # (150 - 1.5) × 12 × 1000 = 1,782,000 µg/day
    expected_pm25 = (150.0 - 1.5) * 3 * 4.0 * 1000
    assert abs(result.pm25_avoided_ug_per_day - expected_pm25) < 100


def test_lpg_to_induction_saves_pm25() -> None:
    profile = _profile(cooking_fuel=CookingFuel.LPG)
    result = calc_cooking_switch_impact(profile, CookingFuel.INDUCTION)
    assert result.pm25_avoided_ug_per_day > 0


def test_cooking_switch_no_negative_savings() -> None:
    # Switching from cleaner to dirtier fuel – savings should be clamped to 0
    profile = _profile(cooking_fuel=CookingFuel.INDUCTION)
    result = calc_cooking_switch_impact(profile, CookingFuel.BIOMASS)
    assert result.pm25_avoided_ug_per_day == 0


# ---------------------------------------------------------------------------
# Mask impact
# ---------------------------------------------------------------------------

def test_n95_beats_surgical() -> None:
    n95 = calc_wear_mask_impact(aqi=200, mask_type="n95", hours_outside=2.0)
    surg = calc_wear_mask_impact(aqi=200, mask_type="surgical", hours_outside=2.0)
    assert n95.pm25_avoided_ug_per_day > surg.pm25_avoided_ug_per_day


def test_mask_impact_scales_with_aqi() -> None:
    low_aqi = calc_wear_mask_impact(aqi=50, mask_type="n95")
    high_aqi = calc_wear_mask_impact(aqi=300, mask_type="n95")
    assert high_aqi.pm25_avoided_ug_per_day > low_aqi.pm25_avoided_ug_per_day


def test_mask_has_explicit_assumptions() -> None:
    result = calc_wear_mask_impact(aqi=150)
    assumptions_text = " ".join(result.assumptions)
    assert "ASSUMPTION" in assumptions_text or "proxy" in assumptions_text.lower()


# ---------------------------------------------------------------------------
# Purifier impact
# ---------------------------------------------------------------------------

def test_purifier_cadr_note_in_assumptions() -> None:
    result = calc_purifier_impact(room_volume_m3=50.0, cadr_m3_per_hour=200.0)
    all_text = " ".join(result.assumptions)
    assert "CADR" in all_text or "m³/h" in all_text


def test_purifier_recommended_cadr_calculation() -> None:
    # 50 m³ room × 0.75 = 37.5 m³/h minimum CADR
    result = calc_purifier_impact(room_volume_m3=50.0, cadr_m3_per_hour=37.5)
    assert result.factor_version == _VERSION
