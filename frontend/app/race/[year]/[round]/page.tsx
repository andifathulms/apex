import { RaceWeekendHub } from "@/components/race/RaceWeekendHub";

export default function RacePage({
  params,
}: {
  params: { year: string; round: string };
}) {
  return (
    <RaceWeekendHub year={Number(params.year)} round={Number(params.round)} />
  );
}
