"use client";

import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { StateWrapper } from "@/components/ui/StateWrapper";
import { DriverCareerStats, type CareerData } from "./DriverCareerStats";

export function DriverCareerView({ code }: { code: string }) {
  const state = useAsync<CareerData>(
    () => api.getDriverCareer(code) as Promise<CareerData>,
    [code]
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Driver Career</h1>
      </header>
      <div className="card max-w-lg p-6">
        <StateWrapper state={state}>
          {(data) => <DriverCareerStats data={data} />}
        </StateWrapper>
      </div>
    </div>
  );
}
