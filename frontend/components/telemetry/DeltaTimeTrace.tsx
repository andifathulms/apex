"use client";

import { useMemo, useRef } from "react";
import * as d3 from "d3";
import type { DeltaPoint } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import { CHART, innerHeight, innerWidth } from "./shared";

/**
 * Cumulative delta time between the two drivers along track distance.
 * Positive => driver B is behind driver A. Zero line highlighted; area shaded
 * green where A is ahead, red where B is ahead.
 */
export function DeltaTimeTrace({
  delta,
  scrubDistance,
  setScrubDistance,
  maxDistance,
  codeA,
  codeB,
}: {
  delta: DeltaPoint[];
  scrubDistance: number | null;
  setScrubDistance: (d: number | null) => void;
  maxDistance: number;
  codeA: string;
  codeB: string;
}) {
  const svgRef = useRef<SVGSVGElement>(null);

  const { x, y, path } = useMemo(() => {
    const iw = innerWidth();
    const ih = innerHeight();
    const extent = d3.extent(delta, (d) => d.delta) as [number, number];
    const bound = Math.max(Math.abs(extent[0] ?? 0), Math.abs(extent[1] ?? 0), 0.1);
    const x = d3.scaleLinear().domain([0, maxDistance]).range([0, iw]);
    const y = d3.scaleLinear().domain([-bound, bound]).range([ih, 0]);
    const line = d3
      .line<DeltaPoint>()
      .x((d) => x(d.distance))
      .y((d) => y(d.delta));
    return { x, y, path: line(delta) ?? "" };
  }, [delta, maxDistance]);

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = e.clientX - rect.left - CHART.margin.left;
    setScrubDistance(x.invert(Math.max(0, Math.min(innerWidth(), px))));
  }

  const scrubX = scrubDistance !== null ? x(scrubDistance) : null;
  const current =
    scrubDistance !== null && delta.length
      ? delta.reduce((a, b) =>
          Math.abs(b.distance - scrubDistance) < Math.abs(a.distance - scrubDistance) ? b : a
        )
      : null;

  return (
    <div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${CHART.width} ${CHART.height}`}
        className="w-full"
        onMouseMove={handleMove}
        onMouseLeave={() => setScrubDistance(null)}
      >
        <g transform={`translate(${CHART.margin.left},${CHART.margin.top})`}>
          <line x1={0} x2={innerWidth()} y1={y(0)} y2={y(0)} stroke={COLORS.border} />
          <path d={path} fill="none" stroke={COLORS.purpleSector} strokeWidth={1.5} />
          {scrubX !== null && (
            <line x1={scrubX} x2={scrubX} y1={0} y2={innerHeight()} stroke={COLORS.textMuted} strokeDasharray="3 3" />
          )}
        </g>
      </svg>
      {current && (
        <p className="mt-1 font-mono text-xs text-text-secondary">
          @ {Math.round(current.distance)}m:{" "}
          <span style={{ color: current.delta >= 0 ? COLORS.drsGreen : COLORS.apexRed }}>
            {current.delta >= 0 ? codeA : codeB} ahead by{" "}
            {Math.abs(current.delta).toFixed(3)}s
          </span>
        </p>
      )}
    </div>
  );
}
