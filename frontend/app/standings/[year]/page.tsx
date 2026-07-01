"use client";

import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { StandingsTable } from "@/components/standings/StandingsTable";
import { PointsProgressionChart } from "@/components/standings/PointsProgressionChart";
import { FormGuide } from "@/components/standings/FormGuide";

export default function StandingsPage({
  params,
}: {
  params: { year: string };
}) {
  const year = Number(params.year);
  const standings = useAsync<any>(() => api.getStandings(year), [year]);
  const progression = useAsync<any>(
    () => api.getStandingsProgression(year),
    [year]
  );

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold">{year} Standings & Trends</h1>
        <p className="text-text-secondary">
          Championship points progression, race by race.
        </p>
      </header>

      <section className="card p-4">
        <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
          Points Progression
        </h2>
        <StateWrapper state={progression}>
          {(data) => <PointsProgressionChart series={data.series} />}
        </StateWrapper>
      </section>

      <div className="grid gap-8 lg:grid-cols-3">
        <section className="card p-4 lg:col-span-2">
          <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
            Driver Standings
          </h2>
          <StateWrapper state={standings}>
            {(data) => <StandingsTable standings={data.standings} />}
          </StateWrapper>
        </section>

        <section className="card p-4">
          <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
            Form Guide — last 5
          </h2>
          <FormGuide year={year} />
        </section>
      </div>
    </div>
  );
}
