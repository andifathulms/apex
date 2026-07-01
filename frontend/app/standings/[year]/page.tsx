"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { StandingsTable } from "@/components/standings/StandingsTable";
import { PointsProgressionChart } from "@/components/standings/PointsProgressionChart";
import { PositionChangeChart } from "@/components/standings/PositionChangeChart";
import { FormGuide } from "@/components/standings/FormGuide";
import { ConstructorStandings } from "@/components/standings/ConstructorStandings";

export default function StandingsPage({
  params,
}: {
  params: { year: string };
}) {
  const year = Number(params.year);
  const [tab, setTab] = useState<"drivers" | "constructors">("drivers");
  const standings = useAsync<any>(() => api.getStandings(year), [year]);
  const progression = useAsync<any>(
    () => api.getStandingsProgression(year),
    [year]
  );

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <div>
          <h1 className="text-2xl font-bold">{year} Standings & Trends</h1>
          <p className="text-text-secondary">
            Championship progression, position swings and form, race by race.
          </p>
        </div>
        <div className="flex gap-2">
          {(["drivers", "constructors"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded border px-3 py-1 text-sm capitalize ${
                tab === t
                  ? "border-apex-red text-text-primary"
                  : "border-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </header>

      {tab === "constructors" ? (
        <ConstructorStandings year={year} />
      ) : (
        <>
          <section className="card p-4">
            <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
              Points Progression
            </h2>
            <StateWrapper state={progression}>
              {(data) => <PointsProgressionChart series={data.series} />}
            </StateWrapper>
          </section>

          <section className="card p-4">
            <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
              Championship Position — who gained/lost when
            </h2>
            <PositionChangeChart year={year} />
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
        </>
      )}
    </div>
  );
}
