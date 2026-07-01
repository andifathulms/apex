import { tireColor } from "@/lib/constants";

export function TireCompoundBadge({ compound }: { compound?: string }) {
  if (!compound) return null;
  const color = tireColor(compound);
  const letter = compound.charAt(0).toUpperCase();
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-bold"
      style={{ borderColor: color, color }}
      title={compound}
    >
      {letter}
    </span>
  );
}
