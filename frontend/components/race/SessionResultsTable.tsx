"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { LapTimeDisplay } from "@/components/ui/LapTimeDisplay";
import { TeamColorBar } from "@/components/ui/TeamColorBar";
import type { Driver, Team } from "@/lib/types";

interface Entry {
  id: number;
  driver: Driver;
  team: Team | null;
  grid_position: number | null;
  finish_position: number | null;
  status: string;
  points: number;
  fastest_lap_time: string | null;
}

interface Results {
  results: Entry[];
}

export function SessionResultsTable({
  gpId,
  sessionType,
}: {
  gpId: number;
  sessionType: string;
}) {
  const state = useAsync<Results>(
    () => api.getSessionResults(gpId, sessionType) as Promise<Results>,
    [gpId, sessionType]
  );

  return (
    <StateWrapper state={state} empty="No results ingested for this session.">
      {(data) => (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase text-text-muted">
              <th className="py-2">Pos</th>
              <th>Driver</th>
              <th>Team</th>
              <th>Grid</th>
              <th className="text-right">Fastest</th>
              <th className="text-right">Pts</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((e) => (
              <tr key={e.id} className="border-b border-border/50">
                <td className="py-2 font-mono">{e.finish_position ?? e.status}</td>
                <td className="font-mono">{e.driver.code}</td>
                <td className="flex items-center gap-2">
                  <TeamColorBar color={e.team?.color_hex} />
                  {e.team?.name ?? "—"}
                </td>
                <td className="font-mono">{e.grid_position ?? "—"}</td>
                <td className="text-right">
                  <LapTimeDisplay value={e.fastest_lap_time} />
                </td>
                <td className="text-right font-mono">{e.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </StateWrapper>
  );
}
