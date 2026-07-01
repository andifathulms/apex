import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">
          F1 broadcasts show you the result.{" "}
          <span className="text-apex-red">Apex shows you why.</span>
        </h1>
        <p className="max-w-2xl text-text-secondary">
          Using the same timing and telemetry data the teams see, explore race
          weekends at a depth normally reserved for strategists — lap-by-lap
          pace, tire degradation curves, and side-by-side speed traces through
          any corner.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <Link
            key={f.title}
            href={f.href}
            className="card p-5 transition-colors hover:border-apex-red"
          >
            <h2 className="mb-1 font-semibold">{f.title}</h2>
            <p className="text-sm text-text-secondary">{f.blurb}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}

const FEATURES = [
  {
    title: "Race Weekend Hub",
    blurb: "Every session, results, weather and the fastest-lap callout.",
    href: "/race/2024/1",
  },
  {
    title: "Lap Time Comparison",
    blurb: "Overlay two drivers' lap times, sector deltas and pit windows.",
    href: "/race/2024/1/compare",
  },
  {
    title: "Tire Strategy",
    blurb: "Every driver's stint history and degradation, color-coded.",
    href: "/race/2024/1/strategy",
  },
  {
    title: "Telemetry Deep Dive",
    blurb: "Synchronized speed/throttle/brake traces on a live track map.",
    href: "/race/2024/1/telemetry",
  },
  {
    title: "Season Standings & Trends",
    blurb: "Points progression race-by-race, not just the final table.",
    href: "/standings/2024",
  },
  {
    title: "Driver Comparison",
    blurb: "Cross-era, normalized career stats head-to-head.",
    href: "/drivers/compare",
  },
];
