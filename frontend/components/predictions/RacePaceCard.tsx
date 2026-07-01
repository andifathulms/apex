"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { TeamColorBar } from "@/components/ui/TeamColorBar";
import { formatLapTime } from "@/lib/format";
import type { Team } from "@/lib/types";

interface Prediction {
  id: number;
  team: Team;
  predicted_pace_rank: number;
  avg_long_run_pace: number;
  actual_race_rank: number | null;
}

interface PredictionResponse {
  grand_prix: string;
  predictions: Prediction[];
}

export function RacePaceCard({ gpId }: { gpId: number }) {
  const state = useAsync<PredictionResponse>(
    () => api.getPredictions(gpId) as Promise<PredictionResponse>,
    [gpId]
  );

  return (
    <StateWrapper state={state} empty="No prediction computed for this weekend.">
      {(data) => (
        <div>
          <p className="mb-3 text-xs text-text-muted">
            Predicted competitive order from FP2/FP3 fuel-corrected long-run pace.
            Actual race rank shown for accuracy.
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-text-muted">
                <th className="py-2">Pred</th>
                <th>Team</th>
                <th className="text-right">Long-run pace</th>
                <th className="text-right">Actual</th>
              </tr>
            </thead>
            <tbody>
              {data.predictions.map((p) => {
                const delta =
                  p.actual_race_rank != null
                    ? p.predicted_pace_rank - p.actual_race_rank
                    : null;
                return (
                  <tr key={p.id} className="border-b border-border/50">
                    <td className="py-2 font-mono">{p.predicted_pace_rank}</td>
                    <td className="flex items-center gap-2">
                      <TeamColorBar color={p.team.color_hex} />
                      {p.team.name}
                    </td>
                    <td className="text-right font-mono">
                      {formatLapTime(p.avg_long_run_pace)}
                    </td>
                    <td className="text-right font-mono">
                      {p.actual_race_rank ?? "—"}
                      {delta != null && delta !== 0 && (
                        <span
                          className="ml-1 text-xs"
                          style={{ color: delta > 0 ? "#00D2A0" : "#E10600" }}
                        >
                          {delta > 0 ? `▲${delta}` : `▼${-delta}`}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </StateWrapper>
  );
}
