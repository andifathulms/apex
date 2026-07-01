import { tireColor } from "@/lib/constants";
import type { Stint } from "@/lib/types";

export function StintBar({ stints, totalLaps }: { stints: Stint[]; totalLaps: number }) {
  return (
    <div className="flex h-6 w-full overflow-hidden rounded">
      {stints.map((s, i) => {
        const width = (s.laps / Math.max(totalLaps, 1)) * 100;
        return (
          <div
            key={i}
            className="flex items-center justify-center text-[10px] font-bold text-track-black"
            style={{ width: `${width}%`, backgroundColor: tireColor(s.compound) }}
            title={`${s.compound} · laps ${s.lap_start}-${s.lap_end}`}
          >
            {s.laps > 2 ? s.compound.charAt(0) : ""}
          </div>
        );
      })}
    </div>
  );
}
