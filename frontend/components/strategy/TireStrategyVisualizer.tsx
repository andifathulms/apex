"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import type { DriverStrategy } from "@/lib/types";
import { StintBar } from "./StintBar";

interface StrategyResponse {
  strategies: DriverStrategy[];
}

export function TireStrategyVisualizer({ sessionId }: { sessionId: number }) {
  const state = useAsync<StrategyResponse>(
    () => api.getStrategy(sessionId) as Promise<StrategyResponse>,
    [sessionId]
  );

  return (
    <StateWrapper state={state}>
      {(data) => {
        const totalLaps = Math.max(
          1,
          ...data.strategies.flatMap((s) => s.stints.map((st) => st.lap_end))
        );
        return (
          <div className="space-y-2">
            {data.strategies.map((strat) => (
              <div key={strat.driver_code} className="flex items-center gap-3">
                <span className="w-10 font-mono text-sm">{strat.driver_code}</span>
                <div className="flex-1">
                  <StintBar stints={strat.stints} totalLaps={totalLaps} />
                </div>
              </div>
            ))}
          </div>
        );
      }}
    </StateWrapper>
  );
}
