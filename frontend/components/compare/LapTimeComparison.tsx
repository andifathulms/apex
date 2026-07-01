"use client";

import { useMemo } from "react";
import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { DRIVER_COLORS } from "@/lib/constants";
import { durationToSeconds, formatLapTime } from "@/lib/format";
import type { Lap } from "@/lib/types";

interface DriverBlock {
  driver_code: string;
  laps: Lap[];
  pit_stops: { lap_number: number }[];
}

interface CompareResponse {
  drivers: DriverBlock[];
}

export function LapTimeComparison({
  sessionId,
  drivers,
}: {
  sessionId: number;
  drivers: string[];
}) {
  const state = useAsync<CompareResponse>(
    () => api.compareLaps(sessionId, drivers) as Promise<CompareResponse>,
    [sessionId, drivers.join(",")]
  );

  return (
    <StateWrapper state={state}>
      {(data) => <Chart data={data} />}
    </StateWrapper>
  );
}

function Chart({ data }: { data: CompareResponse }) {
  // Merge laps into rows keyed by lap number for Recharts.
  const rows = useMemo(() => {
    const byLap: Record<number, Record<string, number | null>> = {};
    for (const block of data.drivers) {
      for (const lap of block.laps) {
        byLap[lap.lap_number] ??= { lap: lap.lap_number };
        byLap[lap.lap_number][block.driver_code] = durationToSeconds(lap.lap_time);
      }
    }
    return Object.values(byLap).sort(
      (a, b) => (a.lap as number) - (b.lap as number)
    );
  }, [data]);

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis dataKey="lap" stroke="#9A9AA5" fontSize={11} />
          <YAxis
            stroke="#9A9AA5"
            fontSize={11}
            domain={["dataMin - 0.5", "dataMax + 0.5"]}
            tickFormatter={(v) => formatLapTime(v)}
            width={70}
          />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
            formatter={(v: number) => formatLapTime(v)}
          />
          <Legend />
          {data.drivers.map((block, i) => (
            <Line
              key={block.driver_code}
              type="monotone"
              dataKey={block.driver_code}
              stroke={DRIVER_COLORS[i % DRIVER_COLORS.length]}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
