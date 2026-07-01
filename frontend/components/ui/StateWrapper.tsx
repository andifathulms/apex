import type { AsyncState } from "@/lib/useAsync";

/** Renders loading / error / empty states around async data. */
export function StateWrapper<T>({
  state,
  children,
  empty,
}: {
  state: AsyncState<T>;
  children: (data: T) => React.ReactNode;
  empty?: string;
}) {
  if (state.loading) {
    return <p className="text-text-secondary">Loading…</p>;
  }
  if (state.error) {
    return (
      <div className="card border-apex-red/40 p-4 text-sm text-text-secondary">
        Could not load data — the backend may not be running or this session has
        no ingested data yet.
        <span className="mt-1 block font-mono text-xs text-text-muted">
          {state.error}
        </span>
      </div>
    );
  }
  if (!state.data) {
    return <p className="text-text-muted">{empty ?? "No data."}</p>;
  }
  return <>{children(state.data)}</>;
}
