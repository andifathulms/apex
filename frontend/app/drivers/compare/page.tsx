"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  DriverCareerStats,
  type CareerData,
} from "@/components/drivers/DriverCareerStats";
import { HeadToHead } from "@/components/drivers/HeadToHead";

export default function DriverComparePage() {
  const [a, setA] = useState("VER");
  const [b, setB] = useState("HAM");
  const [result, setResult] = useState<{ a: CareerData; b: CareerData } | null>(
    null
  );
  const [h2hYear, setH2hYear] = useState(2024);
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

      <div className="card p-6">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <h2 className="text-sm font-semibold">Head-to-Head</h2>
          <span className="text-xs text-text-muted">
            Direct season comparison — counts only rounds both contested
            (teammates/rivals).
          </span>
          <label className="ml-auto text-sm">
            <span className="mr-2 text-xs text-text-muted">Season</span>
            <input
              type="number"
              value={h2hYear}
              min={2018}
              max={2026}
              onChange={(e) => setH2hYear(Number(e.target.value) || 2024)}
              className="w-24 rounded border border-border bg-surface px-3 py-1 font-mono"
            />
          </label>
        </div>
        <HeadToHead a={a} b={b} year={h2hYear} />
      </div>
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
