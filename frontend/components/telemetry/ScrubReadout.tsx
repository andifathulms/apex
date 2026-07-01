"use client";

import { sampleAtDistance, type SharedScrubProps } from "./shared";

/** Readout panel: both drivers' values at the current scrub distance. */
export function ScrubReadout(props: SharedScrubProps) {
  const { scrubDistance, driver1, driver2, colors } = props;
  const s1 = scrubDistance !== null ? sampleAtDistance(driver1.telemetry, scrubDistance) : null;
  const s2 = scrubDistance !== null ? sampleAtDistance(driver2.telemetry, scrubDistance) : null;

  return (
    <div className="card grid grid-cols-2 gap-4 p-4 font-mono text-sm">
      <Column code={driver1.code} color={colors[0]} sample={s1} />
      <Column code={driver2.code} color={colors[1]} sample={s2} />
      <p className="col-span-2 text-xs text-text-muted">
        {scrubDistance === null
          ? "Hover a chart to inspect this point of the lap."
          : `Distance: ${Math.round(scrubDistance)} m from lap start`}
      </p>
    </div>
  );
}

function Column({
  code,
  color,
  sample,
}: {
  code: string;
  color: string;
  sample: ReturnType<typeof sampleAtDistance>;
}) {
  return (
    <div>
      <div className="mb-1 font-semibold" style={{ color }}>
        {code}
      </div>
      <Row label="Speed" value={sample?.speed_kmh != null ? `${Math.round(sample.speed_kmh)} km/h` : "—"} />
      <Row label="Throttle" value={sample?.throttle_pct != null ? `${Math.round(sample.throttle_pct)}%` : "—"} />
      <Row label="Brake" value={sample ? (sample.brake ? "ON" : "off") : "—"} />
      <Row label="Gear" value={sample?.gear != null ? String(sample.gear) : "—"} />
      <Row label="DRS" value={sample ? (sample.drs ? "OPEN" : "closed") : "—"} />
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-muted">{label}</span>
      <span>{value}</span>
    </div>
  );
}
