"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { ChamberRunPanel } from "@/components/chamber/chamber-run-panel";
import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { RightPanel } from "@/components/common/right-panel";
import { SectionCard } from "@/components/common/section-card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  createCaseRun,
  getCasePredictions,
  getCaseQualitySummary,
  getCaseRuns,
  getRun,
  getRunQuality,
} from "@/lib/api/client";
import type {
  CaseQualitySummary,
  CaseMatter,
  CasePrediction,
  ChamberRun,
  ChamberRunQuality,
  ChamberRunSummary,
  ChamberTaskType,
} from "@/types";
import { formatDateTime } from "@/lib/utils";
import { CommandComposer } from "@/components/workspace/command-composer";

const suggestedPrompts = [
  "Draft preliminary objections in this matter",
  "Summarize the factual controversy",
  "Identify maintainability issues",
  "Prepare hearing notes for the next listing",
  "Generate a research memo on the core issue",
];

const taskTypeOptions: Array<{ value: ChamberTaskType; label: string }> = [
  { value: "summary", label: "Matter summary" },
  { value: "issue_spotting", label: "Issue spotting" },
  { value: "preliminary_objections", label: "Preliminary objections" },
  { value: "hearing_notes", label: "Hearing notes" },
  { value: "draft_outline", label: "Draft outline" },
  { value: "draft_review", label: "Draft review" },
  { value: "research_memo", label: "Research memo" },
  { value: "procedural_check", label: "Procedural check" },
];

function inferTaskType(prompt: string): ChamberTaskType | undefined {
  const lowered = prompt.toLowerCase();
  if (lowered.includes("objection") || lowered.includes("maintainability")) {
    return "preliminary_objections";
  }
  if (lowered.includes("hearing") || lowered.includes("bench")) {
    return "hearing_notes";
  }
  if (lowered.includes("review draft") || lowered.includes("review the draft")) {
    return "draft_review";
  }
  if (
    lowered.includes("research") ||
    lowered.includes("authority") ||
    lowered.includes("precedent")
  ) {
    return "research_memo";
  }
  if (lowered.includes("procedural") || lowered.includes("deadline")) {
    return "procedural_check";
  }
  if (lowered.includes("issue") || lowered.includes("risk")) {
    return "issue_spotting";
  }
  if (
    lowered.includes("draft") ||
    lowered.includes("petition") ||
    lowered.includes("reply") ||
    lowered.includes("memo")
  ) {
    return "draft_outline";
  }
  return "summary";
}

export function CommandWorkspace({
  cases,
  initialCaseId = null,
}: {
  cases: CaseMatter[];
  initialCaseId?: string | null;
}) {
  const [selectedCaseId, setSelectedCaseId] = useState<string>(
    initialCaseId ?? cases[0]?.id ?? "",
  );
  const [instruction, setInstruction] = useState("");
  const [taskType, setTaskType] = useState<ChamberTaskType | "">("");
  const [loading, setLoading] = useState(false);
  const [runsLoading, setRunsLoading] = useState(Boolean(selectedCaseId));
  const [runDetailLoading, setRunDetailLoading] = useState(false);
  const [runSummaries, setRunSummaries] = useState<ChamberRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<ChamberRun | null>(null);
  const [predictions, setPredictions] = useState<CasePrediction[]>([]);
  const [caseQuality, setCaseQuality] = useState<CaseQualitySummary | null>(null);
  const [selectedRunQuality, setSelectedRunQuality] = useState<ChamberRunQuality | null>(null);
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

    void getCaseRuns(selectedCaseId)
      .then((runs) => {
        if (cancelled) {
          return;
        }
        setRunSummaries(runs);
        setSelectedRunId((current) => {
          const nextRunId = current ?? runs[0]?.id ?? null;
          if (!current && nextRunId) {
            setRunDetailLoading(true);
          }
          return nextRunId;
        });
        if (!runs.length) {
          setSelectedRun(null);
        }
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        setRunSummaries([]);
        setSelectedRun(null);
        setSelectedRunId(null);
        setFeedback({
          tone: "error",
          message:
            error instanceof Error
              ? error.message
              : "Unable to load chamber runs for the selected matter.",
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
          setRunDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedCaseId) {
      return;
    }

    let cancelled = false;

    void getCasePredictions(selectedCaseId)
      .then((items) => {
        if (!cancelled) {
          setPredictions(items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPredictions([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCaseId]);

  useEffect(() => {
    if (!selectedCaseId) {
      return;
    }

    let cancelled = false;

    void getCaseQualitySummary(selectedCaseId)
      .then((summary) => {
        if (!cancelled) {
          setCaseQuality(summary);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCaseQuality(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCaseId, runSummaries.length]);

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }

    let cancelled = false;

    void getRunQuality(selectedRunId)
      .then((quality) => {
        if (!cancelled) {
          setSelectedRunQuality(quality);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSelectedRunQuality(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  const rightPanelSections = useMemo(
    () => [
      {
        title: "Selected matter",
        items: selectedCase
          ? [
              {
                id: selectedCase.id,
                label: selectedCase.title,
                value: selectedCase.status,
                detail: `${selectedCase.caseNumber} / ${selectedCase.forum}`,
              },
            ]
          : [
              {
                id: "no-case",
                label: "No matter selected",
                value: "Idle",
              },
            ],
      },
      {
        title: "Recent runs",
        items: runSummaries.length
          ? runSummaries.slice(0, 4).map((run) => ({
              id: run.id,
              label: run.userInstruction,
              value: run.status,
              detail: formatDateTime(run.startedAt),
            }))
          : [
              {
                id: "no-runs",
                label: runsLoading
                  ? "Loading chamber runs..."
                  : "No chamber runs recorded for this matter yet",
                value: runsLoading ? "Loading" : "Ready",
              },
            ],
      },
      {
        title: "Selected run posture",
        items: selectedRun
          ? [
              {
                id: selectedRun.id,
                label: selectedRun.selectedWorkflow,
                value: selectedRun.status,
                detail: selectedRun.criticSummary || selectedRun.finalSummary,
              },
            ]
          : [
              {
                id: "no-active-run",
                label: "No run selected",
                value: runDetailLoading ? "Loading" : "Idle",
              },
            ],
      },
      {
        title: "Quality posture",
        items: caseQuality
          ? [
              {
                id: `${caseQuality.caseId}-quality`,
                label: `Grounded runs ${caseQuality.groundedRunCount}/${caseQuality.recentRunCount}`,
                value:
                  caseQuality.latestRunQuality?.groundingStrength?.toUpperCase() ?? "NO RUNS",
                detail:
                  caseQuality.qualityWarnings[0] ??
                  "Recent chamber runs remain grounded and critic-reviewed.",
                tone:
                  caseQuality.criticalWarningCount > 0 ? ("warning" as const) : ("success" as const),
              },
            ]
          : [
              {
                id: "quality-empty",
                label: "No case quality summary yet",
                value: "Idle",
              },
            ],
      },
    ],
    [caseQuality, runDetailLoading, runSummaries, runsLoading, selectedCase, selectedRun],
  );

  async function handleSubmit() {
    const nextInstruction = instruction.trim();
    if (!nextInstruction || !selectedCase) {
      return;
    }

    setLoading(true);
    setFeedback({
      tone: "info",
      message: "Running coordinated chamber workflow against the selected matter...",
    });

    try {
      const run = await createCaseRun(selectedCase.id, {
        instruction: nextInstruction,
        taskType: taskType || inferTaskType(nextInstruction),
      });

      setRunSummaries((current) => [
        run,
        ...current.filter((item) => item.id !== run.id),
      ]);
      setSelectedRun(run);
      setSelectedRunId(run.id);
      setInstruction("");
      setSelectedRunQuality(null);
      setFeedback({
        tone: "success",
        message:
          "Chamber workflow completed. The full run trace, critic review, and final output were stored against the selected matter.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to start the chamber workflow.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Workspace"
          title="Chamber orchestration console"
          description="Issue a higher-level legal instruction, route it through the chamber workflow, and inspect the stored run trace with critic-reviewed output."
          meta={[
            "Manager-led routing",
            "Case memory foundation",
            "Stored step-by-step run traces",
          ]}
        actions={
          selectedCase ? (
              <Link
                href={`/cases/${selectedCase.id}`}
                className={buttonVariants({ variant: "secondary" })}
              >
                Open current matter context
              </Link>
            ) : (
              <Button disabled variant="secondary">
                Select a matter first
              </Button>
            )
          }
        />

        {feedback ? (
          <InlineFeedback message={feedback.message} tone={feedback.tone} />
        ) : null}

        <Card className="space-y-5 rounded-[30px]">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px_260px]">
            <label className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                Chamber target matter
              </span>
              <select
                className="h-11 w-full rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50"
                value={selectedCaseId}
                onChange={(event) => {
                  const nextCaseId = event.target.value;
                  setRunsLoading(Boolean(nextCaseId));
                  setRunDetailLoading(false);
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
            </label>

            <label className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                Task type
              </span>
              <select
                className="h-11 w-full rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50"
                value={taskType}
                onChange={(event) =>
                  setTaskType((event.target.value as ChamberTaskType | "") ?? "")
                }
              >
                <option value="">Auto detect from instruction</option>
                {taskTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="rounded-[22px] border border-line bg-panel-highlight p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                Matter posture
              </p>
              <p className="mt-2 text-sm font-medium text-foreground">
                {selectedCase ? selectedCase.stage : "Select a matter"}
              </p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {selectedCase?.summary ??
                  "Choose a matter to run coordinated chamber workflows."}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((suggestion) => (
              <button
                key={suggestion}
                className="rounded-full border border-line px-3 py-1.5 text-xs uppercase tracking-[0.16em] text-muted-foreground transition-colors hover:border-accent/40 hover:text-foreground"
                onClick={() => {
                  setInstruction(suggestion);
                  setTaskType(inferTaskType(suggestion) ?? "");
                }}
                type="button"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </Card>

        <CommandComposer
          value={instruction}
          onChange={setInstruction}
          onSubmit={handleSubmit}
          loading={loading}
        />

        <SectionCard
          title="Predictive assistance"
          description="Latest stored Phase 7 model outputs for the selected matter."
        >
          {predictions.length ? (
            <div className="grid gap-4 xl:grid-cols-2">
              {predictions.slice(0, 4).map((prediction) => (
                <Card
                  key={prediction.id}
                  className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                        {prediction.taskName.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-sm font-medium text-foreground">
                        {prediction.predictedLabel}
                      </p>
                    </div>
                    <span className="rounded-full border border-line px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                      {(prediction.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    {prediction.modelFamily} · {prediction.modelName}
                  </p>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No predictions stored"
              description="Train models in the prediction engine lab and run predictions on the case workspace."
            />
          )}
        </SectionCard>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <SectionCard
            title="Selected chamber run"
            description="Full stored workflow trace, including case memory provenance, specialist agent steps, and critic-reviewed output."
          >
            {selectedRun ? (
              <ChamberRunPanel run={selectedRun} />
            ) : runDetailLoading ? (
              <EmptyState
                title="Loading chamber run"
                description="Fetching the full run trace and final reviewed output."
              />
            ) : (
              <EmptyState
                title="No chamber run selected"
                description="Start a new coordinated workflow or open one of the stored runs for this matter."
              />
            )}
          </SectionCard>

          <div className="space-y-6">
            <SectionCard
              title="Recent chamber runs"
              description="Stored orchestrated runs attached to the selected matter."
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
                        setRunDetailLoading(true);
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
                        <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                          {run.status}
                        </span>
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
                  description="Run the first coordinated chamber workflow to start building a matter-level trace."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Chamber posture"
              description="What the selected run used and what it produced."
            >
              {selectedRun ? (
                <div className="space-y-3">
                  <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      Agents used
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground/88">
                      {selectedRun.agentNames.join(" / ")}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      Memory sources
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground/88">
                      {selectedRun.memorySources.length}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      Critic position
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground/88">
                      {selectedRun.criticSummary || selectedRun.finalSummary}
                    </p>
                  </div>
                  {selectedRunQuality ? (
                    <>
                      <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          Retrieval mode / grounding
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {selectedRunQuality.retrievalMode} / {selectedRunQuality.groundingStrength}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {selectedRunQuality.sourceCountRetrieved} sources retrieved / {selectedRunQuality.sourceCountReliedOn} relied on
                        </p>
                      </div>
                      <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          Critic flags / unsupported claims
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {selectedRunQuality.criticFlags[0] ?? "No major critic flag recorded."}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {selectedRunQuality.unsupportedClaimWarnings[0] ??
                            "No unsupported-claim warning was surfaced for the selected run."}
                        </p>
                      </div>
                    </>
                  ) : null}
                </div>
              ) : (
                <EmptyState
                  title="No run posture yet"
                  description="Select a stored run to inspect its workflow posture and critic review."
                />
              )}
            </SectionCard>
          </div>
        </div>
      </div>

      <RightPanel
        title="Chamber intelligence"
        description="Matter context, stored run history, and the posture of the currently selected workflow."
        sections={rightPanelSections}
      />
    </div>
  );
}
