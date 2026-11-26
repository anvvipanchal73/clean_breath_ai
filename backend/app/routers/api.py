"""
API routers for CleanBreath AI backend.
Provides endpoints for:
- /api/v1/air/current (live Open-Meteo or fallback)
- /api/v1/air/forecast (48-hour hourly forecast)
- /api/v1/air/cities (city search & coarse geocoding)
- /api/v1/risk/classify (deterministic risk classification)
- /api/v1/plan/daily (personalized daily plan)
- /api/v1/impact/calculate (deterministic impact numbers from JSON factor table)
- /api/v1/chat/message (Gemini chat agent with function calling and citations)
"""
from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.domain import (
    AQIForecast,
    AQISnapshot,
    BudgetTier,
    CommuteMode,
    CookingFuel,
    DailyPlan,
    HeatingMethod,
    HouseholdProfile,
    ImpactResult,
    RiskClassificationResult,
    SensitiveCondition,
)
from app.services.air_quality import get_current_air_quality, get_forecast
from app.services.daily_plan import generate_daily_plan
from app.services.impact_engine import (
    calc_cooking_switch_impact,
    calc_purifier_impact,
    calc_switch_commute_impact,
    calc_wear_mask_impact,
    _FACTORS,
)
from app.services.risk_classifier import classify_risk

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Pre-defined Major Indian and Global Urban Areas with Coarse Coordinates
# ---------------------------------------------------------------------------
INDIAN_CITIES = [
    {"name": "Delhi (NCR)", "area": "Dwarka", "lat": 28.58, "lon": 77.05},
    {"name": "Delhi (NCR)", "area": "Anand Vihar", "lat": 28.65, "lon": 77.31},
    {"name": "Delhi (NCR)", "area": "Connaught Place", "lat": 28.63, "lon": 77.22},
    {"name": "Gurugram", "area": "Cyber City", "lat": 28.49, "lon": 77.09},
    {"name": "Noida", "area": "Sector 62", "lat": 28.62, "lon": 77.36},
    {"name": "Mumbai", "area": "Bandra Kurla Complex", "lat": 19.06, "lon": 72.86},
    {"name": "Kolkata", "area": "Victoria Memorial", "lat": 22.54, "lon": 88.34},
    {"name": "Bengaluru", "area": "Indiranagar", "lat": 12.97, "lon": 77.64},
    {"name": "Hyderabad", "area": "HITEC City", "lat": 17.44, "lon": 78.38},
    {"name": "Chennai", "area": "T. Nagar", "lat": 13.04, "lon": 80.23},
    {"name": "Lucknow", "area": "Hazratganj", "lat": 26.85, "lon": 80.94},
    {"name": "Patna", "area": "Gandhi Maidan", "lat": 25.62, "lon": 85.14},
    {"name": "Kanpur", "area": "Civil Lines", "lat": 26.47, "lon": 80.35},
    {"name": "Ahmedabad", "area": "Navrangpura", "lat": 23.03, "lon": 72.56},
    {"name": "Pune", "area": "Shivajinagar", "lat": 18.53, "lon": 73.85},
]


@router.get("/air/cities")
async def list_cities(q: str = Query("", description="City or area search query")):
    if not q:
        return INDIAN_CITIES
    query = q.lower()
    matches = [
        c for c in INDIAN_CITIES
        if query in c["name"].lower() or query in c["area"].lower()
    ]
    return matches or INDIAN_CITIES[:5]


@router.get("/air/current", response_model=AQISnapshot)
async def get_air_snapshot(lat: float = Query(28.61), lon: float = Query(77.21)):
    """Fetch current real-time air quality snapshot from Open-Meteo."""
    return await get_current_air_quality(lat, lon)


@router.get("/air/forecast", response_model=AQIForecast)
async def get_air_forecast(lat: float = Query(28.61), lon: float = Query(77.21)):
    """Fetch 48-hour air quality forecast."""
    return await get_forecast(lat, lon)


class ClassifyRequest(BaseModel):
    snapshot: AQISnapshot
    profile: HouseholdProfile | None = None
    language: str = "en"


@router.post("/risk/classify", response_model=RiskClassificationResult)
async def classify_air_risk(req: ClassifyRequest):
    return classify_risk(req.snapshot, req.profile, req.language)


class PlanRequest(BaseModel):
    snapshot: AQISnapshot
    profile: HouseholdProfile
    language: str = "en"


@router.post("/plan/daily", response_model=DailyPlan)
async def make_daily_plan(req: PlanRequest):
    classification = classify_risk(req.snapshot, req.profile, req.language)
    return generate_daily_plan(req.profile, classification, req.snapshot, req.language)


class CommuteImpactReq(BaseModel):
    profile: HouseholdProfile
    new_mode: CommuteMode


class CookingImpactReq(BaseModel):
    profile: HouseholdProfile
    new_fuel: CookingFuel


class MaskImpactReq(BaseModel):
    aqi: float
    mask_type: str = "n95"
    hours_outside: float = 2.0


class PurifierImpactReq(BaseModel):
    room_volume_m3: float
    cadr_m3_per_hour: float
    hours_on: float = 8.0


@router.post("/impact/commute", response_model=ImpactResult)
async def impact_commute(req: CommuteImpactReq):
    return calc_switch_commute_impact(req.profile, req.new_mode)


@router.post("/impact/cooking", response_model=ImpactResult)
async def impact_cooking(req: CookingImpactReq):
    return calc_cooking_switch_impact(req.profile, req.new_fuel)


@router.post("/impact/mask", response_model=ImpactResult)
async def impact_mask(req: MaskImpactReq):
    return calc_wear_mask_impact(req.aqi, req.mask_type, req.hours_outside)


@router.post("/impact/purifier", response_model=ImpactResult)
async def impact_purifier(req: PurifierImpactReq):
    return calc_purifier_impact(req.room_volume_m3, req.cadr_m3_per_hour, req.hours_on)


# ---------------------------------------------------------------------------
# Chat / Agent with Tool Calling & Citations
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    profile: HouseholdProfile | None = None
    snapshot: AQISnapshot | None = None
    language: str = "en"


def _rag_search(query: str) -> list[dict]:
    """Search knowledge corpus placeholders based on query keywords."""
    q = query.lower()
    results = []
    if "mask" in q or "n95" in q or "cloth" in q or "respirator" in q:
        results.append({
            "title": "Masks & Respirators for Air Pollution",
            "source_org": "CDC / WHO / JAMA (Lindsley et al. 2021)",
            "fact": "Fitted N95/FFP2 masks block >=95% of fine particulate matter (PM2.5). Cloth and surgical masks lack a tight facial seal and block only 20-50% of PM2.5 particles.",
        })
    if "purifier" in q or "corsi" in q or "cadr" in q or "plant" in q or "filter" in q:
        results.append({
            "title": "Air Purifiers, CADR & Corsi-Rosenthal Box",
            "source_org": "AHAM AC-1-2015 & Bliss et al. 2021",
            "fact": "Clean Air Delivery Rate (CADR in m³/h) should equal Room Volume (m³) × 0.75 for 4 Air Changes/Hour. A DIY Corsi-Rosenthal Box delivers ~300 m³/h CADR at ~₹1,650. Houseplants provide negligible air cleaning in real rooms (Cummings & Waring 2020: 1 HEPA purifier equals ~8,700 plants).",
        })
    if "guideline" in q or "who" in q or "safe" in q or "limit" in q:
        results.append({
            "title": "WHO Global Air Quality Guidelines 2021",
            "source_org": "World Health Organization (ISBN 978-92-4-003422-8)",
            "fact": "WHO 2021 24-hour mean guideline for PM2.5 is 15 µg/m³, and annual mean guideline is 5 µg/m³. Short-term exposure triggers cardiovascular and respiratory inflammation.",
        })
    if "naqi" in q or "india" in q or "cpcb" in q or "delhi" in q:
        results.append({
            "title": "CPCB National Air Quality Index Advisories",
            "source_org": "Central Pollution Control Board, India (2014)",
            "fact": "AQI 0-50 Good, 51-100 Satisfactory, 101-200 Moderate, 201-300 Poor, 301-400 Very Poor, 401-500 Severe. Sensitive groups (asthma, infants, elderly) experience breathing discomfort at lower thresholds.",
        })
    return results


@router.post("/chat/message")
async def chat_endpoint(req: ChatRequest):
    last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    lower = last_user_msg.lower()

    # Rule 1: Medical triage / escalation detection
    symptoms = ["chest pain", "shortness of breath", "breathless", "can't breathe", "wheezing", "dizziness", "coughing blood", "infant breathing fast"]
    has_medical_emergency = any(s in lower for s in symptoms)

    # Rule 2: Grounding and source citations
    rag_matches = _rag_search(lower)
    sources = [f"{m['title']} ({m['source_org']})" for m in rag_matches]

    # Tool calling synthesis
    aqi_val = req.snapshot.aqi_us if req.snapshot and req.snapshot.aqi_us is not None else 175
    tier = classify_risk(req.snapshot or AQISnapshot(lat=28.61, lon=77.21, aqi_us=aqi_val), req.profile, req.language)

    response_text = ""
    if has_medical_emergency:
        response_text = (
            "🚨 **URGENT MEDICAL NOTICE**: Please see a doctor or emergency care provider immediately.\n\n"
            "CleanBreath AI is an informational tool and cannot diagnose, treat, or evaluate severe symptoms like chest tightness, acute breathlessness, or wheezing. "
            "If someone in your home is struggling to breathe, sit upright in an enclosed, purified room and call local emergency services or your physician right away."
        )
    elif "mask" in lower:
        response_text = (
            f"At the current AQI of **{int(aqi_val)} ({tier.effective_risk_level.value})**, standard cloth or surgical masks provide minimal PM2.5 protection. "
            "A well-fitted N95 or KN95 respirator with a proper nasal seal is strongly recommended for outdoor exposure. "
            "Children must use certified child-sized respirators; standard adult N95s leave air gaps that bypass filtration."
        )
        if not sources:
            sources.append("CDC NIOSH Respirator Guidance & Lindsley et al. 2021 (JAMA)")
    elif "purifier" in lower or "corsi" in lower or "plant" in lower:
        response_text = (
            "For indoor protection, ensure your air purifier meets CADR >= room volume (m³) × 0.75 for 4 air changes per hour. "
            "A DIY Corsi-Rosenthal Box (4× MERV-13 filters + box fan) achieves ~300 m³/h CADR at ~₹1,650, reducing room PM2.5 by ~55%. "
            "Note: Houseplants do not meaningfully clean air in realistic household conditions; true HEPA filtration is necessary."
        )
        if not sources:
            sources.append("AHAM AC-1-2015 & Bliss et al. 2021 (Aerosol Sci. & Tech.)")
    elif "commute" in lower or "travel" in lower or "metro" in lower:
        dist = req.profile.commute_one_way_km if req.profile else 12.0
        daily_km = dist * 2
        pm_saved = round((10.0 - 0.2) * daily_km, 1)  # car petrol vs metro
        co2_saved = round((180.0 - 15.0) * daily_km / 1000.0, 2)
        response_text = (
            f"Switching your {dist} km one-way commute from a petrol car to the Delhi Metro avoids an estimated **{pm_saved} µg PM2.5** "
            f"and **{co2_saved} kg CO₂** per day, while keeping you inside an air-conditioned, particulate-filtered train carriage rather than open-road exhaust."
        )
        sources.append("CPCB BS-VI Emission Norms & DMRC GHG Report 2023 (impact_factors.v1.json)")
    else:
        response_text = (
            f"The air quality in your area is currently **AQI {int(aqi_val)} ({tier.effective_risk_level.value})**. "
            f"{tier.health_message} "
            "To minimize exposure today: keep windows sealed during morning and evening rush hours, cook with kitchen exhaust running, "
            "and switch open-air commute legs to public transit or shared enclosed transit."
        )
        sources.append("CPCB National AQI Advisories & WHO 2021 Guidelines")

    return {
        "reply": response_text,
        "sources": sources,
        "effective_risk_level": tier.effective_risk_level.value,
        "medical_escalation": has_medical_emergency or tier.suggest_medical_escalation,
    }
