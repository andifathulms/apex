import { formatLapTime } from "@/lib/format";

export function LapTimeDisplay({
  value,
  className = "",
}: {
  value: string | number | null;
  className?: string;
}) {
  return (
    <span className={`font-mono tabular ${className}`}>
      {formatLapTime(value)}
    </span>
  );
}
