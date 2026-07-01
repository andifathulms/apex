export interface Driver {
  id: number;
  driver_number: number | null;
  code: string;
  full_name: string;
  nationality: string;
  date_of_birth: string | null;
}

export interface Team {
  id: number;
  name: string;
  nationality: string;
  color_hex: string;
}

export interface Session {
  id: number;
  session_type: string;
  session_type_display: string;
  date: string | null;
  weather_summary: Record<string, unknown>;
  is_loaded: boolean;
}

export interface GrandPrix {
  id: number;
  year: number;
  round_number: number;
  name: string;
  official_name: string;
  circuit_name: string;
  circuit_country: string;
  circuit_location: string;
  date_start: string | null;
  date_end: string | null;
  sessions: Session[];
  fastest_laps?: FastestLapCallout[];
}

export interface FastestLapCallout {
  session_type: string;
  driver_code: string;
  lap_number: number;
  lap_time: string;
}

export interface Lap {
  id: number;
  driver_code: string;
  lap_number: number;
  lap_time: string | null;
  sector1_time: string | null;
  sector2_time: string | null;
  sector3_time: string | null;
  compound: string;
  tyre_life: number | null;
  stint_number: number | null;
  is_personal_best: boolean;
  pit_in: boolean;
  pit_out: boolean;
  track_status: string;
}

export interface TelemetrySample {
  distance: number;
  time_offset: number;
  speed_kmh: number | null;
  throttle_pct: number | null;
  brake: boolean;
  gear: number | null;
  rpm: number | null;
  drs: boolean;
  x_position: number | null;
  y_position: number | null;
}

export interface TelemetryDriverTrace {
  code: string;
  lap_number: number;
  telemetry: TelemetrySample[];
}

export interface DeltaPoint {
  distance: number;
  delta: number;
}

export interface TelemetryComparison {
  status: "ready" | "ingesting";
  session_id: number;
  driver1: TelemetryDriverTrace;
  driver2: TelemetryDriverTrace;
  delta_trace: DeltaPoint[];
}

export interface Stint {
  stint_number: number | null;
  compound: string;
  lap_start: number;
  lap_end: number;
  laps: number;
}

export interface DriverStrategy {
  driver_code: string;
  stints: Stint[];
}
