import { Clock3, Settings2, Sparkles, Play } from "lucide-react";

import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { AgentDefinition } from "@/types";

interface AgentCardProps {
  agent: AgentDefinition;
  onRun: (id: string) => void;
  onViewOutput: (id: string) => void;
  runDisabled?: boolean;
  runLabel?: string;
  viewDisabled?: boolean;
  viewLabel?: string;
  configureDisabled?: boolean;
  configureLabel?: string;
}

export function AgentCard({
  agent,
  onRun,
  onViewOutput,
  runDisabled = false,
  runLabel = "Run",
  viewDisabled = false,
  viewLabel = "View Output",
  configureDisabled = true,
  configureLabel = "Configure · Coming soon",
}: AgentCardProps) {
  return (
    <Card className="space-y-5 rounded-[28px]">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
            <Sparkles className="size-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold tracking-tight text-foreground">
              {agent.name}
            </h3>
            <p className="text-sm text-muted-foreground">{agent.role}</p>
          </div>
        </div>
        <StatusBadge status={agent.status} />
      </div>

      <p className="text-sm leading-6 text-muted-foreground">{agent.description}</p>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-line bg-white/[0.03] p-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
            <Clock3 className="size-3.5" />
            Last run
          </div>
          <p className="mt-2 text-sm text-foreground">{agent.lastRun}</p>
        </div>
        <div className="rounded-2xl border border-line bg-white/[0.03] p-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
            <Sparkles className="size-3.5" />
            Confidence
          </div>
          <p className="mt-2 text-sm text-foreground">{agent.confidence}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {agent.specialties.map((specialty) => (
          <span
            key={specialty}
            className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            {specialty}
          </span>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Button
          className="w-full"
          disabled={runDisabled}
          onClick={() => onRun(agent.id)}
          size="sm"
        >
          <Play className="size-4" />
          {runLabel}
        </Button>
        <Button
          className="w-full"
          disabled={viewDisabled}
          onClick={() => onViewOutput(agent.id)}
          size="sm"
          variant="secondary"
        >
          {viewLabel}
        </Button>
        <Button
          className="w-full"
          disabled={configureDisabled}
          size="sm"
          variant="outline"
        >
          <Settings2 className="size-4" />
          {configureLabel}
        </Button>
      </div>
    </Card>
  );
}
