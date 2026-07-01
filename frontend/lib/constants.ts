// Tire compound colors must match official F1 convention exactly — do not deviate.
export const TIRE_COLORS = {
  SOFT: "#FF3333",
  MEDIUM: "#FFD500",
  HARD: "#F5F5F5",
  INTERMEDIATE: "#43B02A",
  WET: "#0067B1",
} as const;

export type Compound = keyof typeof TIRE_COLORS;

export function tireColor(compound?: string): string {
  if (!compound) return "#56565F";
  return TIRE_COLORS[compound.toUpperCase() as Compound] ?? "#56565F";
}

// Design tokens mirrored from tailwind.config for use in D3 (which can't read
// Tailwind classes directly).
export const COLORS = {
  trackBlack: "#0A0A0C",
  surface: "#15151A",
  surfaceRaised: "#1E1E24",
  border: "#2A2A32",
  apexRed: "#E10600",
  drsGreen: "#00D2A0",
  purpleSector: "#C724B1",
  yellowFlag: "#FFD500",
  textPrimary: "#F5F5F7",
  textSecondary: "#9A9AA5",
  textMuted: "#56565F",
} as const;

// Two-driver comparison accent colors (driver A / driver B).
export const DRIVER_COLORS = ["#00D2A0", "#E10600"] as const;
