"use client";

import { useMemo, useRef } from "react";
import * as d3 from "d3";
import type { TelemetrySample } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import {
  CHART,
  innerHeight,
  innerWidth,
  sampleAtDistance,
  type SharedScrubProps,
} from "./shared";

/** Throttle (%) line plus brake-on shaded regions, stacked below speed. */
export function ThrottleBrakeTrace(props: SharedScrubProps) {
  const { scrubDistance, setScrubDistance, maxDistance, driver1, driver2, colors } =
    props;
  const svgRef = useRef<SVGSVGElement>(null);

  const { x, y, throttlePath, brakeRects } = useMemo(() => {
    const iw = innerWidth();
    const ih = innerHeight();
    const x = d3.scaleLinear().domain([0, maxDistance]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);
    const line = d3
      .line<TelemetrySample>()
      .defined((d) => d.throttle_pct !== null)
      .x((d) => x(d.distance))
      .y((d) => y(d.throttle_pct ?? 0));

    // Brake-on distance spans for driver 1 (reference driver).
    const rects: Array<{ x0: number; x1: number }> = [];
    let start: number | null = null;
    for (const s of driver1.telemetry) {
      if (s.brake && start === null) start = s.distance;
      if (!s.brake && start !== null) {
        rects.push({ x0: x(start), x1: x(s.distance) });
        start = null;
      }
    }
    if (start !== null) rects.push({ x0: x(start), x1: x(maxDistance) });

    return {
      x,
      y,
      throttlePath: (t: TelemetrySample[]) => line(t) ?? "",
      brakeRects: rects,
    };
  }, [driver1, maxDistance]);

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = e.clientX - rect.left - CHART.margin.left;
    setScrubDistance(x.invert(Math.max(0, Math.min(innerWidth(), px))));
  }

  const scrubX = scrubDistance !== null ? x(scrubDistance) : null;
  const s1 = scrubDistance !== null ? sampleAtDistance(driver1.telemetry, scrubDistance) : null;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${CHART.width} ${CHART.height}`}
      className="w-full"
      onMouseMove={handleMove}
      onMouseLeave={() => setScrubDistance(null)}
    >
      <g transform={`translate(${CHART.margin.left},${CHART.margin.top})`}>
        {brakeRects.map((r, i) => (
          <rect
            key={i}
            x={r.x0}
            y={0}
            width={Math.max(0, r.x1 - r.x0)}
            height={innerHeight()}
            fill={COLORS.apexRed}
            opacity={0.12}
          />
        ))}
        <path d={throttlePath(driver1.telemetry)} fill="none" stroke={colors[0]} strokeWidth={1.5} />
        <path d={throttlePath(driver2.telemetry)} fill="none" stroke={colors[1]} strokeWidth={1.5} />
        {scrubX !== null && (
          <line x1={scrubX} x2={scrubX} y1={0} y2={innerHeight()} stroke={COLORS.textMuted} strokeDasharray="3 3" />
        )}
        {s1 && (
          <text x={4} y={12} fontSize={9} fill={COLORS.textMuted}>
            {s1.brake ? "BRAKE" : `${Math.round(s1.throttle_pct ?? 0)}% throttle`}
          </text>
        )}
      </g>
    </svg>
  );
}
