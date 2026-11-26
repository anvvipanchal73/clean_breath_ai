/**
 * CleanBreath AI – TypeScript type definitions for the entire domain.
 * Mirrors the Pydantic models in backend/app/models/domain.py.
 */

// ---------------------------------------------------------------------------
// Risk / AQI
// ---------------------------------------------------------------------------

export type RiskLevel = "Green" | "Yellow" | "Orange" | "Red" | "Maroon";

export const RISK_LEVEL_ORDER: RiskLevel[] = [
  "Green",
  "Yellow",
  "Orange",
  "Red",
  "Maroon",
];

export const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  Green:  { bg: "#E8F5E9", text: "#1B5E20", border: "#2E7D32" },
  Yellow: { bg: "#FFFDE7", text: "#7B4B00", border: "#F9A825" },
  Orange: { bg: "#FFF3E0", text: "#BF360C", border: "#E65100" },
  Red:    { bg: "#FFEBEE", text: "#7F0000", border: "#C62828" },
  Maroon: { bg: "#F3E5F5", text: "#4A148C", border: "#6A1B9A" },
};

export const RISK_ICONS: Record<RiskLevel, string> = {
  Green:  "😊",
  Yellow: "😐",
  Orange: "😷",
  Red:    "⚠️",
  Maroon: "🚨",
};

// ---------------------------------------------------------------------------
// Air Quality
// ---------------------------------------------------------------------------

export interface AQISnapshot {
  lat: number;
  lon: number;
  aqi_us: number | null;
  aqi_in: number | null;
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  o3: number | null;
  temperature_c: number | null;
  wind_speed_kmh: number | null;
  humidity_pct: number | null;
  boundary_layer_height_m: number | null;
  stagnation_risk: boolean;
  source: string;
  fetched_at: string; // ISO datetime string
  is_stale: boolean;
}

export interface ForecastPoint {
  time: string;
  aqi_us: number | null;
  pm25: number | null;
  temperature_c: number | null;
}

export interface AQIForecast {
  lat: number;
  lon: number;
  points: ForecastPoint[];
  source: string;
  fetched_at: string;
}

// ---------------------------------------------------------------------------
// Risk Classification
// ---------------------------------------------------------------------------

export interface RiskClassificationResult {
  aqi_value: number;
  aqi_scale: string;
  risk_level: RiskLevel;
  effective_risk_level: RiskLevel;
  is_adjusted_for_sensitive: boolean;
  health_message: string;
  color_hex: string;
  icon_emoji: string;
  suggest_medical_escalation: boolean;
}

// ---------------------------------------------------------------------------
// Household Profile
// ---------------------------------------------------------------------------

export type CommuteMode =
  | "walk"
  | "cycle"
  | "public_transit"
  | "motorcycle"
  | "car_petrol"
  | "car_diesel"
  | "car_cng"
  | "car_electric"
  | "auto_rickshaw"
  | "work_from_home";

export type CookingFuel = "lpg" | "png" | "biomass" | "kerosene" | "electric" | "induction";
export type HeatingMethod =
  | "none"
  | "central_gas"
  | "room_heater_electric"
  | "room_heater_oil"
  | "coal"
  | "wood"
  | "biomass";
export type BudgetTier = "low" | "medium" | "high";
export type SensitiveCondition =
  | "asthma"
  | "copd"
  | "heart_disease"
  | "pregnancy"
  | "infant"
  | "child_under_12"
  | "elderly";

export interface HouseholdProfile {
  id?: string;
  city: string;
  area: string;
  coarse_lat: number;
  coarse_lon: number;
  timezone: string;
  household_size: number;
  age_groups: string[];
  sensitive_groups: SensitiveCondition[];
  health_data_consent: boolean;
  commute_mode: CommuteMode;
  commute_one_way_km: number;
  home_type: string;
  cooking_fuel: CookingFuel;
  heating_method: HeatingMethod;
  budget_tier: BudgetTier;
  preferred_language: "en" | "hi";
}

// ---------------------------------------------------------------------------
// Daily Plan
// ---------------------------------------------------------------------------

export interface PlanAction {
  time_label: string;
  block: "wake_up" | "commute" | "school" | "exercise" | "cooking" | "evening" | "sleep";
  icon: string;
  action: string;
  detail: string;
  impact_note: string | null;
  is_avoid: boolean;
}

export interface DailyPlan {
  profile_id: string | null;
  risk_level: RiskLevel;
  effective_risk_level: RiskLevel;
  aqi_snapshot: AQISnapshot;
  plan_date: string;
  language: string;
  actions: PlanAction[];
  summary_headline: string;
  medical_disclaimer: string;
  generated_at: string;
}

// ---------------------------------------------------------------------------
// Impact Engine
// ---------------------------------------------------------------------------

export interface ImpactResult {
  action_key: string;
  description: string;
  pm25_avoided_ug_per_day: number | null;
  co2_avoided_kg_per_day: number | null;
  money_saved_inr_per_day: number | null;
  assumptions: string[];
  sources: string[];
  factor_version: string;
}

// ---------------------------------------------------------------------------
// Community
// ---------------------------------------------------------------------------

export type PledgeType =
  | "carpool_day"
  | "no_waste_burning"
  | "public_transit"
  | "clean_cooking"
  | "no_idling"
  | "cycle_day";

export interface CommunityGroup {
  id: string;
  name: string;
  city: string;
  area: string;
  join_code: string;
  member_count: number;
}

export interface CommunityPledge {
  group_id: string;
  pledge_type: PledgeType;
  estimated_pm25_g_avoided: number;
  estimated_co2_kg_avoided: number;
  estimated_money_saved_inr: number;
}

// ---------------------------------------------------------------------------
// API response wrappers
// ---------------------------------------------------------------------------

export interface ApiError {
  detail: string;
  code?: string;
}

export type ApiResponse<T> = { data: T; error: null } | { data: null; error: ApiError };
