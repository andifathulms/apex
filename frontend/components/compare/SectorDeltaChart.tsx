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
import { durationToSeconds } from "@/lib/format";
import { COLORS } from "@/lib/constants";
import type { Lap } from "@/lib/types";

interface DriverBlock {
  driver_code: string;
  laps: Lap[];
}
interface CompareResponse {
  drivers: DriverBlock[];
}

function median(values: number[]): number | null {
  const v = values.filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
  if (!v.length) return null;
  const mid = Math.floor(v.length / 2);
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}

/**
 * Where each driver gains/loses time by sector. Bars show driver A's median
 * sector time minus driver B's: negative (green) = A quicker, positive (red) =
 * A slower. Medians ignore in/out and outlier laps naturally.
 */
export function SectorDeltaChart({
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

function Chart({
  data,
  drivers,
}: {
  data: CompareResponse;
  drivers: [string, string];
}) {
  const rows = useMemo(() => {
    const medians: Record<string, (number | null)[]> = {};
    for (const block of data.drivers) {
      medians[block.driver_code] = [1, 2, 3].map((s) =>
        median(
          block.laps.map((l) =>
            durationToSeconds(
              (l as unknown as Record<string, string | null>)[`sector${s}_time`]
            ) as number
          )
        )
      );
    }
    const [a, b] = drivers;
    return [1, 2, 3].map((s, i) => {
      const av = medians[a]?.[i];
      const bv = medians[b]?.[i];
      const delta = av != null && bv != null ? +(av - bv).toFixed(3) : 0;
      return { sector: `S${s}`, delta };
    });
  }, [data, drivers]);

  return (
    <div className="h-64 w-full">
      <p className="mb-2 text-xs text-text-muted">
        {drivers[0]} vs {drivers[1]} — bar below zero means {drivers[0]} is
        quicker in that sector.
      </p>
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#2A2A32" strokeDasharray="3 3" />
          <XAxis dataKey="sector" stroke="#9A9AA5" fontSize={12} />
          <YAxis
            stroke="#9A9AA5"
            fontSize={11}
            tickFormatter={(v) => `${v > 0 ? "+" : ""}${v}s`}
          />
          <Tooltip
            contentStyle={{ background: "#15151A", border: "1px solid #2A2A32" }}
            formatter={(v: number) => [`${v > 0 ? "+" : ""}${v}s`, "delta"]}
          />
          <Bar dataKey="delta">
            {rows.map((r, i) => (
              <Cell
                key={i}
                fill={r.delta <= 0 ? COLORS.drsGreen : COLORS.apexRed}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
