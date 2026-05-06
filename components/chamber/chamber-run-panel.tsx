"use client";

import type { ChamberRun, ChamberRunSummary } from "@/types";

import { LegalSourceList } from "@/components/common/legal-source-list";
import { StatusBadge } from "@/components/common/status-badge";
import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";

function labelTaskType(taskType: string) {
  return taskType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function isFullRun(run: ChamberRun | ChamberRunSummary): run is ChamberRun {
  return "steps" in run;
}

export function ChamberRunPanel({
  run,
  showSteps = true,
}: {
  run: ChamberRun | ChamberRunSummary;
  showSteps?: boolean;
}) {
  const linkedItems = [
    run.finalArtifactId ? `Artifact ${run.finalArtifactId}` : null,
    run.linkedDraftId ? `Draft ${run.linkedDraftId}` : null,
    run.linkedResearchEntryId ? `Research ${run.linkedResearchEntryId}` : null,
  ].filter((item): item is string => Boolean(item));

  return (
    <Card className="space-y-5 rounded-[28px]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
            {labelTaskType(run.taskType)} / {run.selectedWorkflow}
          </p>
          <h3 className="text-lg font-semibold tracking-tight text-foreground">
            {run.userInstruction}
          </h3>
          <p className="text-sm leading-6 text-muted-foreground">
            Started {formatDateTime(run.startedAt)}
            {run.completedAt ? ` / Completed ${formatDateTime(run.completedAt)}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {run.confidenceScore !== null ? (
            <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {Math.round(run.confidenceScore * 100)}% confidence
            </span>
          ) : null}
          <StatusBadge status={run.status} />
        </div>
      </div>

      <div className="rounded-[24px] border border-line bg-white/[0.03] p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
          Final reviewed summary
        </p>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          {run.finalSummary}
        </p>
      </div>

      {run.criticSummary ? (
        <div className="rounded-[24px] border border-line bg-panel-highlight p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
            Critic review
          </p>
          <p className="mt-3 text-sm leading-7 text-foreground/88">
            {run.criticSummary}
          </p>
        </div>
      ) : null}

      <div className="rounded-[24px] border border-line bg-panel-highlight p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
              Legal grounding
            </p>
            <p className="mt-2 text-sm leading-6 text-foreground/88">
              {run.groundingStatus}
            </p>
            <p className="mt-1 text-xs uppercase tracking-[0.16em] text-subtle">
              Retrieval mode: {run.retrievalMode}
            </p>
          </div>
          {run.legalSourceCount ? (
            <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {run.legalSourceCount} source{run.legalSourceCount === 1 ? "" : "s"}
            </span>
          ) : null}
        </div>
        {run.legalRetrievalQuery ? (
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Retrieval query: {run.legalRetrievalQuery}
          </p>
        ) : null}
        {"weights" in run.retrievalDiagnostics ? (
          <p className="mt-2 text-xs uppercase tracking-[0.16em] text-subtle">
            Fusion weights:{" "}
            {Object.entries((run.retrievalDiagnostics.weights as Record<string, unknown>) ?? {})
              .map(([key, value]) => `${key} ${value}`)
              .join(" / ")}
          </p>
        ) : null}
        <div className="mt-4">
          <LegalSourceList
            compact
            sources={run.legalSources}
            emptyMessage="This run did not attach a retrieved Pakistani legal source."
          />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
            Participating agents
          </p>
          <div className="flex flex-wrap gap-2">
            {run.agentNames.map((agentName) => (
              <span
                key={`${run.id}-${agentName}`}
                className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
              >
                {agentName}
              </span>
            ))}
          </div>
          {linkedItems.length ? (
            <div className="flex flex-wrap gap-2">
              {linkedItems.map((item) => (
                <span
                  key={`${run.id}-${item}`}
                  className="rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-accent"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="rounded-[24px] border border-line bg-white/[0.03] p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
            Memory provenance
          </p>
          <div className="mt-3 space-y-3">
            {run.memorySources.length ? (
              run.memorySources.slice(0, 4).map((source) => (
                <div key={`${run.id}-${source.sourceId}`} className="space-y-1">
                  <p className="text-sm font-medium text-foreground">
                    {source.title}
                  </p>
                  <p className="text-xs uppercase tracking-[0.16em] text-subtle">
                    {source.sourceType}
                    {source.detail ? ` / ${source.detail}` : ""}
                  </p>
                  {source.excerpt ? (
                    <p className="text-sm leading-6 text-muted-foreground">
                      {source.excerpt}
                    </p>
                  ) : null}
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-muted-foreground">
                No stored matter memory was attached to this run.
              </p>
            )}
          </div>
        </div>
      </div>

      {isFullRun(run) ? (
        <>
          <div className="rounded-[24px] border border-line bg-white/[0.03] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
              Final reviewed output
            </p>
            <p className="mt-3 whitespace-pre-line text-sm leading-7 text-muted-foreground">
              {run.finalOutput}
            </p>
          </div>

          {showSteps && run.steps.length ? (
            <div className="space-y-3">
              {run.steps.map((step) => (
                <details
                  key={step.id}
                  className="rounded-[24px] border border-line bg-white/[0.03] p-4"
                >
                  <summary className="flex cursor-pointer list-none items-start justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                        Step {step.stepOrder}
                      </p>
                      <h4 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                        {step.agentName}
                      </h4>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {step.taskLabel}
                      </p>
                    </div>
                    <StatusBadge status={step.status} />
                  </summary>
                  <div className="mt-4 space-y-4">
                    {step.inputSummary ? (
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          Input summary
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {step.inputSummary}
                        </p>
                      </div>
                    ) : null}

                    <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                        Output summary
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground/88">
                        {step.outputSummary}
                      </p>
                      {typeof step.metadataJson.legalGroundingStatus === "string" ? (
                        <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                          Grounding status: {String(step.metadataJson.legalGroundingStatus)}
                        </p>
                      ) : null}
                      {Array.isArray(step.metadataJson.groundingSourceIds) ? (
                        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-subtle">
                          Retrieved sources in context: {step.metadataJson.groundingSourceIds.length}
                        </p>
                      ) : null}
                    </div>

                    <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                        Full step output
                      </p>
                      <p className="mt-2 whitespace-pre-line text-sm leading-6 text-foreground/88">
                        {step.fullOutput}
                      </p>
                    </div>
                  </div>
                </details>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}
