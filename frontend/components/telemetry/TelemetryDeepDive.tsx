"use client";

import { useMemo, useState } from "react";
import type { TelemetryComparison } from "@/lib/types";
import { DRIVER_COLORS } from "@/lib/constants";
import { SpeedTrace } from "./SpeedTrace";
import { ThrottleBrakeTrace } from "./ThrottleBrakeTrace";
import { TrackMap } from "./TrackMap";
import { DeltaTimeTrace } from "./DeltaTimeTrace";
import { ScrubReadout } from "./ScrubReadout";

/**
 * Parent of the signature Telemetry Deep Dive. Owns the single shared scrub
 * state (distance along the lap). Every child — speed trace, throttle/brake
 * trace, track map, delta trace, readout — reads the SAME scrubDistance and
 * updates it on the SAME mouse event, so all four visuals stay in lockstep.
 */
export function TelemetryDeepDive({ data }: { data: TelemetryComparison }) {
  const [scrubDistance, setScrubDistance] = useState<number | null>(null);

  const maxDistance = useMemo(() => {
    const d1 = data.driver1.telemetry.at(-1)?.distance ?? 0;
    const d2 = data.driver2.telemetry.at(-1)?.distance ?? 0;
    return Math.max(d1, d2);
  }, [data]);

  const shared = {
    scrubDistance,
    setScrubDistance,
    maxDistance,
    driver1: data.driver1,
    driver2: data.driver2,
    colors: DRIVER_COLORS,
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-6 text-sm">
        <Legend color={DRIVER_COLORS[0]} label={data.driver1.code} />
        <Legend color={DRIVER_COLORS[1]} label={data.driver2.code} />
        <span className="text-text-muted">
          Hover any chart — all views scrub together.
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
            Speed (km/h)
          </h3>
          <SpeedTrace {...shared} />
        </div>
        <div className="card p-4">
          <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
            Track Map
          </h3>
          <TrackMap {...shared} />
        </div>
      </div>

      <div className="card p-4">
        <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
          Throttle / Brake
        </h3>
        <ThrottleBrakeTrace {...shared} />
      </div>

      <div className="card p-4">
        <h3 className="mb-2 text-xs uppercase tracking-wide text-text-secondary">
          Delta Time — where time was gained
        </h3>
        <DeltaTimeTrace
          delta={data.delta_trace}
          scrubDistance={scrubDistance}
          setScrubDistance={setScrubDistance}
          maxDistance={maxDistance}
          codeA={data.driver1.code}
          codeB={data.driver2.code}
        />
      </div>

      <ScrubReadout {...shared} />
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-2">
      <span
        className="inline-block h-2 w-4 rounded-sm"
        style={{ backgroundColor: color }}
      />
      <span className="font-mono">{label}</span>
    </span>
  );
}
