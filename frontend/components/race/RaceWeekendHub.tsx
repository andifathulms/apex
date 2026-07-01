"use client";

import { useState } from "react";
import Link from "next/link";
import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { LapTimeDisplay } from "@/components/ui/LapTimeDisplay";
import type { GrandPrix } from "@/lib/types";
import { SessionResultsTable } from "./SessionResultsTable";
import { WeatherSummary } from "./WeatherSummary";
import { TrackLayoutMap } from "./TrackLayoutMap";

export function RaceWeekendHub({
  year,
  round,
}: {
  year: number;
  round: number;
}) {
  const state = useAsync<GrandPrix>(async () => {
    const gp = await api.resolveRace(year, round);
    if (!gp) throw new Error(`No race for ${year} round ${round}`);
    return api.getRaceHub(gp.id) as Promise<GrandPrix>;
  }, [year, round]);

  return (
    <StateWrapper state={state}>
      {(gp) => <HubContent gp={gp} year={year} round={round} />}
    </StateWrapper>
  );
}

function HubContent({
  gp,
  year,
  round,
}: {
  gp: GrandPrix;
  year: number;
  round: number;
}) {
  const [active, setActive] = useState(
    gp.sessions.find((s) => s.session_type === "R")?.session_type ??
      gp.sessions[0]?.session_type ??
      "R"
  );
  const activeSession = gp.sessions.find((s) => s.session_type === active);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-xs uppercase tracking-wide text-text-muted">
          {gp.year} · Round {gp.round_number}
        </p>
        <h1 className="text-2xl font-bold">{gp.name}</h1>
        <p className="text-text-secondary">
          {gp.circuit_name} · {gp.circuit_location}, {gp.circuit_country}
        </p>
      </header>

      <nav className="flex flex-wrap gap-4 text-sm">
        <Link className="text-drs-green hover:underline" href={`/race/${year}/${round}/compare`}>
          Lap Comparison →
        </Link>
        <Link className="text-drs-green hover:underline" href={`/race/${year}/${round}/strategy`}>
          Tire Strategy →
        </Link>
        <Link className="text-drs-green hover:underline" href={`/race/${year}/${round}/telemetry`}>
          Telemetry Deep Dive →
        </Link>
        <Link className="text-drs-green hover:underline" href={`/race/${year}/${round}/prediction`}>
          Race Pace Prediction →
        </Link>
      </nav>

      {gp.fastest_laps && gp.fastest_laps.length > 0 && (
        <div className="card p-4">
          <h2 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
            Fastest Laps
          </h2>
          <ul className="flex flex-wrap gap-4 text-sm">
            {gp.fastest_laps.map((f) => (
              <li key={f.session_type} className="font-mono">
                <span className="text-text-muted">{f.session_type}</span>{" "}
                {f.driver_code} <LapTimeDisplay value={f.lap_time} />
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <div className="mb-3 flex flex-wrap gap-2">
          {gp.sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActive(s.session_type)}
              className={`rounded border px-3 py-1 text-sm ${
                active === s.session_type
                  ? "border-apex-red text-text-primary"
                  : "border-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {s.session_type_display}
            </button>
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="card p-4 lg:col-span-2">
            <SessionResultsTable gpId={gp.id} sessionType={active} />
          </div>
          <div className="space-y-4">
            <div className="card p-4">
              <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
                Weather
              </h3>
              <WeatherSummary weather={activeSession?.weather_summary as never} />
            </div>
            <div className="card p-4">
              <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
                Circuit
              </h3>
              <TrackLayoutMap gpId={gp.id} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
