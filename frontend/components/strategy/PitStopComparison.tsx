"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { tireColor } from "@/lib/constants";

interface PitStop {
  id: number;
  driver_code: string;
  lap_number: number;
  duration_seconds: number | null;
  compound_in: string;
}
interface PitResponse {
  pit_stops: PitStop[];
}

/** Fastest-to-slowest pit stops, colored by the compound fitted. */
export function PitStopComparison({ sessionId }: { sessionId: number }) {
  const state = useAsync<PitResponse>(
    () => api.getPitStops(sessionId) as Promise<PitResponse>,
    [sessionId]
  );

  return (
    <StateWrapper state={state} empty="No pit stops recorded for this session.">
      {(data) => <Chart stops={data.pit_stops} />}
    </StateWrapper>
  );
}

function Chart({ stops }: { stops: PitStop[] }) {
  const rows = useMemo(
    () =>
      stops
        .filter((s) => s.duration_seconds != null)
        .sort((a, b) => (a.duration_seconds ?? 0) - (b.duration_seconds ?? 0))
        .map((s) => ({
          label: `${s.driver_code} L${s.lap_number}`,
          duration: s.duration_seconds as number,
          compound: s.compound_in,
        })),
    [stops]
  );

  return (
    <div style={{ height: Math.max(200, rows.length * 22) }} className="w-full">
      <ResponsiveContainer>
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 24, bottom: 4, left: 60 }}
        >
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis
            type="number"
            stroke="#9A9AA5"
            fontSize={11}
            tickFormatter={(v) => `${v}s`}
            domain={["dataMin - 0.5", "dataMax + 0.5"]}
          />
          <YAxis
            type="category"
            dataKey="label"
            stroke="#9A9AA5"
            fontSize={10}
            width={70}
          />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
            formatter={(v: number) => [`${v.toFixed(3)}s`, "pit lane"]}
          />
          <Bar dataKey="duration">
            {rows.map((r, i) => (
              <Cell key={i} fill={tireColor(r.compound)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
