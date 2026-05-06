import type { WorkflowStep } from "@/types";

export function AgentWorkflow({ steps }: { steps: WorkflowStep[] }) {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={step.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="flex size-10 items-center justify-center rounded-2xl border border-accent/30 bg-accent/10 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
              {index + 1}
            </div>
            {index < steps.length - 1 ? (
              <div className="mt-2 h-full w-px bg-line" />
            ) : null}
          </div>
          <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
            <p className="text-sm font-medium text-foreground">{step.title}</p>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {step.detail}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
