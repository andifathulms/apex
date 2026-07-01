"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { TeamColorBar } from "@/components/ui/TeamColorBar";
import { PointsProgressionChart } from "./PointsProgressionChart";
import type { Team } from "@/lib/types";

interface ConstructorRow {
  position: number;
  team: Team;
  points: number;
}
interface StandingsResponse {
  standings: ConstructorRow[];
}
interface ProgressionResponse {
  series: { team: string; points: { round: number; points: number }[] }[];
}

export function ConstructorStandings({ year }: { year: number }) {
  const standings = useAsync<StandingsResponse>(
    () => api.getConstructorStandings(year) as Promise<StandingsResponse>,
    [year]
  );
  const progression = useAsync<ProgressionResponse>(
    () => api.getConstructorProgression(year) as Promise<ProgressionResponse>,
    [year]
  );

  return (
    <div className="space-y-6">
      <div className="card p-4">
        <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
          Constructor Points Progression
        </h2>
        <StateWrapper state={progression}>
          {(data) => (
            <PointsProgressionChart
              series={data.series.map((s) => ({ driver: s.team, points: s.points }))}
            />
          )}
        </StateWrapper>
      </div>

      <div className="card p-4">
        <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
          Constructor Standings
        </h2>
        <StateWrapper state={standings}>
          {(data) => (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase text-text-muted">
                  <th className="py-2">Pos</th>
                  <th>Constructor</th>
                  <th className="text-right">Points</th>
                </tr>
              </thead>
              <tbody>
                {data.standings.map((r) => (
                  <tr key={r.team.id} className="border-b border-border/50">
                    <td className="py-2 font-mono">{r.position}</td>
                    <td className="flex items-center gap-2">
                      <TeamColorBar color={r.team.color_hex} />
                      {r.team.name}
                    </td>
                    <td className="text-right font-mono">{r.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </StateWrapper>
      </div>
    </div>
  );
}
