import type { Metadata } from "next";
import { api } from "@/lib/api";
import { RaceWeekendHub } from "@/components/race/RaceWeekendHub";

export async function generateMetadata({
  params,
}: {
  params: { year: string; round: string };
}): Promise<Metadata> {
  const year = Number(params.year);
  const round = Number(params.round);
  try {
    const data = (await api.raw(
      `/races/?season__year=${year}&round_number=${round}`
    )) as { results: { name: string }[] };
    const name = data.results[0]?.name;
    if (name) {
      return {
        title: `${year} ${name} — Apex`,
        description: `Session results, tire strategy, lap comparison and telemetry deep dive for the ${year} ${name}.`,
      };
    }
  } catch {
    // fall through to the generic title
  }
  return { title: `${year} Round ${round} — Apex` };
}

export default function RacePage({
  params,
}: {
  params: { year: string; round: string };
}) {
  return (
    <RaceWeekendHub year={Number(params.year)} round={Number(params.round)} />
  );
}
