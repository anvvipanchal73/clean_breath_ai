"""
Unit tests for the deterministic Risk Classifier.
Run with: pytest tests/test_risk_classifier.py -v
"""
from __future__ import annotations

import pytest

from app.models.domain import (
    AQISnapshot,
    HouseholdProfile,
    RiskLevel,
    SensitiveCondition,
    CommuteMode,
    CookingFuel,
    HeatingMethod,
    BudgetTier,
)
from app.services.risk_classifier import classify_risk, _pm25_to_aqi_approx


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _snapshot(aqi_us: float | None = None, pm25: float | None = None, is_stale: bool = False) -> AQISnapshot:
    return AQISnapshot(lat=28.61, lon=77.21, aqi_us=aqi_us, pm25=pm25, is_stale=is_stale, source="test")


def _profile(**kwargs) -> HouseholdProfile:
    defaults = dict(
        city="Delhi",
        area="Dwarka",
        coarse_lat=28.61,
        coarse_lon=77.21,
        household_size=4,
        commute_mode=CommuteMode.PUBLIC_TRANSIT,
        commute_one_way_km=15.0,
        home_type="apartment",
        cooking_fuel=CookingFuel.LPG,
        heating_method=HeatingMethod.ROOM_HEATER_ELECTRIC,
        budget_tier=BudgetTier.LOW,
    )
    defaults.update(kwargs)
    return HouseholdProfile(**defaults)


# ---------------------------------------------------------------------------
# Base AQI → risk tier mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("aqi, expected_level", [
    (0,   RiskLevel.GREEN),
    (25,  RiskLevel.GREEN),
    (50,  RiskLevel.GREEN),
    (51,  RiskLevel.YELLOW),
    (75,  RiskLevel.YELLOW),
    (100, RiskLevel.YELLOW),
    (101, RiskLevel.ORANGE),
    (150, RiskLevel.ORANGE),
    (151, RiskLevel.RED),
    (200, RiskLevel.RED),
    (201, RiskLevel.MAROON),
    (500, RiskLevel.MAROON),
])
def test_base_risk_levels(aqi: float, expected_level: RiskLevel) -> None:
    result = classify_risk(_snapshot(aqi_us=aqi))
    assert result.risk_level == expected_level


# ---------------------------------------------------------------------------
# Sensitive-group shift (one tier stricter)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("aqi, base_level, expected_effective", [
    (50,  RiskLevel.GREEN,  RiskLevel.YELLOW),   # Green → Yellow for sensitive
    (100, RiskLevel.YELLOW, RiskLevel.ORANGE),   # Yellow → Orange
    (150, RiskLevel.ORANGE, RiskLevel.RED),      # Orange → Red
    (200, RiskLevel.RED,    RiskLevel.MAROON),   # Red → Maroon
    (300, RiskLevel.MAROON, RiskLevel.MAROON),   # Maroon stays Maroon (capped)
])
def test_sensitive_group_shift(aqi: float, base_level: RiskLevel, expected_effective: RiskLevel) -> None:
    profile = _profile(sensitive_groups=[SensitiveCondition.ASTHMA])
    result = classify_risk(_snapshot(aqi_us=aqi), profile=profile)
    assert result.risk_level == base_level
    assert result.effective_risk_level == expected_effective
    assert result.is_adjusted_for_sensitive is True


def test_no_shift_without_sensitive_members() -> None:
    profile = _profile(sensitive_groups=[])
    result = classify_risk(_snapshot(aqi_us=100), profile=profile)
    assert result.effective_risk_level == result.risk_level
    assert result.is_adjusted_for_sensitive is False


def test_infant_triggers_sensitive_shift() -> None:
    profile = _profile(sensitive_groups=[SensitiveCondition.INFANT])
    result = classify_risk(_snapshot(aqi_us=100), profile=profile)
    assert result.effective_risk_level == RiskLevel.ORANGE  # Yellow → Orange


# ---------------------------------------------------------------------------
# Medical escalation
# ---------------------------------------------------------------------------

def test_medical_escalation_at_red() -> None:
    result = classify_risk(_snapshot(aqi_us=201))
    assert result.suggest_medical_escalation is True


def test_no_escalation_at_yellow() -> None:
    result = classify_risk(_snapshot(aqi_us=75))
    assert result.suggest_medical_escalation is False


def test_sensitive_escalates_at_orange() -> None:
    profile = _profile(sensitive_groups=[SensitiveCondition.COPD])
    # AQI 150 → base Orange; with shift → Red; Red >= ORANGE threshold for sensitive
    result = classify_risk(_snapshot(aqi_us=150), profile=profile)
    assert result.suggest_medical_escalation is True


# ---------------------------------------------------------------------------
# PM2.5 fallback derivation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pm25, expected_min_aqi, expected_max_aqi", [
    (5.0,   0,   50),     # Good
    (20.0,  51,  100),    # Moderate
    (45.0, 101,  150),    # Unhealthy for sensitive
    (90.0, 151,  200),    # Unhealthy
    (160.0, 201, 300),    # Very unhealthy
    (300.0, 301, 500),    # Hazardous
])
def test_pm25_to_aqi_approximate_ranges(pm25: float, expected_min_aqi: float, expected_max_aqi: float) -> None:
    aqi = _pm25_to_aqi_approx(pm25)
    assert expected_min_aqi <= aqi <= expected_max_aqi, f"PM2.5={pm25} gave AQI={aqi}, expected {expected_min_aqi}–{expected_max_aqi}"


def test_classify_uses_pm25_when_no_aqi_us() -> None:
    # PM2.5 = 20 → AQI ~70 → Yellow
    result = classify_risk(_snapshot(pm25=20.0))
    assert result.risk_level == RiskLevel.YELLOW
    assert "PM2.5" in result.aqi_scale


# ---------------------------------------------------------------------------
# Language / output fields
# ---------------------------------------------------------------------------

def test_hindi_health_message() -> None:
    result = classify_risk(_snapshot(aqi_us=50), language="hi")
    assert "hi" in result.health_message or any(c > "\u0900" for c in result.health_message)


def test_color_hex_format() -> None:
    for aqi in [25, 75, 125, 175, 250]:
        result = classify_risk(_snapshot(aqi_us=aqi))
        assert result.color_hex.startswith("#")
        assert len(result.color_hex) == 7


def test_icon_emoji_present() -> None:
    result = classify_risk(_snapshot(aqi_us=100))
    assert len(result.icon_emoji) >= 1
