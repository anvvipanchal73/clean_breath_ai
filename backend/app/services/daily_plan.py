"""
Deterministic Daily Plan generator for CleanBreath AI.

Produces a 7-block time-based routine tailored to the household's risk level,
sensitive members, commute mode, cooking fuel, and language preference.

This module contains NO LLM calls; all logic is deterministic rule-based code.
The LLM Explainer (Phase 2+) may add conversational text on top, but the
structured plan is always generated first from these rules.
"""
from __future__ import annotations

from datetime import date

from app.models.domain import (
    AQISnapshot,
    CookingFuel,
    CommuteMode,
    DailyPlan,
    HouseholdProfile,
    PlanAction,
    RiskClassificationResult,
    RiskLevel,
)

# ---------------------------------------------------------------------------
# Translation stubs – will be expanded in Phase 1
# ---------------------------------------------------------------------------

_I18N: dict[str, dict] = {
    "en": {
        "wake_up": "Wake Up",
        "commute": "Commute",
        "school": "School / Work",
        "exercise": "Exercise",
        "cooking": "Cooking",
        "evening": "Evening",
        "sleep": "Sleep Prep",
    },
    "hi": {
        "wake_up": "उठना",
        "commute": "आवागमन",
        "school": "स्कूल / काम",
        "exercise": "व्यायाम",
        "cooking": "खाना पकाना",
        "evening": "शाम",
        "sleep": "सोने की तैयारी",
    },
}


def _t(key: str, lang: str) -> str:
    return _I18N.get(lang, _I18N["en"]).get(key, key)


# ---------------------------------------------------------------------------
# Plan action builders (rule-based, one per time block)
# ---------------------------------------------------------------------------

def _wake_up_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    actions: list[PlanAction] = []

    if risk in (RiskLevel.GREEN, RiskLevel.YELLOW):
        actions.append(PlanAction(
            time_label="06:00–07:00",
            block="wake_up",
            icon="🌅",
            action="Open windows briefly" if lang == "en" else "खिड़कियाँ थोड़ी देर खोलें",
            detail=(
                "Air is relatively clean in early morning. Open windows for 10–15 min "
                "to flush stale indoor air before commute."
                if lang == "en" else
                "सुबह हवा अपेक्षाकृत साफ होती है। आवागमन से पहले 10–15 मिनट के लिए खिड़कियाँ खोलें।"
            ),
        ))
    else:
        actions.append(PlanAction(
            time_label="06:00–07:00",
            block="wake_up",
            icon="🚫",
            action="Keep windows closed" if lang == "en" else "खिड़कियाँ बंद रखें",
            detail=(
                "Outdoor air quality is poor. Keep windows shut. If you have an air "
                "purifier, turn it on now."
                if lang == "en" else
                "बाहरी हवा की गुणवत्ता खराब है। खिड़कियाँ बंद रखें। वायु शोधक चालू करें।"
            ),
            is_avoid=True,
        ))

    if risk in (RiskLevel.RED, RiskLevel.MAROON):
        actions.append(PlanAction(
            time_label="06:00–07:00",
            block="wake_up",
            icon="😷",
            action="Wear N95 if leaving home" if lang == "en" else "बाहर जाएं तो N95 पहनें",
            detail=(
                "If you must go out, wear a well-fitted N95 or P100 respirator, not a cloth mask."
                if lang == "en" else
                "यदि बाहर जाना हो तो अच्छी तरह से फिट N95 या P100 श्वासयंत्र पहनें।"
            ),
        ))
    return actions


def _commute_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    actions: list[PlanAction] = []
    is_en = lang == "en"

    if profile.commute_mode == CommuteMode.WORK_FROM_HOME:
        actions.append(PlanAction(
            time_label="08:00–09:00",
            block="commute",
            icon="🏠",
            action="Work from home today" if is_en else "आज घर से काम करें",
            detail=(
                "No commute – great for air quality. Keep indoor air clean with purifier "
                "or sealed windows."
                if is_en else
                "कोई आवागमन नहीं। वायु शोधक से घर की हवा साफ रखें।"
            ),
        ))
        return actions

    if risk in (RiskLevel.RED, RiskLevel.MAROON):
        actions.append(PlanAction(
            time_label="08:00–09:00",
            block="commute",
            icon="⚠️",
            action="Wear N95 for the entire commute" if is_en else "पूरे आवागमन में N95 पहनें",
            detail=(
                "Air is hazardous. Wear N95/P100 for the whole journey. Avoid rushing "
                "– faster breathing increases exposure."
                if is_en else
                "हवा खतरनाक है। पूरे सफर में N95/P100 पहनें। तेज चलने से बचें।"
            ),
        ))

    if profile.commute_mode in (CommuteMode.CAR_PETROL, CommuteMode.CAR_DIESEL):
        actions.append(PlanAction(
            time_label="08:00–09:00",
            block="commute",
            icon="🚗",
            action="Recirculate car air" if is_en else "कार में हवा रीसर्कुलेट करें",
            detail=(
                "Set car ventilation to 'recirculate' (not fresh air) to reduce "
                "outdoor PM2.5 entering the cabin."
                if is_en else
                "कार का वेंटिलेशन 'रीसर्कुलेट' पर सेट करें – बाहरी PM2.5 कम होगा।"
            ),
        ))
    elif profile.commute_mode in (CommuteMode.MOTORCYCLE, CommuteMode.CYCLE, CommuteMode.WALK):
        if risk >= RiskLevel.ORANGE:
            actions.append(PlanAction(
                time_label="08:00–09:00",
                block="commute",
                icon="🚌",
                action="Consider public transit today" if is_en else "आज सार्वजनिक परिवहन उपयोग करें",
                detail=(
                    "Air quality is poor for open-air commuting. Metro or bus reduces "
                    "your PM2.5 inhalation significantly."
                    if is_en else
                    "खुली सवारी से आवागमन के लिए हवा खराब है। मेट्रो या बस लें।"
                ),
            ))

    return actions


def _exercise_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    is_en = lang == "en"
    if risk in (RiskLevel.GREEN, RiskLevel.YELLOW):
        return [PlanAction(
            time_label="17:00–18:00",
            block="exercise",
            icon="🏃",
            action="Outdoor exercise is fine" if is_en else "बाहरी व्यायाम ठीक है",
            detail=(
                "Air quality allows outdoor activity. Avoid exercising near roads or "
                "construction sites."
                if is_en else
                "हवा की गुणवत्ता ठीक है। सड़क या निर्माण स्थल से दूर रहें।"
            ),
        )]
    elif risk == RiskLevel.ORANGE:
        return [PlanAction(
            time_label="17:00–18:00",
            block="exercise",
            icon="🏠",
            action="Exercise indoors today" if is_en else "आज अंदर व्यायाम करें",
            detail=(
                "Air quality is moderate. Prefer indoor workouts – yoga, stretching, "
                "or home cardio."
                if is_en else
                "हवा मध्यम है। योग, स्ट्रेचिंग या होम कार्डियो करें।"
            ),
        )]
    else:
        return [PlanAction(
            time_label="17:00–18:00",
            block="exercise",
            icon="🚫",
            action="Skip outdoor exercise" if is_en else "बाहरी व्यायाम न करें",
            detail=(
                "Air is too polluted for any outdoor physical exertion. Even gentle "
                "outdoor activity raises PM2.5 intake significantly. Stick indoors."
                if is_en else
                "बाहरी व्यायाम के लिए हवा बहुत प्रदूषित है। घर के अंदर रहें।"
            ),
            is_avoid=True,
        )]


def _cooking_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    is_en = lang == "en"
    actions: list[PlanAction] = []

    if profile.cooking_fuel == CookingFuel.BIOMASS:
        actions.append(PlanAction(
            time_label="12:00–13:00",
            block="cooking",
            icon="🔥",
            action="Cook outdoors or in well-ventilated area" if is_en else "बाहर या हवादार जगह पकाएं",
            detail=(
                "Biomass burning releases high PM2.5. If possible, cook outside or use "
                "a pressure cooker to reduce cook time by 70%."
                if is_en else
                "बायोमास से PM2.5 अधिक निकलता है। बाहर या प्रेशर कुकर में पकाएं।"
            ),
        ))
    else:
        actions.append(PlanAction(
            time_label="12:00–13:00",
            block="cooking",
            icon="🍲",
            action="Use exhaust fan while cooking" if is_en else "खाना पकाते समय एग्जॉस्ट फैन चलाएं",
            detail=(
                "Even LPG/PNG cooking raises indoor PM2.5 by 2–5×. Run exhaust or "
                "open the kitchen window slightly while cooking."
                if is_en else
                "LPG/PNG पकाने से भी PM2.5 बढ़ता है। एग्जॉस्ट फैन चलाएं या किचन खिड़की खोलें।"
            ),
        ))

    if risk in (RiskLevel.RED, RiskLevel.MAROON):
        actions.append(PlanAction(
            time_label="12:00–13:00",
            block="cooking",
            icon="🚫",
            action="Avoid frying and high-heat cooking" if is_en else "तलने से बचें",
            detail=(
                "High-heat cooking significantly worsens indoor PM2.5 on bad air days. "
                "Prefer steaming, boiling, or pressure cooking."
                if is_en else
                "खराब हवा में तलने से घर के अंदर PM2.5 बहुत बढ़ जाता है। उबालें या प्रेशर कुकर उपयोग करें।"
            ),
            is_avoid=True,
        ))
    return actions


def _evening_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    is_en = lang == "en"
    return [
        PlanAction(
            time_label="19:00–21:00",
            block="evening",
            icon="🕯️",
            action="Check tomorrow's forecast" if is_en else "कल का पूर्वानुमान देखें",
            detail=(
                "Plan tomorrow's commute, school run, and outdoor activity based on "
                "the 48-hour AQI forecast."
                if is_en else
                "48 घंटे के AQI पूर्वानुमान के आधार पर कल की योजना बनाएं।"
            ),
        ),
        PlanAction(
            time_label="19:00–21:00",
            block="evening",
            icon="🚫",
            action="No waste burning, no incense sticks" if is_en else "कचरा न जलाएं, अगरबत्ती से बचें",
            detail=(
                "Burning garden waste or incense spikes indoor and neighbourhood PM2.5. "
                "Dispose of waste in municipal bins."
                if is_en else
                "बगीचे का कचरा या अगरबत्ती जलाने से PM2.5 बढ़ता है। कूड़े को म्युनिसिपल बिन में डालें।"
            ),
            is_avoid=True,
        ),
    ]


def _sleep_actions(risk: RiskLevel, profile: HouseholdProfile, lang: str) -> list[PlanAction]:
    is_en = lang == "en"
    actions: list[PlanAction] = [
        PlanAction(
            time_label="21:00–22:00",
            block="sleep",
            icon="😴",
            action="Run purifier in bedroom overnight" if is_en else "रात में बेडरूम में शोधक चलाएं",
            detail=(
                "Sleep-time is 7–9 hours of continuous exposure. Running a HEPA purifier "
                "or DIY Corsi-Rosenthal box in your bedroom is the single highest-impact "
                "indoor air action."
                if is_en else
                "नींद के 7–9 घंटे लगातार संपर्क होता है। HEPA शोधक या DIY फ़िल्टर रात को चलाएं।"
            ),
        )
    ]
    if risk in (RiskLevel.RED, RiskLevel.MAROON):
        actions.append(PlanAction(
            time_label="21:00–22:00",
            block="sleep",
            icon="🔒",
            action="Seal bedroom door gaps with towels" if is_en else "दरवाजे की दरारें बंद करें",
            detail=(
                "On very bad air days, place a rolled towel at the bedroom door gap to "
                "slow infiltration of outdoor PM2.5."
                if is_en else
                "बहुत खराब हवा में कमरे के दरवाजे की दरारों को तौलिए से बंद करें।"
            ),
        ))
    return actions


# ---------------------------------------------------------------------------
# Main plan generator
# ---------------------------------------------------------------------------

def generate_daily_plan(
    profile: HouseholdProfile,
    classification: RiskClassificationResult,
    snapshot: AQISnapshot,
    language: str = "en",
) -> DailyPlan:
    """
    Generate a full 7-block daily plan deterministically.
    Returns a DailyPlan with PlanAction list – no LLM calls made here.
    """
    risk = classification.effective_risk_level
    lang = language if language in ("en", "hi") else "en"

    all_actions: list[PlanAction] = []
    all_actions.extend(_wake_up_actions(risk, profile, lang))
    all_actions.extend(_commute_actions(risk, profile, lang))
    all_actions.extend(_exercise_actions(risk, profile, lang))
    all_actions.extend(_cooking_actions(risk, profile, lang))
    all_actions.extend(_evening_actions(risk, profile, lang))
    all_actions.extend(_sleep_actions(risk, profile, lang))

    headlines = {
        RiskLevel.GREEN:  {
            "en": "Good air day – get outside!",
            "hi": "आज हवा अच्छी है – बाहर जाएं!",
        },
        RiskLevel.YELLOW: {
            "en": "Moderate air – sensitive members, take care.",
            "hi": "मध्यम हवा – संवेदनशील लोग ध्यान रखें।",
        },
        RiskLevel.ORANGE: {
            "en": "Poor air – limit outdoor time and wear a mask.",
            "hi": "खराब हवा – बाहर कम समय बिताएं और मास्क पहनें।",
        },
        RiskLevel.RED: {
            "en": "Unhealthy air – protect yourself indoors.",
            "hi": "अस्वस्थ हवा – अंदर रहकर खुद को सुरक्षित रखें।",
        },
        RiskLevel.MAROON: {
            "en": "⚠️ Hazardous air – stay home, seal up, purify.",
            "hi": "⚠️ खतरनाक हवा – घर में रहें, दरारें बंद करें।",
        },
    }

    headline = headlines[risk].get(lang, headlines[risk]["en"])

    return DailyPlan(
        profile_id=profile.id,
        risk_level=classification.risk_level,
        effective_risk_level=risk,
        aqi_snapshot=snapshot,
        plan_date=date.today().isoformat(),
        language=lang,
        actions=all_actions,
        summary_headline=headline,
    )
