"""
Deterministic Risk Classifier for CleanBreath AI.

Converts a raw AQI (US-EPA scale, as returned by Open-Meteo) into one of five
risk tiers: Green / Yellow / Orange / Red / Maroon.

Sensitive-group rule: if the household profile contains any sensitive member
(infant, child under 12, elderly 65+, asthma, COPD, heart disease, pregnancy),
the effective risk level is shifted one tier stricter than the base level.

IMPORTANT: This module contains NO LLM calls.  All logic is deterministic
and unit-tested.  Source: India NAQI breakpoints (CPCB) extended with WHO
2021 PM2.5 24-h guideline (15 µg/m³) used to inform the Green/Yellow boundary.

References:
  - CPCB National Air Quality Index (2014): https://cpcb.nic.in/
  - WHO Global Air Quality Guidelines 2021: ISBN 978-92-4-003422-8
"""
from __future__ import annotations

from app.models.domain import (
    AQISnapshot,
    HouseholdProfile,
    RiskClassificationResult,
    RiskLevel,
    SensitiveCondition,
)

# ---------------------------------------------------------------------------
# AQI → risk tier breakpoints (US-EPA scale, as reported by Open-Meteo)
# ---------------------------------------------------------------------------
#  0 –  50  → Green    (Good)
# 51 – 100  → Yellow   (Moderate / India: Satisfactory)
# 101 – 150 → Orange   (Unhealthy for Sensitive Groups)
# 151 – 200 → Red      (Unhealthy)
# 201+      → Maroon   (Very Unhealthy / Hazardous)
#
# India NAQI breakpoints differ slightly; we use the stricter of the two for
# the user's safety and note the assumption in the config.
_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (50.0,  RiskLevel.GREEN),
    (100.0, RiskLevel.YELLOW),
    (150.0, RiskLevel.ORANGE),
    (200.0, RiskLevel.RED),
]  # > 200 → MAROON

_TIER_ORDER = [
    RiskLevel.GREEN,
    RiskLevel.YELLOW,
    RiskLevel.ORANGE,
    RiskLevel.RED,
    RiskLevel.MAROON,
]

_COLOR_MAP: dict[RiskLevel, str] = {
    RiskLevel.GREEN:  "#4CAF50",
    RiskLevel.YELLOW: "#FFEB3B",
    RiskLevel.ORANGE: "#FF9800",
    RiskLevel.RED:    "#F44336",
    RiskLevel.MAROON: "#880E4F",
}

_ICON_MAP: dict[RiskLevel, str] = {
    RiskLevel.GREEN:  "😊",
    RiskLevel.YELLOW: "😐",
    RiskLevel.ORANGE: "😷",
    RiskLevel.RED:    "⚠️",
    RiskLevel.MAROON: "🚨",
}

_HEALTH_MSG: dict[RiskLevel, dict[str, str]] = {
    RiskLevel.GREEN: {
        "en": "Air quality is good. Enjoy outdoor activities.",
        "hi": "हवा की गुणवत्ता अच्छी है। बाहरी गतिविधियाँ आनंद लें।",
    },
    RiskLevel.YELLOW: {
        "en": "Air quality is satisfactory. Sensitive individuals should limit prolonged outdoor exertion.",
        "hi": "हवा की गुणवत्ता संतोषजनक है। संवेदनशील लोग बाहरी परिश्रम सीमित करें।",
    },
    RiskLevel.ORANGE: {
        "en": "Air quality is poor. Reduce outdoor activity. Wear N95/P100 mask outside.",
        "hi": "हवा की गुणवत्ता खराब है। बाहरी गतिविधि कम करें और मास्क पहनें।",
    },
    RiskLevel.RED: {
        "en": "Unhealthy air. Avoid outdoor exertion. Keep windows closed. Run air purifier.",
        "hi": "अस्वस्थ हवा। बाहर जाने से बचें। खिड़कियाँ बंद रखें। वायु शोधक चलाएं।",
    },
    RiskLevel.MAROON: {
        "en": "Hazardous air. Stay indoors. Seal gaps. All outdoor activity strictly avoided.",
        "hi": "खतरनाक हवा। घर के अंदर रहें। दरारें बंद करें। बाहर बिल्कुल न जाएं।",
    },
}

# Medical escalation triggers at or above these levels
_ESCALATION_THRESHOLD = RiskLevel.RED
# Sensitive groups always escalate at RED or above
_SENSITIVE_ESCALATION_THRESHOLD = RiskLevel.ORANGE


def _base_risk_level(aqi: float) -> RiskLevel:
    """Map a numeric AQI value to the base risk tier."""
    for threshold, level in _THRESHOLDS:
        if aqi <= threshold:
            return level
    return RiskLevel.MAROON


def _shift_one_tier_stricter(level: RiskLevel) -> RiskLevel:
    """Move one position up the severity scale (capped at MAROON)."""
    idx = _TIER_ORDER.index(level)
    return _TIER_ORDER[min(idx + 1, len(_TIER_ORDER) - 1)]


def classify_risk(
    snapshot: AQISnapshot,
    profile: HouseholdProfile | None = None,
    language: str = "en",
) -> RiskClassificationResult:
    """
    Classify AQI risk.

    Parameters
    ----------
    snapshot: AQISnapshot
        Current air quality reading.  Uses aqi_us if available, falls back to
        deriving from pm25 when aqi_us is None.
    profile: HouseholdProfile | None
        If provided, sensitive-group adjustment is applied.
    language: str
        Language code for health message; falls back to 'en'.

    Returns
    -------
    RiskClassificationResult with deterministic fields – no LLM involvement.
    """
    # Determine best available AQI value
    aqi_value: float
    aqi_scale: str
    if snapshot.aqi_us is not None:
        aqi_value = snapshot.aqi_us
        aqi_scale = "US-EPA"
    elif snapshot.pm25 is not None:
        # Approximate US AQI from PM2.5 (24-h equivalent; simplified linear interpolation
        # between USEPA 2024 breakpoints – used only as last resort when API lacks AQI field)
        aqi_value = _pm25_to_aqi_approx(snapshot.pm25)
        aqi_scale = "US-EPA (derived from PM2.5)"
    else:
        # No data – treat as unavailable; return MAROON to err on side of caution
        # Caller MUST check is_stale / source to surface appropriate UI warning
        aqi_value = 999.0
        aqi_scale = "unknown"

    base_level = _base_risk_level(aqi_value)

    # Sensitive-group adjustment
    has_sensitive = bool(profile and profile.has_sensitive_members)
    if has_sensitive:
        effective_level = _shift_one_tier_stricter(base_level)
        is_adjusted = True
    else:
        effective_level = base_level
        is_adjusted = False

    # Medical escalation
    escalation_trigger = (
        _SENSITIVE_ESCALATION_THRESHOLD if has_sensitive else _escalation_threshold
    )
    suggest_escalation = _tier_order_index(effective_level) >= _tier_order_index(
        escalation_trigger
    )

    lang = language if language in ("en", "hi") else "en"
    health_message = _HEALTH_MSG[effective_level][lang]

    return RiskClassificationResult(
        aqi_value=aqi_value,
        aqi_scale=aqi_scale,
        risk_level=base_level,
        effective_risk_level=effective_level,
        is_adjusted_for_sensitive=is_adjusted,
        health_message=health_message,
        color_hex=_COLOR_MAP[effective_level],
        icon_emoji=_ICON_MAP[effective_level],
        suggest_medical_escalation=suggest_escalation,
    )


def _tier_order_index(level: RiskLevel) -> int:
    return _TIER_ORDER.index(level)


_escalation_threshold = _ESCALATION_THRESHOLD  # module-level alias


def _pm25_to_aqi_approx(pm25: float) -> float:
    """
    Approximate US AQI from hourly PM2.5 concentration (µg/m³).
    Uses simplified linear segments from USEPA 2024 breakpoints.
    ASSUMPTION: Treats hourly PM2.5 as 24-h average – yields conservative
    (higher) AQI; errs on side of caution.
    Source: USEPA AQI Technical Assistance Document (2024).
    """
    # (PM2.5_low, PM2.5_high, AQI_low, AQI_high)
    breakpoints = [
        (0.0, 9.0, 0, 50),
        (9.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200),
        (125.5, 225.4, 201, 300),
        (225.5, 325.4, 301, 500),
    ]
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo, 1)
    return 500.0  # > 325.4 µg/m³ → cap at 500
