"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RacePaceCard } from "@/components/predictions/RacePaceCard";

export default function PredictionPage({
  params,
}: {
  params: { year: string; round: string };
}) {
  const year = Number(params.year);
  const round = Number(params.round);
  const [gpId, setGpId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const gp = await api.resolveRace(year, round);
        if (!gp) throw new Error("Race not found");
        setGpId(gp.id);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, [year, round]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Predicted Race Pace</h1>
        <p className="text-text-secondary">
          Pre-race competitive order from practice long-run analysis.
        </p>
      </header>
      {error && <p className="text-apex-red">{error}</p>}
      {gpId && (
        <div className="card p-4">
          <RacePaceCard gpId={gpId} />
        </div>
      )}
    </div>
  );
}
