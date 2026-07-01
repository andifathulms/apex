"use client";

import { useMemo } from "react";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { tireColor } from "@/lib/constants";
import type { DriverStrategy } from "@/lib/types";

interface StrategyResponse {
  strategies: DriverStrategy[];
}
interface ResultsResponse {
  results: {
    driver: { code: string };
    finish_position: number | null;
    status: string;
  }[];
}

interface Bucket {
  stops: number;
  drivers: { code: string; finish: number | null; compounds: string[] }[];
  finishes: number[];
}

/**
 * "What-if" strategy comparator: buckets drivers by number of pit stops and
 * shows how each strategy actually played out (average / best finish). An
 * educational view of 1-stop vs 2-stop vs 3-stop outcomes for the same race.
 */
export function StintComparator({
  sessionId,
  gpId,
  sessionType,
}: {
  sessionId: number;
  gpId: number;
  sessionType: string;
}) {
  const state = useAsync<{ strat: StrategyResponse; res: ResultsResponse }>(
    async () => {
      const [strat, res] = await Promise.all([
        api.getStrategy(sessionId) as Promise<StrategyResponse>,
        api.getSessionResults(gpId, sessionType) as Promise<ResultsResponse>,
      ]);
      return { strat, res };
    },
    [sessionId, gpId, sessionType]
  );

  const buckets = useMemo(() => {
    if (!state.data) return [];
    const finishByCode: Record<string, number | null> = {};
    for (const r of state.data.res.results) {
      finishByCode[r.driver.code] = r.finish_position;
    }
    const byStops: Record<number, Bucket> = {};
    for (const s of state.data.strat.strategies) {
      const stops = Math.max(0, s.stints.length - 1);
      const finish = finishByCode[s.driver_code] ?? null;
      const bucket = (byStops[stops] ??= { stops, drivers: [], finishes: [] });
      bucket.drivers.push({
        code: s.driver_code,
        finish,
        compounds: s.stints.map((st) => st.compound),
      });
      if (finish != null) bucket.finishes.push(finish);
    }
    return Object.values(byStops).sort((a, b) => a.stops - b.stops);
  }, [state.data]);

  return (
    <StateWrapper state={state} empty="Not enough data to compare strategies.">
      {() => (
        <div className="space-y-4">
          <p className="text-xs text-text-muted">
            How each strategy played out — drivers grouped by number of pit stops.
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            {buckets.map((b) => {
              const avg =
                b.finishes.length > 0
                  ? (b.finishes.reduce((s, x) => s + x, 0) / b.finishes.length).toFixed(1)
                  : "—";
              const best = b.finishes.length ? Math.min(...b.finishes) : null;
              return (
                <div key={b.stops} className="rounded border border-border p-3">
                  <div className="mb-2 font-semibold">
                    {b.stops}-stop
                    <span className="ml-2 text-xs text-text-muted">
                      {b.drivers.length} drivers
                    </span>
                  </div>
                  <div className="mb-2 flex gap-4 font-mono text-sm">
                    <span>
                      <span className="text-text-muted">avg</span> P{avg}
                    </span>
                    <span>
                      <span className="text-text-muted">best</span>{" "}
                      {best != null ? `P${best}` : "—"}
                    </span>
                  </div>
                  <ul className="space-y-1 text-xs">
                    {b.drivers
                      .sort((x, y) => (x.finish ?? 99) - (y.finish ?? 99))
                      .map((d) => (
                        <li key={d.code} className="flex items-center gap-2">
                          <span className="w-8 font-mono">{d.code}</span>
                          <span className="flex gap-0.5">
                            {d.compounds.map((c, i) => (
                              <span
                                key={i}
                                className="inline-block h-2 w-2 rounded-full"
                                style={{ backgroundColor: tireColor(c) }}
                              />
                            ))}
                          </span>
                          <span className="ml-auto font-mono text-text-muted">
                            {d.finish != null ? `P${d.finish}` : "DNF"}
                          </span>
                        </li>
                      ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </StateWrapper>
  );
}
