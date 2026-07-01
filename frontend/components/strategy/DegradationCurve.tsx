"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { durationToSeconds, formatLapTime } from "@/lib/format";
import { tireColor } from "@/lib/constants";
import type { Lap } from "@/lib/types";

interface LapsResponse {
  laps: Lap[];
}

/**
 * Lap-time trend within each stint for one driver — the tyre degradation
 * signature. Each stint is a separate line colored by compound; the upward
 * slope is wear. In/out laps and outliers are filtered out.
 */
export function DegradationCurve({
  gpId,
  sessionType,
}: {
  gpId: number;
  sessionType: string;
}) {
  const state = useAsync<LapsResponse>(
    () => api.getSessionLaps(gpId, sessionType) as Promise<LapsResponse>,
    [gpId, sessionType]
  );

  return (
    <StateWrapper state={state}>
      {(data) => <Curve laps={data.laps} />}
    </StateWrapper>
  );
}

function Curve({ laps }: { laps: Lap[] }) {
  const drivers = useMemo(
    () => Array.from(new Set(laps.map((l) => l.driver_code))).sort(),
    [laps]
  );
  const [driver, setDriver] = useState(drivers[0] ?? "");

  const { rows, stints } = useMemo(() => {
    const clean = laps.filter(
      (l) =>
        l.driver_code === driver &&
        l.lap_time &&
        !l.pit_in &&
        !l.pit_out &&
        l.stint_number != null
    );
    const byLap: Record<number, Record<string, number | null>> = {};
    const stintMeta: Record<string, string> = {};
    for (const lap of clean) {
      const key = `stint${lap.stint_number}`;
      stintMeta[key] = lap.compound;
      byLap[lap.lap_number] ??= { lap: lap.lap_number };
      byLap[lap.lap_number][key] = durationToSeconds(lap.lap_time);
    }
    return {
      rows: Object.values(byLap).sort((a, b) => (a.lap as number) - (b.lap as number)),
      stints: stintMeta,
    };
  }, [laps, driver]);

  return (
    <div>
      <label className="mb-3 block text-sm">
        <span className="mr-2 text-xs text-text-muted">Driver</span>
        <select
          value={driver}
          onChange={(e) => setDriver(e.target.value)}
          className="rounded border border-border bg-surface px-3 py-1 font-mono"
        >
          {drivers.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>
      <div className="h-72 w-full">
        <ResponsiveContainer>
          <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
            <XAxis dataKey="lap" stroke="#9A9AA5" fontSize={11} />
            <YAxis
              stroke="#9A9AA5"
              fontSize={11}
              domain={["dataMin - 0.3", "dataMax + 0.3"]}
              tickFormatter={(v) => formatLapTime(v)}
              width={70}
            />
            <Tooltip
              contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
              formatter={(v: number, name) => [formatLapTime(v), `${name} (${stints[name as string]})`]}
            />
            {Object.entries(stints).map(([key, compound]) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={key}
                stroke={tireColor(compound)}
                dot={{ r: 2 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
