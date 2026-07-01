"use client";

interface Weather {
  air_temp?: number;
  track_temp?: number;
  humidity?: number;
  rainfall?: boolean;
}

/** Compact weather readout for a session (from FastF1 weather data). */
export function WeatherSummary({ weather }: { weather?: Weather | null }) {
  if (!weather || Object.keys(weather).length === 0) {
    return (
      <p className="text-xs text-text-muted">No weather data for this session.</p>
    );
  }
  return (
    <div className="flex flex-wrap gap-4 font-mono text-sm">
      {weather.air_temp != null && (
        <Stat label="Air" value={`${weather.air_temp}°C`} />
      )}
      {weather.track_temp != null && (
        <Stat label="Track" value={`${weather.track_temp}°C`} />
      )}
      {weather.humidity != null && (
        <Stat label="Humidity" value={`${weather.humidity}%`} />
      )}
      <Stat
        label="Conditions"
        value={weather.rainfall ? "Wet ☔" : "Dry"}
        accent={weather.rainfall ? "#0067B1" : undefined}
      />
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="text-xs text-text-muted">{label}</span>
      <span style={accent ? { color: accent } : undefined}>{value}</span>
    </span>
  );
}
