import type { WorkspaceAgentResponse } from "@/types";

import { Card } from "@/components/ui/card";

const toneClassMap: Record<WorkspaceAgentResponse["tone"], string> = {
  analysis: "border-sky-400/20 bg-sky-400/6",
  draft: "border-accent/20 bg-accent/6",
  critical: "border-rose-400/20 bg-rose-400/6",
  procedure: "border-emerald-400/20 bg-emerald-400/6",
};

export function AgentResponseCard({
  output,
}: {
  output: WorkspaceAgentResponse;
}) {
  return (
    <Card className={`space-y-4 rounded-[26px] ${toneClassMap[output.tone]}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
            {output.agent} / {output.role}
          </p>
          <h3 className="text-lg font-semibold tracking-tight text-foreground">
            {output.title}
          </h3>
        </div>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{output.summary}</p>
      <div className="space-y-2">
        {output.bullets.map((bullet) => (
          <div
            key={bullet}
            className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm leading-6 text-foreground/88"
          >
            {bullet}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {output.citations.map((citation) => (
          <span
            key={citation}
            className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            {citation}
          </span>
        ))}
      </div>
    </Card>
  );
}
