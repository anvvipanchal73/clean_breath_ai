"""
CleanBreath AI – domain models (Pydantic v2).
Shared across routers, services, and tests.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Risk / AQI Enums
# ---------------------------------------------------------------------------


class RiskLevel(str, Enum):
    """
    Five-tier AQI risk classification used throughout CleanBreath AI.
    Sensitive-group thresholds are intentionally one tier stricter (see
    RiskClassifier).  Colour names match India's national AQI colour code
    and WHO 2021 breakpoints.
    """
    GREEN = "Green"       # AQI 0-50   – Good
    YELLOW = "Yellow"     # AQI 51-100 – Satisfactory
    ORANGE = "Orange"     # AQI 101-200 – Moderate / unhealthy for sensitive
    RED = "Red"           # AQI 201-300 – Poor
    MAROON = "Maroon"     # AQI 301+   – Very poor / severe


class SensitiveCondition(str, Enum):
    ASTHMA = "asthma"
    COPD = "copd"
    HEART_DISEASE = "heart_disease"
    PREGNANCY = "pregnancy"
    INFANT = "infant"            # < 2 years
    CHILD_UNDER_12 = "child_under_12"
    ELDERLY = "elderly"          # 65+


class CommuteMode(str, Enum):
    WALK = "walk"
    CYCLE = "cycle"
    PUBLIC_TRANSIT = "public_transit"
    MOTORCYCLE = "motorcycle"
    CAR_PETROL = "car_petrol"
    CAR_DIESEL = "car_diesel"
    CAR_CNG = "car_cng"
    CAR_ELECTRIC = "car_electric"
    AUTO_RICKSHAW = "auto_rickshaw"
    WORK_FROM_HOME = "work_from_home"


class CookingFuel(str, Enum):
    LPG = "lpg"
    PNG = "png"         # piped natural gas
    BIOMASS = "biomass"
    KEROSENE = "kerosene"
    ELECTRIC = "electric"
    INDUCTION = "induction"


class HeatingMethod(str, Enum):
    NONE = "none"
    CENTRAL_GAS = "central_gas"
    ROOM_HEATER_ELECTRIC = "room_heater_electric"
    ROOM_HEATER_OIL = "room_heater_oil"
    COAL = "coal"
    WOOD = "wood"
    BIOMASS = "biomass"


class BudgetTier(str, Enum):
    LOW = "low"           # < ₹20 k/month household
    MEDIUM = "medium"     # ₹20–70 k/month
    HIGH = "high"         # > ₹70 k/month


# ---------------------------------------------------------------------------
# Household Profile
# ---------------------------------------------------------------------------


class HouseholdProfile(BaseModel):
    id: str | None = None
    user_id: str | None = None
    city: str
    area: str = ""
    coarse_lat: float
    coarse_lon: float
    timezone: str = "Asia/Kolkata"
    household_size: int = Field(ge=1, le=20)
    age_groups: list[str] = Field(default_factory=list)
    sensitive_groups: list[SensitiveCondition] = Field(default_factory=list)
    health_data_consent: bool = False
    commute_mode: CommuteMode
    commute_one_way_km: float = Field(ge=0)
    home_type: str
    cooking_fuel: CookingFuel
    heating_method: HeatingMethod
    budget_tier: BudgetTier = BudgetTier.LOW
    preferred_language: str = "en"

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = {"en", "hi"}
        if v not in allowed:
            raise ValueError(f"preferred_language must be one of {allowed}")
        return v

    @property
    def has_sensitive_members(self) -> bool:
        return bool(self.sensitive_groups)


# ---------------------------------------------------------------------------
# Air Quality & Forecast
# ---------------------------------------------------------------------------


class AQISnapshot(BaseModel):
    """Current air quality reading at a coarse grid location."""
    lat: float
    lon: float
    aqi_us: float | None = None      # US EPA scale (what Open-Meteo returns)
    aqi_in: float | None = None      # India NAQI – set by classifier if available
    pm25: float | None = None        # µg/m³
    pm10: float | None = None        # µg/m³
    no2: float | None = None
    o3: float | None = None
    co: float | None = None
    so2: float | None = None
    temperature_c: float | None = None
    wind_speed_kmh: float | None = None
    wind_dir_deg: float | None = None
    humidity_pct: float | None = None
    boundary_layer_height_m: float | None = None
    stagnation_risk: bool = False
    source: str = "open-meteo"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    is_stale: bool = False


class ForecastPoint(BaseModel):
    time: datetime
    aqi_us: float | None = None
    pm25: float | None = None
    temperature_c: float | None = None


class AQIForecast(BaseModel):
    lat: float
    lon: float
    points: list[ForecastPoint] = Field(default_factory=list)
    source: str = "open-meteo"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Risk Classification
# ---------------------------------------------------------------------------


class RiskClassificationResult(BaseModel):
    aqi_value: float
    aqi_scale: str = "US-EPA"
    risk_level: RiskLevel
    # Adjusted level if profile has sensitive members (one tier stricter)
    effective_risk_level: RiskLevel
    is_adjusted_for_sensitive: bool
    health_message: str
    color_hex: str
    icon_emoji: str
    # Medical escalation flag: if True, include "see a doctor" prompt in UI
    suggest_medical_escalation: bool = False


# ---------------------------------------------------------------------------
# Daily Plan
# ---------------------------------------------------------------------------


class PlanAction(BaseModel):
    time_label: str                 # e.g. "06:00–07:00"
    block: str                      # wake_up | commute | school | exercise | cooking | evening | sleep
    icon: str                       # single emoji or Material icon key
    action: str                     # Short imperative
    detail: str                     # 1-2 sentence elaboration
    impact_note: str | None = None  # Optional short "this saves X" note (from Impact Engine)
    is_avoid: bool = False          # True = "avoid this", False = "do this"


class DailyPlan(BaseModel):
    profile_id: str | None = None
    risk_level: RiskLevel
    effective_risk_level: RiskLevel
    aqi_snapshot: AQISnapshot
    plan_date: str                  # ISO date string
    language: str = "en"
    actions: list[PlanAction] = Field(default_factory=list)
    summary_headline: str = ""
    medical_disclaimer: str = (
        "This is general guidance only. "
        "If you experience breathlessness, chest pain, or persistent cough, please see a doctor immediately."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Impact Engine
# ---------------------------------------------------------------------------


class ImpactResult(BaseModel):
    action_key: str
    description: str
    # Every numeric claim MUST come from the Impact Engine deterministic calc
    pm25_avoided_ug_per_day: float | None = None
    co2_avoided_kg_per_day: float | None = None
    money_saved_inr_per_day: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    factor_version: str = "v1"


# ---------------------------------------------------------------------------
# Knowledge / RAG
# ---------------------------------------------------------------------------


class KnowledgeChunk(BaseModel):
    id: str | None = None
    doc_id: str
    title: str
    source_org: str
    source_url: str | None = None
    published_year: int | None = None
    language: str = "en"
    chunk_index: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------


class PledgeType(str, Enum):
    CARPOOL_DAY = "carpool_day"
    NO_WASTE_BURNING = "no_waste_burning"
    PUBLIC_TRANSIT = "public_transit"
    CLEAN_COOKING = "clean_cooking"
    NO_IDLING = "no_idling"
    CYCLE_DAY = "cycle_day"


class CommunityPledge(BaseModel):
    group_id: str
    pledge_type: PledgeType
    estimated_pm25_g_avoided: float = 0.0
    estimated_co2_kg_avoided: float = 0.0
    estimated_money_saved_inr: float = 0.0
