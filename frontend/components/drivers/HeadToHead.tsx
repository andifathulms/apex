"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { DRIVER_COLORS } from "@/lib/constants";

interface Tally {
  a_wins: number;
  b_wins: number;
  rounds: number;
}
interface H2HResponse {
  a: string;
  b: string;
  race: Tally;
  qualifying: Tally;
}

/** Direct teammate/rival head-to-head over a season (race + qualifying). */
export function HeadToHead({
  a,
  b,
  year,
}: {
  a: string;
  b: string;
  year: number;
}) {
  const state = useAsync<H2HResponse>(
    () => api.getHeadToHead(a.toUpperCase(), b.toUpperCase(), year) as Promise<H2HResponse>,
    [a, b, year]
  );

  return (
    <StateWrapper state={state} empty="No shared races that season.">
      {(d) => (
        <div className="space-y-4">
          <Bar label="Race (finishing position)" tally={d.race} a={d.a} b={d.b} />
          <Bar label="Qualifying" tally={d.qualifying} a={d.a} b={d.b} />
        </div>
      )}
    </StateWrapper>
  );
}

function Bar({
  label,
  tally,
  a,
  b,
}: {
  label: string;
  tally: Tally;
  a: string;
  b: string;
}) {
  const total = tally.a_wins + tally.b_wins || 1;
  const aPct = (tally.a_wins / total) * 100;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-text-muted">
        <span>{label}</span>
        <span>{tally.rounds} shared rounds</span>
      </div>
      <div className="flex items-center gap-2 font-mono text-sm">
        <span style={{ color: DRIVER_COLORS[0] }}>
          {a} {tally.a_wins}
        </span>
        <div className="flex h-3 flex-1 overflow-hidden rounded">
          <div style={{ width: `${aPct}%`, backgroundColor: DRIVER_COLORS[0] }} />
          <div style={{ width: `${100 - aPct}%`, backgroundColor: DRIVER_COLORS[1] }} />
        </div>
        <span style={{ color: DRIVER_COLORS[1] }}>
          {tally.b_wins} {b}
        </span>
      </div>
    </div>
  );
}
