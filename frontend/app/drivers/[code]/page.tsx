import type { Metadata } from "next";
import { api } from "@/lib/api";
import { DriverCareerView } from "@/components/drivers/DriverCareerView";

export async function generateMetadata({
  params,
}: {
  params: { code: string };
}): Promise<Metadata> {
  const code = params.code.toUpperCase();
  try {
    const data = (await api.getDriverCareer(code)) as {
      driver: { full_name: string };
    };
    const name = data.driver?.full_name;
    if (name) {
      return {
        title: `${name} (${code}) — Apex`,
        description: `Career stats — wins, podiums, poles, points per race — for ${name}.`,
      };
    }
  } catch {
    // fall through
  }
  return { title: `${code} — Apex` };
}

export default function DriverPage({ params }: { params: { code: string } }) {
  return <DriverCareerView code={params.code.toUpperCase()} />;
}
