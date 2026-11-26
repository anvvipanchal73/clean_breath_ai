/**
 * CleanBreath AI – Home page (Phase 0 scaffold).
 * Shows the app identity and design system preview.
 * Phase 1 will replace this with the live AQI dashboard.
 */
import type { RiskLevel } from "@/types/cleanbreath";
import { RISK_COLORS, RISK_ICONS } from "@/types/cleanbreath";

const RISK_LEVELS: RiskLevel[] = ["Green", "Yellow", "Orange", "Red", "Maroon"];
const RISK_LABELS: Record<RiskLevel, string> = {
  Green:  "Good",
  Yellow: "Satisfactory",
  Orange: "Moderate",
  Red:    "Poor",
  Maroon: "Severe",
};

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm px-4 pt-safe-top pb-3 flex items-center gap-3">
        <span className="text-3xl" role="img" aria-label="CleanBreath icon">🌬️</span>
        <div>
          <h1 className="text-xl font-bold text-gray-900">CleanBreath AI</h1>
          <p className="text-xs text-gray-500">Breathe safer. Live smarter.</p>
        </div>
      </header>

      <div className="flex-1 px-4 py-6 space-y-6">

        {/* Phase badge */}
        <div
          className="rounded-xl border-2 border-blue-200 bg-blue-50 p-4 text-center"
          role="status"
        >
          <p className="text-sm font-semibold text-blue-800">🚧 Phase 0 – Scaffold</p>
          <p className="text-xs text-blue-600 mt-1">
            Live AQI dashboard and onboarding coming in Phase 1.
          </p>
        </div>

        {/* Design system preview – Risk Level cards */}
        <section aria-labelledby="ds-heading">
          <h2 id="ds-heading" className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
            Design System – Risk Levels
          </h2>
          <div className="space-y-2">
            {RISK_LEVELS.map((level) => {
              const colors = RISK_COLORS[level];
              return (
                <div
                  key={level}
                  className="rounded-xl border-2 p-4 flex items-center gap-3"
                  style={{
                    backgroundColor: colors.bg,
                    color: colors.text,
                    borderColor: colors.border,
                  }}
                >
                  <span className="text-2xl" role="img" aria-label={level}>
                    {RISK_ICONS[level]}
                  </span>
                  <div>
                    <p className="font-semibold">{level}</p>
                    <p className="text-xs opacity-80">{RISK_LABELS[level]}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Medical disclaimer – always visible */}
        <div
          className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900"
          role="note"
          aria-label="Medical disclaimer"
        >
          <span className="font-bold">ℹ️ Note: </span>
          This app provides general guidance only. If you experience breathlessness,
          chest pain, or persistent cough — please see a doctor immediately.
        </div>

        {/* Architecture summary */}
        <section>
          <h2 className="text-sm font-semibold text-gray-600 mb-2 uppercase tracking-wide">
            What&apos;s Built (Phase 0)
          </h2>
          <ul className="space-y-1 text-sm text-gray-700 list-none">
            {[
              "✅ Repo scaffold & .env.example",
              "✅ Supabase + pgvector schema (001_init.sql)",
              "✅ Pydantic domain models (Python)",
              "✅ TypeScript type definitions (mirror)",
              "✅ Deterministic Risk Classifier (Python, unit-tested)",
              "✅ Deterministic Impact Engine (versioned JSON factors)",
              "✅ Deterministic Daily Plan generator",
              "✅ Air Quality ingestion service (Open-Meteo primary)",
              "✅ WCAG AA mobile-first design system",
              "✅ PWA manifest + Service Worker skeleton",
              "✅ Knowledge corpus placeholders (/knowledge)",
              "✅ Unit tests: Risk Classifier, Impact Engine, Models",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
