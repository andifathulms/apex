"use client";

import { useAsync } from "@/lib/useAsync";
import { api } from "@/lib/api";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { COLORS } from "@/lib/constants";

interface FormRow {
  driver: string;
  last5: number[];
  rolling_avg: number | null;
  races: number;
}
interface FormResponse {
  form: FormRow[];
}

function posColor(pos: number): string {
  if (pos === 1) return COLORS.purpleSector;
  if (pos <= 3) return COLORS.drsGreen;
  if (pos <= 10) return COLORS.textPrimary;
  return COLORS.textMuted;
}

/** Rolling average finishing position over the last 5 races. */
export function FormGuide({ year }: { year: number }) {
  const state = useAsync<FormResponse>(
    () => api.getForm(year) as Promise<FormResponse>,
    [year]
  );

  return (
    <StateWrapper state={state} empty="No form data available.">
      {(data) => (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase text-text-muted">
              <th className="py-2">Driver</th>
              <th>Last 5 (finish)</th>
              <th className="text-right">Avg</th>
            </tr>
          </thead>
          <tbody>
            {data.form.slice(0, 12).map((f) => (
              <tr key={f.driver} className="border-b border-border/50">
                <td className="py-2 font-mono">{f.driver}</td>
                <td>
                  <span className="flex gap-1">
                    {f.last5.map((p, i) => (
                      <span
                        key={i}
                        className="inline-flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold"
                        style={{ border: `1px solid ${posColor(p)}`, color: posColor(p) }}
                      >
                        {p}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="text-right font-mono">{f.rolling_avg ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </StateWrapper>
  );
}
