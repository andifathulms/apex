import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Apex — F1 Analytics",
  description:
    "Fan-facing Formula 1 analytics: lap comparisons, tire strategy, and corner-by-corner telemetry deep dives.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-border bg-surface">
          <nav className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-4">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-apex-red">
                APEX
              </span>
              <span className="text-xs text-text-muted">F1 ANALYTICS</span>
            </Link>
            <div className="flex gap-4 text-sm text-text-secondary">
              <Link href="/" className="hover:text-text-primary">
                Home
              </Link>
              <Link href="/standings/2024" className="hover:text-text-primary">
                Standings
              </Link>
              <Link href="/drivers/compare" className="hover:text-text-primary">
                Compare Drivers
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        <footer className="border-t border-border px-6 py-6 text-center text-xs text-text-muted">
          Apex is an unofficial fan project, not associated with Formula 1
          companies. Built on FastF1. No official F1 or team logos are used.
          Data may be incomplete for some sessions.
        </footer>
      </body>
    </html>
  );
}
