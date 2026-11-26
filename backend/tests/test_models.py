"""
Smoke test for domain models – ensures Pydantic v2 schemas parse correctly
and validators work as expected.
"""
from __future__ import annotations

import pytest

from app.models.domain import (
    AQISnapshot,
    BudgetTier,
    CommuteMode,
    CookingFuel,
    HeatingMethod,
    HouseholdProfile,
    RiskLevel,
    SensitiveCondition,
)


def test_household_profile_validates_language() -> None:
    with pytest.raises(ValueError):
        HouseholdProfile(
            city="Delhi",
            coarse_lat=28.6,
            coarse_lon=77.2,
            household_size=4,
            commute_mode=CommuteMode.PUBLIC_TRANSIT,
            commute_one_way_km=10,
            home_type="apartment",
            cooking_fuel=CookingFuel.LPG,
            heating_method=HeatingMethod.NONE,
            preferred_language="fr",  # unsupported → should raise
        )


def test_household_profile_has_sensitive_members() -> None:
    p = HouseholdProfile(
        city="Mumbai",
        coarse_lat=19.08,
        coarse_lon=72.88,
        household_size=3,
        commute_mode=CommuteMode.CAR_PETROL,
        commute_one_way_km=8,
        home_type="apartment",
        cooking_fuel=CookingFuel.PNG,
        heating_method=HeatingMethod.NONE,
        sensitive_groups=[SensitiveCondition.INFANT],
    )
    assert p.has_sensitive_members is True


def test_aqi_snapshot_defaults_not_stale() -> None:
    s = AQISnapshot(lat=28.6, lon=77.2)
    assert s.is_stale is False
    assert s.stagnation_risk is False


def test_risk_level_enum_values() -> None:
    assert RiskLevel.GREEN.value == "Green"
    assert RiskLevel.MAROON.value == "Maroon"
    levels = [RiskLevel.GREEN, RiskLevel.YELLOW, RiskLevel.ORANGE, RiskLevel.RED, RiskLevel.MAROON]
    assert len(levels) == 5
