"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Lap } from "@/lib/types";
import { LapTimeComparison } from "@/components/compare/LapTimeComparison";
import { SectorDeltaChart } from "@/components/compare/SectorDeltaChart";
import { CumulativeGapChart } from "@/components/compare/CumulativeGapChart";

export default function ComparePage({
  params,
}: {
  params: { year: string; round: string };
}) {
  const year = Number(params.year);
  const round = Number(params.round);

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [laps, setLaps] = useState<Lap[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const gp = await api.resolveRace(year, round);
        if (!gp) throw new Error("Race not found");
        const hub = (await api.getRaceHub(gp.id)) as {
          sessions: { id: number; session_type: string }[];
        };
        const race = hub.sessions.find((s) => s.session_type === "R") ?? hub.sessions[0];
        if (!race) throw new Error("No session");
        setSessionId(race.id);
        const lapData = (await api.getSessionLaps(gp.id, race.session_type)) as {
          laps: Lap[];
        };
        setLaps(lapData.laps);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, [year, round]);

  const drivers = useMemo(
    () => Array.from(new Set(laps.map((l) => l.driver_code))).sort(),
    [laps]
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Lap Time Comparison</h1>
        <p className="text-text-secondary">
          Overlay two drivers' lap times across the session.
        </p>
      </header>

      <div className="card flex flex-wrap items-end gap-4 p-4">
        <Select label="Driver A" value={a} onChange={setA} options={drivers} />
        <span className="pb-2 text-text-muted">vs</span>
        <Select label="Driver B" value={b} onChange={setB} options={drivers} />
      </div>

      {error && <p className="text-apex-red">{error}</p>}

      {sessionId && a && b && (
        <div className="space-y-6">
          <div className="card p-4">
            <h2 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
              Lap Times
            </h2>
            <LapTimeComparison sessionId={sessionId} drivers={[a, b]} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card p-4">
              <h2 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
                Sector Deltas
              </h2>
              <SectorDeltaChart sessionId={sessionId} drivers={[a, b]} />
            </div>
            <div className="card p-4">
              <h2 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
                Cumulative Gap
              </h2>
              <CumulativeGapChart sessionId={sessionId} drivers={[a, b]} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <label className="text-sm">
      <span className="mb-1 block text-xs text-text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-border bg-surface px-3 py-2 font-mono"
      >
        <option value="">—</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}
