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

  function scrubToClientX(clientX: number) {
    const rect = svgRef.current!.getBoundingClientRect();
    // The SVG scales to its rendered width; map back through the viewBox.
    const scale = CHART.width / rect.width;
    const px = (clientX - rect.left) * scale - CHART.margin.left;
    setScrubDistance(x.invert(Math.max(0, Math.min(innerWidth(), px))));
  }

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    scrubToClientX(e.clientX);
  }

  function handleTouch(e: React.TouchEvent<SVGSVGElement>) {
    if (e.touches.length) scrubToClientX(e.touches[0].clientX);
  }

  // DRS-active bands and gear-change markers from the reference driver (A).
  const { drsBands, gearChanges } = useMemo(() => {
    const bands: Array<{ x0: number; x1: number }> = [];
    const gears: Array<{ x: number; gear: number }> = [];
    let start: number | null = null;
    let prevGear: number | null = null;
    for (const s of driver1.telemetry) {
      if (s.drs && start === null) start = s.distance;
      if (!s.drs && start !== null) {
        bands.push({ x0: x(start), x1: x(s.distance) });
        start = null;
      }
      if (s.gear != null && s.gear !== prevGear) {
        gears.push({ x: x(s.distance), gear: s.gear });
        prevGear = s.gear;
      }
    }
    if (start !== null) bands.push({ x0: x(start), x1: x(driver1.telemetry.at(-1)!.distance) });
    return { drsBands: bands, gearChanges: gears };
  }, [driver1, x]);

  const s1 = scrubDistance !== null ? sampleAtDistance(driver1.telemetry, scrubDistance) : null;
  const s2 = scrubDistance !== null ? sampleAtDistance(driver2.telemetry, scrubDistance) : null;
  const scrubX = scrubDistance !== null ? x(scrubDistance) : null;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${CHART.width} ${CHART.height}`}
      className="w-full touch-none"
      onMouseMove={handleMove}
      onMouseLeave={() => setScrubDistance(null)}
      onTouchStart={handleTouch}
      onTouchMove={handleTouch}
    >
      <g transform={`translate(${CHART.margin.left},${CHART.margin.top})`}>
        {/* DRS-active zones (driver A) */}
        {drsBands.map((b, i) => (
          <rect
            key={`drs-${i}`}
            x={b.x0}
            y={0}
            width={Math.max(0, b.x1 - b.x0)}
            height={innerHeight()}
            fill={COLORS.drsGreen}
            opacity={0.1}
          />
        ))}
        <YAxis y={y} />
        {/* Gear-change ticks along the bottom (driver A) */}
        {gearChanges.map((g, i) => (
          <g key={`gear-${i}`} transform={`translate(${g.x},${innerHeight()})`}>
            <line y1={-4} y2={0} stroke={COLORS.textMuted} strokeWidth={0.5} />
            <text y={-6} textAnchor="middle" fontSize={6} fill={COLORS.textMuted}>
              {g.gear}
            </text>
          </g>
        ))}
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
