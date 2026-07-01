"use client";

import Link from "next/link";
import { TeamColorBar } from "@/components/ui/TeamColorBar";
import type { Driver, Team } from "@/lib/types";

interface Row {
  id: number;
  position: number | null;
  points: number;
  driver: Driver;
  team: Team | null;
}

export function StandingsTable({ standings }: { standings: Row[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-border text-left text-xs uppercase text-text-muted">
          <th className="py-2">Pos</th>
          <th>Driver</th>
          <th>Team</th>
          <th className="text-right">Points</th>
        </tr>
      </thead>
      <tbody>
        {standings.map((r) => (
          <tr key={r.id} className="border-b border-border/50">
            <td className="py-2 font-mono">{r.position ?? "—"}</td>
            <td>
              <Link
                href={`/drivers/${r.driver.code}`}
                className="font-mono hover:text-drs-green"
              >
                {r.driver.code}
              </Link>{" "}
              <span className="text-text-secondary">{r.driver.full_name}</span>
            </td>
            <td className="flex items-center gap-2">
              <TeamColorBar color={r.team?.color_hex} />
              {r.team?.name ?? "—"}
            </td>
            <td className="text-right font-mono">{r.points}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
