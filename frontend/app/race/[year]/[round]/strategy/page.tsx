"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TireStrategyVisualizer } from "@/components/strategy/TireStrategyVisualizer";
import { DegradationCurve } from "@/components/strategy/DegradationCurve";
import { PitStopComparison } from "@/components/strategy/PitStopComparison";
import { StintComparator } from "@/components/strategy/StintComparator";

export default function StrategyPage({
  params,
}: {
  params: { year: string; round: string };
}) {
  const year = Number(params.year);
  const round = Number(params.round);
  const [gpId, setGpId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessionType, setSessionType] = useState("R");
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const gp = await api.resolveRace(year, round);
        if (!gp) throw new Error("Race not found");
        setGpId(gp.id);
        const hub = (await api.getRaceHub(gp.id)) as {
          sessions: { id: number; session_type: string }[];
        };
        const race = hub.sessions.find((s) => s.session_type === "R") ?? hub.sessions[0];
        if (!race) throw new Error("No race session");
        setSessionId(race.id);
        setSessionType(race.session_type);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, [year, round]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Tire Strategy</h1>
        <p className="text-text-secondary">
          Stint history, degradation and pit-stop performance.
        </p>
      </header>
      {error && <p className="text-apex-red">{error}</p>}

      {sessionId && (
        <>
          <div className="card p-4">
            <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
              Stint History
            </h2>
            <TireStrategyVisualizer sessionId={sessionId} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card p-4">
              <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
                Tire Degradation
              </h2>
              {gpId && <DegradationCurve gpId={gpId} sessionType={sessionType} />}
            </div>
            <div className="card p-4">
              <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
                Pit Stop Comparison
              </h2>
              <PitStopComparison sessionId={sessionId} />
            </div>
          </div>

          {gpId && (
            <div className="card p-4">
              <h2 className="mb-3 text-xs uppercase tracking-wide text-text-secondary">
                Strategy Comparator — 1-stop vs 2-stop vs 3-stop
              </h2>
              <StintComparator
                sessionId={sessionId}
                gpId={gpId}
                sessionType={sessionType}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
