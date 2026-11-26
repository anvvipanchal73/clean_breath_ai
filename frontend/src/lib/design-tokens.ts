/**
 * Design tokens – single source of truth for colours, spacing, and typography.
 * Import these in components instead of hardcoding Tailwind strings or hex values.
 */

export const RISK_BG: Record<string, string> = {
  Green:  "bg-cb-green-light text-cb-green-text border-cb-green",
  Yellow: "bg-cb-yellow-light text-cb-yellow-text border-cb-yellow",
  Orange: "bg-cb-orange-light text-cb-orange-text border-cb-orange",
  Red:    "bg-cb-red-light text-cb-red-text border-cb-red",
  Maroon: "bg-cb-maroon-light text-cb-maroon-text border-cb-maroon",
};

export const RISK_BADGE_COLOR: Record<string, string> = {
  Green:  "#2E7D32",
  Yellow: "#F9A825",
  Orange: "#E65100",
  Red:    "#C62828",
  Maroon: "#6A1B9A",
};

/** Spacing scale in rem – used for consistent padding across components. */
export const SPACE = {
  xs: "0.25rem",
  sm: "0.5rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
} as const;

/** Typography – body text size optimised for low-resolution screens. */
export const TEXT = {
  bodyLg: "text-base leading-relaxed",
  bodyMd: "text-sm leading-relaxed",
  bodySm: "text-xs leading-relaxed",
  heading1: "text-2xl font-bold",
  heading2: "text-xl font-semibold",
  heading3: "text-lg font-semibold",
} as const;
