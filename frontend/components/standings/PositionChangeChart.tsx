"use client";

import { useMemo } from "react";
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

interface Point {
  round: number;
  position: number | null;
}
interface Series {
  driver: string;
  points: Point[];
}
interface ProgressionResponse {
  series: Series[];
}

const PALETTE = [
  "#00D2A0", "#E10600", "#FFD500", "#C724B1", "#0067B1",
  "#43B02A", "#F5F5F7", "#FF8700", "#9A9AA5", "#00A3E0",
];

/** Championship position over the season (bump chart, P1 at top). */
export function PositionChangeChart({ year }: { year: number }) {
  const state = useAsync<ProgressionResponse>(
    () => api.getStandingsProgression(year) as Promise<ProgressionResponse>,
    [year]
  );

  return (
    <StateWrapper state={state}>
      {(data) => <Chart series={data.series} />}
    </StateWrapper>
  );
}

function Chart({ series }: { series: Series[] }) {
  const { rows, drivers } = useMemo(() => {
    // Keep the 10 drivers with the best final championship position.
    const finalPos = (s: Series) =>
      s.points.filter((p) => p.position != null).at(-1)?.position ?? 99;
    const top = [...series].sort((a, b) => finalPos(a) - finalPos(b)).slice(0, 10);

    const byRound: Record<number, Record<string, number | null>> = {};
    for (const s of top) {
      for (const p of s.points) {
        byRound[p.round] ??= { round: p.round };
        byRound[p.round][s.driver] = p.position;
      }
    }
    return {
      rows: Object.values(byRound).sort(
        (a, b) => (a.round as number) - (b.round as number)
      ),
      drivers: top.map((s) => s.driver),
    };
  }, [series]);

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis dataKey="round" stroke="#9A9AA5" fontSize={11} />
          <YAxis
            stroke="#9A9AA5"
            fontSize={11}
            reversed
            domain={[1, "dataMax"]}
            allowDecimals={false}
            width={28}
          />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
            formatter={(v: number, name) => [`P${v}`, name]}
          />
          {drivers.map((d, i) => (
            <Line
              key={d}
              type="monotone"
              dataKey={d}
              stroke={PALETTE[i % PALETTE.length]}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
