import type { TelemetryDriverTrace, TelemetrySample } from "@/lib/types";

export interface SharedScrubProps {
  scrubDistance: number | null;
  setScrubDistance: (d: number | null) => void;
  maxDistance: number;
  driver1: TelemetryDriverTrace;
  driver2: TelemetryDriverTrace;
  colors: readonly [string, string] | readonly string[];
}

export const CHART = {
  width: 560,
  height: 200,
  margin: { top: 12, right: 12, bottom: 24, left: 40 },
};

export function innerWidth() {
  return CHART.width - CHART.margin.left - CHART.margin.right;
}

export function innerHeight() {
  return CHART.height - CHART.margin.top - CHART.margin.bottom;
}

// Nearest sample to a given distance (binary search on sorted telemetry).
export function sampleAtDistance(
  telemetry: TelemetrySample[],
  distance: number
): TelemetrySample | null {
  if (telemetry.length === 0) return null;
  let lo = 0;
  let hi = telemetry.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (telemetry[mid].distance < distance) lo = mid + 1;
    else hi = mid;
  }
  const cand = telemetry[lo];
  const prev = telemetry[Math.max(0, lo - 1)];
  return Math.abs(prev.distance - distance) < Math.abs(cand.distance - distance)
    ? prev
    : cand;
}
