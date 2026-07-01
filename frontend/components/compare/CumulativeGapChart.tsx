"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { durationToSeconds } from "@/lib/format";
import { COLORS } from "@/lib/constants";
import type { Lap } from "@/lib/types";

interface DriverBlock {
  driver_code: string;
  laps: Lap[];
  pit_stops: { lap_number: number }[];
}
interface CompareResponse {
  drivers: DriverBlock[];
}

/**
 * Running time difference over the race: cumulative lap time of driver B minus
 * driver A. Above zero => driver A is ahead. Pit stops marked as vertical
 * lines. This is the "who is pulling away, and where" view.
 */
export function CumulativeGapChart({
  sessionId,
  drivers,
}: {
  sessionId: number;
  drivers: [string, string];
}) {
  const state = useAsync<CompareResponse>(
    () => api.compareLaps(sessionId, drivers) as Promise<CompareResponse>,
    [sessionId, drivers.join(",")]
  );

  return (
    <StateWrapper state={state}>
      {(data) => <Chart data={data} drivers={drivers} />}
    </StateWrapper>
  );
}

function cumulative(laps: Lap[]): Map<number, number> {
  const out = new Map<number, number>();
  let sum = 0;
  for (const lap of [...laps].sort((a, b) => a.lap_number - b.lap_number)) {
    const s = durationToSeconds(lap.lap_time);
    if (s == null) continue;
    sum += s;
    out.set(lap.lap_number, sum);
  }
  return out;
}

function Chart({
  data,
  drivers,
}: {
  data: CompareResponse;
  drivers: [string, string];
}) {
  const [a, b] = drivers;
  const { rows, pitLaps } = useMemo(() => {
    const blockA = data.drivers.find((d) => d.driver_code === a);
    const blockB = data.drivers.find((d) => d.driver_code === b);
    const cumA = cumulative(blockA?.laps ?? []);
    const cumB = cumulative(blockB?.laps ?? []);
    const laps = Array.from(new Set([...cumA.keys(), ...cumB.keys()])).sort(
      (x, y) => x - y
    );
    const rows = laps
      .filter((n) => cumA.has(n) && cumB.has(n))
      .map((n) => ({ lap: n, gap: +(cumB.get(n)! - cumA.get(n)!).toFixed(3) }));
    const pitLaps = [
      ...(blockA?.pit_stops ?? []),
      ...(blockB?.pit_stops ?? []),
    ].map((p) => p.lap_number);
    return { rows, pitLaps };
  }, [data, a, b]);

  return (
    <div className="h-72 w-full">
      <p className="mb-2 text-xs text-text-muted">
        Cumulative gap (s). Above zero = {a} ahead of {b}. Dashed lines = pit
        stops.
      </p>
      <ResponsiveContainer>
        <AreaChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <defs>
            <linearGradient id="gapFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS.drsGreen} stopOpacity={0.4} />
              <stop offset="100%" stopColor={COLORS.drsGreen} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis dataKey="lap" stroke="#9A9AA5" fontSize={11} />
          <YAxis
            stroke="#9A9AA5"
            fontSize={11}
            tickFormatter={(v) => `${v > 0 ? "+" : ""}${v}s`}
          />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
            formatter={(v: number) => [`${v > 0 ? "+" : ""}${v}s`, `${a} vs ${b}`]}
          />
          <ReferenceLine y={0} stroke={COLORS.border} />
          {pitLaps.map((lap, i) => (
            <ReferenceLine
              key={i}
              x={lap}
              stroke={COLORS.yellowFlag}
              strokeDasharray="2 2"
              strokeOpacity={0.6}
            />
          ))}
          <Area
            type="monotone"
            dataKey="gap"
            stroke={COLORS.drsGreen}
            fill="url(#gapFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
