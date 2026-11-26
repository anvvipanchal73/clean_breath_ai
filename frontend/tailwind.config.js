/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // CleanBreath AI Design System – Risk Level Colours (WCAG AA contrast)
      colors: {
        "cb-green":  { DEFAULT: "#2E7D32", light: "#E8F5E9", text: "#1B5E20" },
        "cb-yellow": { DEFAULT: "#F9A825", light: "#FFFDE7", text: "#7B4B00" },
        "cb-orange": { DEFAULT: "#E65100", light: "#FFF3E0", text: "#BF360C" },
        "cb-red":    { DEFAULT: "#C62828", light: "#FFEBEE", text: "#7F0000" },
        "cb-maroon": { DEFAULT: "#6A1B9A", light: "#F3E5F5", text: "#4A148C" },
        "cb-bg":     "#F5F5F5",
        "cb-surface":"#FFFFFF",
        "cb-primary":"#1565C0",
        "cb-text":   "#212121",
        "cb-muted":  "#757575",
      },
      fontFamily: {
        // System fonts – zero download cost on mobile
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      spacing: {
        "safe-top":    "env(safe-area-inset-top)",
        "safe-bottom": "env(safe-area-inset-bottom)",
      },
      borderRadius: {
        "xl": "1rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
