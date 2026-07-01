"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TireStrategyVisualizer } from "@/components/strategy/TireStrategyVisualizer";

export default function StrategyPage({
  params,
}: {
  params: { year: string; round: string };
}) {
  const year = Number(params.year);
  const round = Number(params.round);
  const [sessionId, setSessionId] = useState<number | null>(null);
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
        if (!race) throw new Error("No race session");
        setSessionId(race.id);
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
          Every driver's stint history, color-coded by compound.
        </p>
      </header>
      {error && <p className="text-apex-red">{error}</p>}
      {sessionId && (
        <div className="card p-4">
          <TireStrategyVisualizer sessionId={sessionId} />
        </div>
      )}
    </div>
  );
}
