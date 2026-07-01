"use client";

import { useMemo } from "react";
import * as d3 from "d3";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";

interface TrackPoint {
  x_position: number | null;
  y_position: number | null;
  speed_kmh: number | null;
}
interface TrackResponse {
  points: TrackPoint[];
}

const SIZE = 260;
const PAD = 14;

/**
 * Circuit outline for the weekend hub, drawn from position data of a telemetry
 * lap. Speed-colored, so corners (slow) and straights (fast) read at a glance.
 * Only appears once telemetry has been ingested for the weekend.
 */
export function TrackLayoutMap({ gpId }: { gpId: number }) {
  const state = useAsync<TrackResponse>(
    () => api.getTrackLayout(gpId) as Promise<TrackResponse>,
    [gpId]
  );

  const segments = useMemo(() => {
    const pts = (state.data?.points ?? []).filter(
      (p) => p.x_position !== null && p.y_position !== null
    );
    if (pts.length < 2) return null;
    const xs = pts.map((p) => p.x_position as number);
    const ys = pts.map((p) => p.y_position as number);
    const x = d3.scaleLinear().domain([Math.min(...xs), Math.max(...xs)]).range([PAD, SIZE - PAD]);
    const y = d3.scaleLinear().domain([Math.min(...ys), Math.max(...ys)]).range([SIZE - PAD, PAD]);
    const color = d3
      .scaleSequential(d3.interpolateTurbo)
      .domain([
        d3.min(pts, (p) => p.speed_kmh ?? 0) ?? 0,
        d3.max(pts, (p) => p.speed_kmh ?? 300) ?? 300,
      ]);
    return pts.slice(1).map((p, i) => ({
      x1: x(pts[i].x_position as number),
      y1: y(pts[i].y_position as number),
      x2: x(p.x_position as number),
      y2: y(p.y_position as number),
      stroke: color(p.speed_kmh ?? 0),
    }));
  }, [state.data]);

  if (state.loading) return <p className="text-xs text-text-muted">Loading track…</p>;
  if (!segments) {
    return (
      <p className="text-xs text-text-muted">
        Track map appears after telemetry is loaded for this weekend (open the
        Telemetry Deep Dive).
      </p>
    );
  }

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[280px]">
      {segments.map((s, i) => (
        <line
          key={i}
          x1={s.x1}
          y1={s.y1}
          x2={s.x2}
          y2={s.y2}
          stroke={s.stroke}
          strokeWidth={3}
          strokeLinecap="round"
        />
      ))}
    </svg>
  );
}
