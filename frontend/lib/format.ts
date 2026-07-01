// Parse a Django DurationField string ("H:MM:SS.ffffff" or "MM:SS.ff") or a
// numeric seconds value into total seconds.
export function durationToSeconds(value: string | number | null): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number") return value;
  const parts = value.split(":").map(Number);
  if (parts.some(Number.isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return parts[0];
}

// Format seconds as F1 lap time M:SS.mmm (DM Mono aligned).
export function formatLapTime(value: string | number | null): string {
  const total = durationToSeconds(value);
  if (total === null) return "—";
  const minutes = Math.floor(total / 60);
  const seconds = total - minutes * 60;
  const secStr = seconds.toFixed(3).padStart(6, "0");
  return `${minutes}:${secStr}`;
}

// Signed delta in seconds, e.g. "+0.213" / "-0.048".
export function formatDelta(seconds: number): string {
  const sign = seconds >= 0 ? "+" : "-";
  return `${sign}${Math.abs(seconds).toFixed(3)}`;
}
