import type { Config } from "tailwindcss";

// Design system "Telemetry" — cockpit HUD meets editorial sports site.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "track-black": "#0A0A0C",
        surface: "#15151A",
        "surface-raised": "#1E1E24",
        border: "#2A2A32",
        "apex-red": "#E10600",
        "drs-green": "#00D2A0",
        "purple-sector": "#C724B1",
        "yellow-flag": "#FFD500",
        "text-primary": "#F5F5F7",
        "text-secondary": "#9A9AA5",
        "text-muted": "#56565F",
        "tire-soft": "#FF3333",
        "tire-medium": "#FFD500",
        "tire-hard": "#F5F5F5",
        "tire-intermediate": "#43B02A",
        "tire-wet": "#0067B1",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["DM Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
