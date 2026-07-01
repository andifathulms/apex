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
} from "recharts";

interface Series {
  driver: string;
  points: { round: number; points: number }[];
}

const PALETTE = [
  "#00D2A0", "#E10600", "#FFD500", "#C724B1", "#0067B1",
  "#43B02A", "#F5F5F7", "#FF8700", "#9A9AA5", "#00A3E0",
];

export function PointsProgressionChart({ series }: { series: Series[] }) {
  const { rows, drivers } = useMemo(() => {
    const byRound: Record<number, Record<string, number>> = {};
    for (const s of series) {
      for (const p of s.points) {
        byRound[p.round] ??= { round: p.round };
        byRound[p.round][s.driver] = p.points;
      }
    }
    return {
      rows: Object.values(byRound).sort(
        (a, b) => (a.round as number) - (b.round as number)
      ),
      drivers: series.map((s) => s.driver),
    };
  }, [series]);

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis dataKey="round" stroke="#9A9AA5" fontSize={11} />
          <YAxis stroke="#9A9AA5" fontSize={11} />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
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
