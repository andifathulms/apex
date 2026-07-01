export function TeamColorBar({ color }: { color?: string }) {
  return (
    <span
      className="inline-block h-4 w-1 rounded-sm"
      style={{ backgroundColor: color || "#56565F" }}
    />
  );
}
