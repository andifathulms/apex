"use client";

import { useEffect, useMemo, useState } from "react";
import { api, fetchTelemetryComparison } from "@/lib/api";
import type { Lap, TelemetryComparison } from "@/lib/types";
import { TelemetryDeepDive } from "@/components/telemetry/TelemetryDeepDive";

export default function TelemetryPage({
  params,
}: {
  params: { year: string; round: string };
}) {
  const year = Number(params.year);
  const round = Number(params.round);

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [laps, setLaps] = useState<Lap[]>([]);
  const [driver1, setDriver1] = useState("");
  const [driver2, setDriver2] = useState("");
  const [lap1, setLap1] = useState<number | null>(null);
  const [lap2, setLap2] = useState<number | null>(null);

  const [data, setData] = useState<TelemetryComparison | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState("");

  // Resolve race -> Race session -> lap list (to populate driver/lap pickers).
  useEffect(() => {
    (async () => {
      try {
        const gp = await api.resolveRace(year, round);
        if (!gp) throw new Error("Race not found");
        const hub = (await api.getRaceHub(gp.id)) as {
          sessions: { id: number; session_type: string }[];
        };
        const race =
          hub.sessions.find((s) => s.session_type === "R") ?? hub.sessions[0];
        if (!race) throw new Error("No session");
        setSessionId(race.id);
        const lapData = (await api.getSessionLaps(gp.id, race.session_type)) as {
          laps: Lap[];
        };
        setLaps(lapData.laps);
      } catch (e) {
        setStatus("error");
        setMessage((e as Error).message);
      }
    })();
  }, [year, round]);

  const drivers = useMemo(
    () => Array.from(new Set(laps.map((l) => l.driver_code))).sort(),
    [laps]
  );

  function fastestLapNumber(code: string): number | null {
    const driverLaps = laps.filter((l) => l.driver_code === code && l.lap_time);
    if (!driverLaps.length) return null;
    return driverLaps.reduce((a, b) =>
      (a.lap_time ?? "9") < (b.lap_time ?? "9") ? a : b
    ).lap_number;
  }

  async function load() {
    if (!sessionId || !driver1 || !driver2) return;
    const l1 = lap1 ?? fastestLapNumber(driver1);
    const l2 = lap2 ?? fastestLapNumber(driver2);
    if (l1 == null || l2 == null) {
      setStatus("error");
      setMessage("Could not determine laps to compare.");
      return;
    }
    setStatus("loading");
    setMessage("Ingesting telemetry on demand — this can take a few seconds…");
    try {
      const result = await fetchTelemetryComparison({
        session: sessionId,
        driver1,
        lap1: l1,
        driver2,
        lap2: l2,
      });
      setData(result);
      setStatus("idle");
    } catch (e) {
      setStatus("error");
      setMessage((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Telemetry Deep Dive</h1>
        <p className="text-text-secondary">
          Synchronized speed, throttle/brake and track-map scrub for two drivers.
        </p>
      </header>

      <div className="card flex flex-wrap items-end gap-4 p-4">
        <DriverSelect label="Driver A" value={driver1} onChange={setDriver1} options={drivers} />
        <LapInput label="Lap A" value={lap1} placeholder={driver1 ? fastestLapNumber(driver1) : null} onChange={setLap1} />
        <span className="pb-2 text-text-muted">vs</span>
        <DriverSelect label="Driver B" value={driver2} onChange={setDriver2} options={drivers} />
        <LapInput label="Lap B" value={lap2} placeholder={driver2 ? fastestLapNumber(driver2) : null} onChange={setLap2} />
        <button
          onClick={load}
          disabled={!driver1 || !driver2 || status === "loading"}
          className="rounded bg-apex-red px-4 py-2 text-sm font-semibold disabled:opacity-40"
        >
          {status === "loading" ? "Loading…" : "Compare"}
        </button>
      </div>

      {message && (
        <p className={status === "error" ? "text-apex-red" : "text-text-secondary"}>
          {message}
        </p>
      )}

      {data && <TelemetryDeepDive data={data} />}
    </div>
  );
}

function DriverSelect({
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

function LapInput({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: number | null;
  placeholder: number | null;
  onChange: (v: number | null) => void;
}) {
  return (
    <label className="text-sm">
      <span className="mb-1 block text-xs text-text-muted">{label}</span>
      <input
        type="number"
        value={value ?? ""}
        placeholder={placeholder ? `fastest (${placeholder})` : "fastest"}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-32 rounded border border-border bg-surface px-3 py-2 font-mono"
      />
    </label>
  );
}
