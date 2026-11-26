/**
 * Typed API client for CleanBreath AI backend.
 * Uses fetch with consistent error handling; designed to work offline
 * (service worker returns cached data or a stale JSON payload).
 */
import type {
  AQIForecast,
  AQISnapshot,
  ApiResponse,
  DailyPlan,
  HouseholdProfile,
  ImpactResult,
  RiskClassificationResult,
} from "@/types/cleanbreath";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return {
        data: null,
        error: { detail: body.detail ?? "Request failed", code: String(res.status) },
      };
    }

    const data: T = await res.json();
    return { data, error: null };
  } catch (err) {
    return {
      data: null,
      error: {
        detail:
          err instanceof Error ? err.message : "Network error – check your connection.",
        code: "NETWORK_ERROR",
      },
    };
  }
}

// ---------------------------------------------------------------------------
// Air Quality
// ---------------------------------------------------------------------------

export async function getAirQuality(lat: number, lon: number) {
  return request<AQISnapshot>(`/api/v1/air/current?lat=${lat}&lon=${lon}`);
}

export async function getForecast(lat: number, lon: number) {
  return request<AQIForecast>(`/api/v1/air/forecast?lat=${lat}&lon=${lon}`);
}

// ---------------------------------------------------------------------------
// Onboarding & Profile
// ---------------------------------------------------------------------------

export async function upsertProfile(profile: HouseholdProfile) {
  return request<HouseholdProfile>("/api/v1/onboarding/profile", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

// ---------------------------------------------------------------------------
// Risk & Plan
// ---------------------------------------------------------------------------

export async function classifyRisk(lat: number, lon: number, profileId?: string) {
  const qs = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  if (profileId) qs.set("profile_id", profileId);
  return request<RiskClassificationResult>(`/api/v1/risk/classify?${qs}`);
}

export async function getDailyPlan(lat: number, lon: number, profileId?: string) {
  const qs = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  if (profileId) qs.set("profile_id", profileId);
  return request<DailyPlan>(`/api/v1/plan/daily?${qs}`);
}

// ---------------------------------------------------------------------------
// Impact Engine
// ---------------------------------------------------------------------------

export async function calcImpact(actionKey: string, params: Record<string, unknown>) {
  return request<ImpactResult>("/api/v1/impact/calculate", {
    method: "POST",
    body: JSON.stringify({ action_key: actionKey, params }),
  });
}
