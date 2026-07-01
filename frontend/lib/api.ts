// Server-side fetches use the absolute API base; client-side calls go through
// the Next.js /api rewrite proxy.
const API_BASE =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    // Weekend/standings data is fine to cache briefly; telemetry never cached.
    cache: init?.cache ?? "no-store",
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status} for ${path}`);
  }
  return res.json() as Promise<T>;
}

interface Paginated<T> {
  results: T[];
}

export const api = {
  raw: request,

  // Frontend routes are keyed by year/round; resolve to the internal gp_id.
  resolveRace: async (year: number, round: number) => {
    const data = await request<Paginated<{ id: number }>>(
      `/races/?season__year=${year}&round_number=${round}`
    );
    return data.results[0] ?? null;
  },

  getRaceHub: (gpId: number | string) => request(`/races/${gpId}/`),
  getTrackLayout: (gpId: number | string) => request(`/races/${gpId}/track/`),
  getForm: (year: number) => request(`/seasons/${year}/form/`),
  getSessionResults: (gpId: number | string, type: string) =>
    request(`/races/${gpId}/sessions/${type}/results/`),
  getSessionLaps: (gpId: number | string, type: string) =>
    request(`/races/${gpId}/sessions/${type}/laps/`),

  compareLaps: (sessionId: number, drivers: string[]) =>
    request(`/compare/laps/?session=${sessionId}&drivers=${drivers.join(",")}`),

  getStrategy: (sessionId: number) => request(`/strategy/${sessionId}/`),
  getPitStops: (sessionId: number) => request(`/strategy/${sessionId}/pitstops/`),

  getStandings: (year: number) => request(`/seasons/${year}/standings/`),
  getStandingsProgression: (year: number) =>
    request(`/seasons/${year}/standings/progression/`),

  getDriverCareer: (code: string) => request(`/drivers/${code}/career/`),
  compareDrivers: (a: string, b: string) =>
    request(`/drivers/compare/?a=${a}&b=${b}`),

  getPredictions: (gpId: number | string) => request(`/predictions/${gpId}/`),
};

// Telemetry comparison uses the 202-then-poll pattern. Returns the comparison
// once ready, polling while the backend ingests on demand.
export async function fetchTelemetryComparison(params: {
  session: number;
  driver1: string;
  lap1: number;
  driver2: string;
  lap2: number;
  maxAttempts?: number;
}): Promise<import("./types").TelemetryComparison> {
  const q = new URLSearchParams({
    session: String(params.session),
    driver1: params.driver1,
    lap1: String(params.lap1),
    driver2: params.driver2,
    lap2: String(params.lap2),
  });
  const maxAttempts = params.maxAttempts ?? 12;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const res = await fetch(`/api/compare/telemetry/?${q.toString()}`, {
      cache: "no-store",
    });
    if (res.status === 202) {
      await new Promise((r) => setTimeout(r, 3000));
      continue;
    }
    if (!res.ok) throw new ApiError(res.status, "Telemetry comparison failed");
    return res.json();
  }
  throw new ApiError(504, "Telemetry ingestion timed out");
}
