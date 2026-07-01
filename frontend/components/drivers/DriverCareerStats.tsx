import type { Driver } from "@/lib/types";

export interface CareerData {
  driver: Driver;
  stats: {
    races_entered: number;
    wins: number;
    podiums: number;
    dnfs: number;
    poles: number;
    total_points: number;
    win_rate: number;
    podium_rate: number;
    dnf_rate: number;
    points_per_race: number;
  };
}

const FIELDS: { key: keyof CareerData["stats"]; label: string; pct?: boolean }[] = [
  { key: "races_entered", label: "Races" },
  { key: "wins", label: "Wins" },
  { key: "podiums", label: "Podiums" },
  { key: "poles", label: "Poles" },
  { key: "dnfs", label: "DNFs" },
  { key: "total_points", label: "Points" },
  { key: "win_rate", label: "Win rate", pct: true },
  { key: "podium_rate", label: "Podium rate", pct: true },
  { key: "dnf_rate", label: "DNF rate", pct: true },
  { key: "points_per_race", label: "Pts / race" },
];

export function DriverCareerStats({ data }: { data: CareerData }) {
  return (
    <div>
      <h2 className="mb-1 font-mono text-lg">{data.driver.code}</h2>
      <p className="mb-4 text-sm text-text-secondary">{data.driver.full_name}</p>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {FIELDS.map((f) => (
          <div key={f.key} className="flex justify-between border-b border-border/50 pb-1">
            <dt className="text-text-muted">{f.label}</dt>
            <dd className="font-mono">
              {f.pct
                ? `${(Number(data.stats[f.key]) * 100).toFixed(1)}%`
                : data.stats[f.key]}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
