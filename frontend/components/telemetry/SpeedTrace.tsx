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

export function SpeedTrace(props: SharedScrubProps) {
  const { scrubDistance, setScrubDistance, maxDistance, driver1, driver2, colors } =
    props;
  const svgRef = useRef<SVGSVGElement>(null);

  const { x, y, linePath } = useMemo(() => {
    const iw = innerWidth();
    const ih = innerHeight();
    const allSpeeds = [...driver1.telemetry, ...driver2.telemetry].map(
      (d) => d.speed_kmh ?? 0
    );
    const x = d3.scaleLinear().domain([0, maxDistance]).range([0, iw]);
    const y = d3
      .scaleLinear()
      .domain([d3.min(allSpeeds) ?? 0, (d3.max(allSpeeds) ?? 300) + 10])
      .range([ih, 0]);
    const line = d3
      .line<TelemetrySample>()
      .defined((d) => d.speed_kmh !== null)
      .x((d) => x(d.distance))
      .y((d) => y(d.speed_kmh ?? 0));
    return {
      x,
      y,
      linePath: (t: TelemetrySample[]) => line(t) ?? "",
    };
  }, [driver1, driver2, maxDistance]);

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = e.clientX - rect.left - CHART.margin.left;
    const dist = x.invert(Math.max(0, Math.min(innerWidth(), px)));
    setScrubDistance(dist);
  }

  const s1 = scrubDistance !== null ? sampleAtDistance(driver1.telemetry, scrubDistance) : null;
  const s2 = scrubDistance !== null ? sampleAtDistance(driver2.telemetry, scrubDistance) : null;
  const scrubX = scrubDistance !== null ? x(scrubDistance) : null;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${CHART.width} ${CHART.height}`}
      className="w-full"
      onMouseMove={handleMove}
      onMouseLeave={() => setScrubDistance(null)}
    >
      <g transform={`translate(${CHART.margin.left},${CHART.margin.top})`}>
        <YAxis y={y} />
        <path d={linePath(driver1.telemetry)} fill="none" stroke={colors[0]} strokeWidth={1.5} />
        <path d={linePath(driver2.telemetry)} fill="none" stroke={colors[1]} strokeWidth={1.5} />
        {scrubX !== null && (
          <line x1={scrubX} x2={scrubX} y1={0} y2={innerHeight()} stroke={COLORS.textMuted} strokeDasharray="3 3" />
        )}
        {s1 && s1.speed_kmh !== null && (
          <circle cx={x(s1.distance)} cy={y(s1.speed_kmh)} r={3} fill={colors[0]} />
        )}
        {s2 && s2.speed_kmh !== null && (
          <circle cx={x(s2.distance)} cy={y(s2.speed_kmh)} r={3} fill={colors[1]} />
        )}
      </g>
    </svg>
  );
}

function YAxis({ y }: { y: d3.ScaleLinear<number, number> }) {
  const ticks = y.ticks(4);
  return (
    <g>
      {ticks.map((t) => (
        <g key={t} transform={`translate(0,${y(t)})`}>
          <line x1={0} x2={innerWidth()} stroke={COLORS.border} strokeWidth={0.5} />
          <text x={-6} dy="0.32em" textAnchor="end" fontSize={9} fill={COLORS.textMuted}>
            {t}
          </text>
        </g>
      ))}
    </g>
  );
}
