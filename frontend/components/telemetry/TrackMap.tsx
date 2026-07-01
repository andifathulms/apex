"use client";

import { useMemo } from "react";
import * as d3 from "d3";
import { COLORS } from "@/lib/constants";
import { sampleAtDistance, type SharedScrubProps } from "./shared";

const SIZE = 300;
const PAD = 16;

/**
 * Track outline built from driver 1's X/Y position data, color-coded by speed.
 * Clicking any point jumps the shared scrub to that distance; the marker
 * follows the scrub position set by any other chart.
 */
export function TrackMap(props: SharedScrubProps) {
  const { scrubDistance, setScrubDistance, driver1, colors } = props;
  const tel = driver1.telemetry.filter(
    (d) => d.x_position !== null && d.y_position !== null
  );

  const { toX, toY, colorFor } = useMemo(() => {
    const xs = tel.map((d) => d.x_position as number);
    const ys = tel.map((d) => d.y_position as number);
    const xScale = d3
      .scaleLinear()
      .domain([Math.min(...xs), Math.max(...xs)])
      .range([PAD, SIZE - PAD]);
    const yScale = d3
      .scaleLinear()
      .domain([Math.min(...ys), Math.max(...ys)])
      .range([SIZE - PAD, PAD]);
    const speedColor = d3
      .scaleSequential(d3.interpolateTurbo)
      .domain([
        d3.min(tel, (d) => d.speed_kmh ?? 0) ?? 0,
        d3.max(tel, (d) => d.speed_kmh ?? 300) ?? 300,
      ]);
    return {
      toX: (v: number) => xScale(v),
      toY: (v: number) => yScale(v),
      colorFor: (s: number) => speedColor(s),
    };
  }, [tel]);

  const marker =
    scrubDistance !== null ? sampleAtDistance(tel, scrubDistance) : null;

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[320px]">
      {/* speed-colored track segments */}
      {tel.slice(1).map((d, i) => {
        const prev = tel[i];
        return (
          <line
            key={i}
            x1={toX(prev.x_position as number)}
            y1={toY(prev.y_position as number)}
            x2={toX(d.x_position as number)}
            y2={toY(d.y_position as number)}
            stroke={colorFor(d.speed_kmh ?? 0)}
            strokeWidth={3}
            strokeLinecap="round"
            onClick={() => setScrubDistance(d.distance)}
            style={{ cursor: "pointer" }}
          />
        );
      })}
      {marker && (
        <circle
          cx={toX(marker.x_position as number)}
          cy={toY(marker.y_position as number)}
          r={5}
          fill={colors[0]}
          stroke={COLORS.trackBlack}
          strokeWidth={1.5}
        />
      )}
    </svg>
  );
}
