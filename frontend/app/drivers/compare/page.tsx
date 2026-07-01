"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  DriverCareerStats,
  type CareerData,
} from "@/components/drivers/DriverCareerStats";

export default function DriverComparePage() {
  const [a, setA] = useState("VER");
  const [b, setB] = useState("HAM");
  const [result, setResult] = useState<{ a: CareerData; b: CareerData } | null>(
    null
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function compare() {
    setLoading(true);
    setError("");
    try {
      const data = (await api.compareDrivers(
        a.toUpperCase(),
        b.toUpperCase()
      )) as { a: CareerData; b: CareerData };
      setResult(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Driver Comparison</h1>
        <p className="text-text-secondary">
          Cross-era, normalized career stats head-to-head.
        </p>
      </header>

      <div className="card flex flex-wrap items-end gap-4 p-4">
        <CodeInput label="Driver A" value={a} onChange={setA} />
        <span className="pb-2 text-text-muted">vs</span>
        <CodeInput label="Driver B" value={b} onChange={setB} />
        <button
          onClick={compare}
          disabled={loading}
          className="rounded bg-apex-red px-4 py-2 text-sm font-semibold disabled:opacity-40"
        >
          {loading ? "Loading…" : "Compare"}
        </button>
      </div>

      {error && <p className="text-apex-red">{error}</p>}

      {result && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card p-6">
            <DriverCareerStats data={result.a} />
          </div>
          <div className="card p-6">
            <DriverCareerStats data={result.b} />
          </div>
        </div>
      )}
    </div>
  );
}

function CodeInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="text-sm">
      <span className="mb-1 block text-xs text-text-muted">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={5}
        className="w-28 rounded border border-border bg-surface px-3 py-2 font-mono uppercase"
      />
    </label>
  );
}
