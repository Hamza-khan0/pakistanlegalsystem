"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Gauge, Orbit, ShieldAlert } from "lucide-react";

import { ChamberRunPanel } from "@/components/chamber/chamber-run-panel";
import { AgentCard } from "@/components/agents/agent-card";
import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { StatusBadge } from "@/components/common/status-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { agents as baseAgents } from "@/data/agents";
import {
  createCaseRun,
  getAgentActivity,
  getCaseRuns,
  getRun,
} from "@/lib/api/client";
import { formatDateTime } from "@/lib/utils";
import type {
  AgentActivity,
  AgentDefinition,
  CaseMatter,
  ChamberRun,
  ChamberRunSummary,
  ChamberTaskType,
} from "@/types";

const AGENT_NAME_BY_ID: Record<string, string> = {
  "manager-agent": "Manager Agent",
  "research-agent": "Research Agent",
  "drafting-agent": "Drafting Agent",
  "critic-agent": "Critic Agent",
  "procedural-agent": "Procedural Agent",
  "memory-agent": "Memory Agent",
};

function roleRunConfig(
  agentId: string,
  caseItem: CaseMatter,
): { instruction: string; taskType: ChamberTaskType } {
  if (agentId === "manager-agent") {
    return {
      instruction: `Prepare a chamber summary for ${caseItem.caseNumber} and surface the strongest next action for counsel.`,
      taskType: "summary",
    };
  }
  if (agentId === "research-agent") {
    return {
      instruction: `Generate a research memo for ${caseItem.caseNumber} focused on ${caseItem.issues[0] ?? "the core maintainability issue"}.`,
      taskType: "research_memo",
    };
  }
  if (agentId === "drafting-agent") {
    return {
      instruction: `Prepare a draft outline for ${caseItem.caseNumber} using the current issue and memory posture.`,
      taskType: "draft_outline",
    };
  }
  if (agentId === "critic-agent") {
    return {
      instruction: `Identify weaknesses, maintainability issues, and record gaps in ${caseItem.caseNumber}.`,
      taskType: "issue_spotting",
    };
  }
  if (agentId === "procedural-agent") {
    return {
      instruction: `Prepare a procedural check and hearing posture note for ${caseItem.caseNumber}.`,
      taskType: "procedural_check",
    };
  }
  return {
    instruction: `Assemble matter memory and continuity posture for ${caseItem.caseNumber} before the next chamber task.`,
    taskType: "summary",
  };
}

function mapAgentStatus(
  latestActivity: AgentActivity | undefined,
  runningAgentId: string | null,
  agentId: string,
): AgentDefinition["status"] {
  if (runningAgentId === agentId) {
    return "Running";
  }
  if (!latestActivity) {
    return "Queued";
  }
  if (latestActivity.status === "Running") {
    return "Running";
  }
  if (latestActivity.status === "Pending") {
    return "Queued";
  }
  if (latestActivity.status === "Failed") {
    return "Reviewing";
  }
  return "Ready";
}

function buildAgentCards(
  activity: AgentActivity[],
  runningAgentId: string | null,
): AgentDefinition[] {
  const latestActivityByName = new Map<string, AgentActivity>();
  activity.forEach((item) => {
    if (!latestActivityByName.has(item.agentName)) {
      latestActivityByName.set(item.agentName, item);
    }
  });

  return baseAgents.map((agent) => {
    const latestActivity = latestActivityByName.get(agent.name);
    const runCount = activity.filter((item) => item.agentName === agent.name).length;

    return {
      ...agent,
      status: mapAgentStatus(latestActivity, runningAgentId, agent.id),
      lastRun: latestActivity?.completedAt
        ? formatDateTime(latestActivity.completedAt)
        : "No stored run yet",
      queueDepth: runCount,
      confidence:
        latestActivity?.confidenceScore !== null &&
        latestActivity?.confidenceScore !== undefined
          ? `${Math.round(latestActivity.confidenceScore * 100)}%`
          : "No run yet",
    };
  });
}

export function AgentsWorkspace({
  cases,
  initialCaseId = null,
}: {
  cases: CaseMatter[];
  initialCaseId?: string | null;
}) {
  const [selectedCaseId, setSelectedCaseId] = useState(
    initialCaseId ?? cases[0]?.id ?? "",
  );
  const [runSummaries, setRunSummaries] = useState<ChamberRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<ChamberRun | null>(null);
  const [activity, setActivity] = useState<AgentActivity[]>([]);
  const [runsLoading, setRunsLoading] = useState(Boolean(selectedCaseId));
  const [detailLoading, setDetailLoading] = useState(false);
  const [runningAgentId, setRunningAgentId] = useState<string | null>(null);
  const [focusedAgentId, setFocusedAgentId] = useState<string>("manager-agent");
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const selectedCase =
    cases.find((caseItem) => caseItem.id === selectedCaseId) ?? null;

  useEffect(() => {
    if (!selectedCaseId) {
      return;
    }

    let cancelled = false;

    Promise.all([getCaseRuns(selectedCaseId), getAgentActivity(selectedCaseId)])
      .then(([runs, nextActivity]) => {
        if (cancelled) {
          return;
        }
        setRunSummaries(runs);
        setActivity(nextActivity);
        setSelectedRunId((current) => {
          const nextRunId = current ?? runs[0]?.id ?? null;
          if (!current && nextRunId) {
            setDetailLoading(true);
          }
          return nextRunId;
        });
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        setFeedback({
          tone: "error",
          message:
            error instanceof Error
              ? error.message
              : "Unable to load chamber runs and agent activity for the selected matter.",
        });
      })
      .finally(() => {
        if (!cancelled) {
          setRunsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCaseId]);

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }

    let cancelled = false;

    void getRun(selectedRunId)
      .then((run) => {
        if (!cancelled) {
          setSelectedRun(run);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setSelectedRun(null);
          setFeedback({
            tone: "error",
            message:
              error instanceof Error
                ? error.message
                : "Unable to load the selected chamber run.",
          });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  const liveAgents = useMemo(
    () => buildAgentCards(activity, runningAgentId),
    [activity, runningAgentId],
  );

  const focusedAgentName = AGENT_NAME_BY_ID[focusedAgentId];
  const focusedSteps = useMemo(() => {
    if (!selectedRun || !focusedAgentName) {
      return [];
    }
    return selectedRun.steps.filter((step) => step.agentName === focusedAgentName);
  }, [focusedAgentName, selectedRun]);

  async function handleRun(agentId: string) {
    if (!selectedCase) {
      return;
    }

    const config = roleRunConfig(agentId, selectedCase);
    setRunningAgentId(agentId);
    setFeedback({
      tone: "info",
      message: `Running ${AGENT_NAME_BY_ID[agentId]} through a coordinated chamber workflow...`,
    });

    try {
      const run = await createCaseRun(selectedCase.id, config);
      const nextActivity = await getAgentActivity(selectedCase.id);
      setActivity(nextActivity);
      setRunSummaries((current) => [
        run,
        ...current.filter((item) => item.id !== run.id),
      ]);
      setSelectedRun(run);
      setSelectedRunId(run.id);
      setFocusedAgentId(agentId);
      setFeedback({
        tone: "success",
        message:
          "Chamber workflow completed and the full run trace is now available for review.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : `Unable to run ${AGENT_NAME_BY_ID[agentId]}.`,
      });
    } finally {
      setRunningAgentId(null);
    }
  }

  function handleViewOutput(agentId: string) {
    setFocusedAgentId(agentId);
  }

  const completedRuns = runSummaries.filter((run) => run.status === "Completed").length;
  const criticRuns = runSummaries.filter((run) => run.criticSummary).length;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Agents"
        title="Chamber run inspection"
        description="Trigger chamber workflows from specialist role perspectives, inspect recent multi-agent runs, and review step-by-step agent traces with critic output."
        meta={[
          selectedCase ? selectedCase.caseNumber : "No matter selected",
          "Live run inspection",
          "Memory-aware chamber workflows",
        ]}
        actions={
          selectedCase ? (
            <Link
              href={`/workspace?caseId=${selectedCase.id}`}
              className={buttonVariants()}
            >
              Open chamber console
            </Link>
          ) : (
            <Button disabled>Open chamber console</Button>
          )
        }
      />

      {feedback ? (
        <InlineFeedback message={feedback.message} tone={feedback.tone} />
      ) : null}

      <Card className="rounded-[28px]">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
              Active matter
            </p>
            <select
              className="h-11 w-full rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50"
              value={selectedCaseId}
              onChange={(event) => {
                const nextCaseId = event.target.value;
                setRunsLoading(Boolean(nextCaseId));
                setDetailLoading(false);
                setSelectedCaseId(nextCaseId);
                setSelectedRunId(null);
                setSelectedRun(null);
              }}
            >
              {cases.map((caseItem) => (
                <option key={caseItem.id} value={caseItem.id}>
                  {caseItem.caseNumber} / {caseItem.title}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-[22px] border border-line bg-panel-highlight p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-subtle">
              Matter posture
            </p>
            <p className="mt-2 text-sm font-medium text-foreground">
              {selectedCase ? selectedCase.stage : "Select a matter"}
            </p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {selectedCase?.summary ??
                "Choose a live matter to inspect chamber runs and agent activity."}
            </p>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          icon={Orbit}
          label="Agent roles"
          value={`${liveAgents.length}`}
          detail="Specialist chamber roles available for orchestrated workflows."
        />
        <MetricCard
          icon={Gauge}
          label="Completed runs"
          value={`${completedRuns}`}
          detail="Stored orchestrated runs completed on the selected matter."
        />
        <MetricCard
          icon={ShieldAlert}
          label="Critic reviewed"
          value={`${criticRuns}`}
          detail={`${activity.length} persisted step events are available for inspection.`}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <div className="grid gap-4 xl:grid-cols-2">
            {liveAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                configureDisabled
                configureLabel="Role profile locked for a future release"
                onRun={handleRun}
                onViewOutput={handleViewOutput}
                runDisabled={runsLoading || !selectedCase}
                runLabel="Run workflow"
                viewDisabled={!selectedRun}
                viewLabel="Focus output"
              />
            ))}
          </div>

          <SectionCard
            title="Recent chamber runs"
            description="Persisted multi-agent runs for the selected matter."
          >
            {runSummaries.length ? (
              <div className="space-y-3">
                {runSummaries.map((run) => (
                  <button
                    key={run.id}
                    className={`w-full rounded-[24px] border p-4 text-left transition-colors ${
                      selectedRunId === run.id
                        ? "border-accent/40 bg-accent/8"
                        : "border-line bg-white/[0.03] hover:border-accent/25"
                    }`}
                    onClick={() => {
                      setDetailLoading(true);
                      setSelectedRunId(run.id);
                    }}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          {run.selectedWorkflow}
                        </p>
                        <p className="mt-1 text-sm font-medium text-foreground">
                          {run.userInstruction}
                        </p>
                      </div>
                      <StatusBadge status={run.status} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">
                      {run.finalSummary}
                    </p>
                    <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                      {formatDateTime(run.startedAt)}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState
                title={runsLoading ? "Loading chamber runs" : "No chamber runs stored yet"}
                description="Run a specialist workflow to create the first multi-agent trace for this matter."
              />
            )}
          </SectionCard>

          <SectionCard
            title="Recent agent activity"
            description="Latest persisted step events from chamber runs on the selected matter."
          >
            {activity.length ? (
              <div className="space-y-3">
                {activity.map((item) => (
                  <div
                    key={item.stepId}
                    className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {item.agentName}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {item.taskLabel}
                        </p>
                      </div>
                      <StatusBadge status={item.status} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-foreground/88">
                      {item.outputSummary}
                    </p>
                    <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                      {item.completedAt ? formatDateTime(item.completedAt) : "In progress"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No activity recorded yet"
                description="Run a workflow from one of the agent roles to start building step-level activity."
              />
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Selected run detail"
            description="Full run trace with memory sources, critic review, and step-by-step outputs."
          >
            {selectedRun ? (
              <ChamberRunPanel run={selectedRun} />
            ) : detailLoading ? (
              <EmptyState
                title="Loading run detail"
                description="Fetching the selected chamber run trace."
              />
            ) : (
              <EmptyState
                title="No run selected"
                description="Choose a stored run to inspect its full chamber trace."
              />
            )}
          </SectionCard>

          <SectionCard
            title="Focused agent trace"
            description={
              focusedAgentName
                ? `Step outputs from ${focusedAgentName} in the selected run.`
                : "Focus one of the chamber roles to inspect its contribution."
            }
          >
            {focusedSteps.length ? (
              <div className="space-y-3">
                {focusedSteps.map((step) => (
                  <Card
                    key={step.id}
                    className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          Step {step.stepOrder}
                        </p>
                        <h3 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                          {step.taskLabel}
                        </h3>
                      </div>
                      <StatusBadge status={step.status} />
                    </div>
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
                    <p className="text-sm leading-6 text-muted-foreground">
                      {step.outputSummary}
                    </p>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No focused step output"
                description="Select a chamber role and a run to inspect that role's stored contribution."
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Orbit;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <Card className="space-y-4 rounded-[28px]">
      <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
        <Icon className="size-5" />
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.18em] text-subtle">{label}</p>
        <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-foreground">
          {value}
        </p>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
      </div>
    </Card>
  );
}
