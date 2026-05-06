"use client";

import { useMemo, useState } from "react";
import { Download, FileCheck2, ShieldCheck, UploadCloud } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  buildTier1Datasets,
  exportTier1TrainingBundle,
  getTier1AuditLabels,
  getTier1Documents,
  getTier1Readiness,
  getTier1Report,
  importTier1HuggingFace,
  importTier1Kaggle,
  importTier1Local,
  updateTier1Label,
} from "@/lib/api/client";
import type {
  MlTaskName,
  Tier1Document,
  Tier1ExportResult,
  Tier1ImportResult,
  Tier1Label,
  Tier1Readiness,
  Tier1Report,
} from "@/types";

const tasks: Array<{ value: MlTaskName; label: string; options: string[] }> = [
  {
    value: "case_outcome",
    label: "Outcome",
    options: ["allowed", "dismissed", "partly_allowed", "remanded", "disposed", "withdrawn", "unknown"],
  },
  {
    value: "maintainability",
    label: "Maintainability",
    options: ["likely_maintainable", "objection_prone", "not_maintainable", "uncertain"],
  },
  {
    value: "risk_scoring",
    label: "Risk",
    options: ["low", "medium", "high"],
  },
  {
    value: "case_type",
    label: "Case type",
    options: ["civil", "criminal", "constitutional", "revenue", "customs", "service", "property", "family", "tax", "commercial", "unknown"],
  },
];

function countBy<T>(rows: T[], getKey: (row: T) => string) {
  return rows.reduce<Record<string, number>>((accumulator, row) => {
    const key = getKey(row) || "Unknown";
    accumulator[key] = (accumulator[key] ?? 0) + 1;
    return accumulator;
  }, {});
}

function CountList({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts);
  if (!entries.length) {
    return <p className="text-sm text-muted-foreground">No records yet.</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([key, value]) => (
        <span key={key} className="rounded-full border border-line px-3 py-1 text-xs text-muted-foreground">
          {key}: {value}
        </span>
      ))}
    </div>
  );
}

interface DataWorkspaceProps {
  documents: Tier1Document[];
  auditLabels: Tier1Label[];
  readiness: Tier1Readiness[];
  report: Tier1Report | null;
}

export function DataWorkspace({
  documents,
  auditLabels,
  readiness,
  report,
}: DataWorkspaceProps) {
  const [documentsState, setDocumentsState] = useState(documents);
  const [labelsState, setLabelsState] = useState(auditLabels);
  const [readinessState, setReadinessState] = useState(readiness);
  const [reportState, setReportState] = useState(report);
  const [taskFilter, setTaskFilter] = useState<MlTaskName | "all">("all");
  const [labelEdits, setLabelEdits] = useState<Record<string, string>>({});
  const [reviewerNotes, setReviewerNotes] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ tone: "success" | "error" | "info"; message: string } | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<Tier1ExportResult | null>(null);

  const sourceCounts = useMemo(() => countBy(documentsState, (item) => item.sourceType), [documentsState]);
  const languageCounts = useMemo(() => countBy(documentsState, (item) => item.language), [documentsState]);
  const visibleLabels = taskFilter === "all" ? labelsState : labelsState.filter((label) => label.taskName === taskFilter);

  async function refresh() {
    const [nextDocuments, nextLabels, nextReadiness, nextReport] = await Promise.all([
      getTier1Documents(),
      getTier1AuditLabels(taskFilter === "all" ? undefined : taskFilter),
      getTier1Readiness(),
      getTier1Report().catch(() => null),
    ]);
    setDocumentsState(nextDocuments);
    setLabelsState(nextLabels);
    setReadinessState(nextReadiness);
    setReportState(nextReport);
  }

  async function runImport(kind: "local" | "kaggle" | "huggingface") {
    setBusyAction(kind);
    setFeedback({ tone: "info", message: `Running ${kind} import. No model training will start.` });
    try {
      const result: Tier1ImportResult =
        kind === "local"
          ? await importTier1Local()
          : kind === "kaggle"
            ? await importTier1Kaggle()
            : await importTier1HuggingFace();
      await refresh();
      setFeedback({
        tone: result.status === "success" ? "success" : "info",
        message: `${result.message} Imported ${result.importedCount}, updated ${result.updatedCount}, labels ${result.labelCount}. ${result.warnings[0] ?? ""}`,
      });
    } catch (error) {
      setFeedback({ tone: "error", message: error instanceof Error ? error.message : "Import failed." });
    } finally {
      setBusyAction(null);
    }
  }

  async function approveLabel(label: Tier1Label) {
    setBusyAction(label.id);
    try {
      await updateTier1Label(label.id, {
        label: labelEdits[label.id] ?? label.label,
        reviewed: true,
        needsReview: false,
        reviewerNote: reviewerNotes[label.id] ?? "Approved from Tier 1 audit UI.",
      });
      await refresh();
      setFeedback({ tone: "success", message: "Label reviewed and saved." });
    } catch (error) {
      setFeedback({ tone: "error", message: error instanceof Error ? error.message : "Unable to update label." });
    } finally {
      setBusyAction(null);
    }
  }

  async function buildDatasets() {
    setBusyAction("build-datasets");
    try {
      const result = await buildTier1Datasets();
      await refresh();
      setFeedback({ tone: "success", message: `${result.message} ${result.warnings[0] ?? ""}` });
    } catch (error) {
      setFeedback({ tone: "error", message: error instanceof Error ? error.message : "Unable to build Tier 1 datasets." });
    } finally {
      setBusyAction(null);
    }
  }

  async function exportBundle() {
    setBusyAction("export-bundle");
    try {
      const result = await exportTier1TrainingBundle();
      setExportResult(result);
      setFeedback({ tone: "success", message: `${result.message} Bundle: ${result.zipPath}` });
    } catch (error) {
      setFeedback({ tone: "error", message: error instanceof Error ? error.message : "Unable to export training bundle." });
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Tier 1 data"
        title="Training data preparation"
        description="Import real legal datasets, audit weak labels, build trainable task datasets, and export a clean training bundle. This page never starts final model training."
        meta={["Credentials stay env-only", "Manual training only", "Weak labels must be audited"]}
      />

      {feedback ? <InlineFeedback tone={feedback.tone} message={feedback.message} /> : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="space-y-4">
          <UploadCloud className="size-5 text-accent" />
          <h2 className="text-lg font-semibold">Import sources</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Local import works without credentials. Kaggle and Hugging Face return warnings until env vars are configured.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => void runImport("local")} disabled={busyAction !== null}>
              Import local folder
            </Button>
            <Button onClick={() => void runImport("kaggle")} disabled={busyAction !== null} variant="outline">
              Import Kaggle
            </Button>
            <Button onClick={() => void runImport("huggingface")} disabled={busyAction !== null} variant="outline">
              Import Hugging Face
            </Button>
          </div>
        </Card>

        <Card className="space-y-4">
          <FileCheck2 className="size-5 text-accent" />
          <h2 className="text-lg font-semibold">Documents</h2>
          <p className="text-3xl font-semibold tracking-tight">{documentsState.length}</p>
          <CountList counts={sourceCounts} />
          <CountList counts={languageCounts} />
        </Card>

        <Card className="space-y-4">
          <ShieldCheck className="size-5 text-accent" />
          <h2 className="text-lg font-semibold">Readiness posture</h2>
          <p className="text-sm text-muted-foreground">
            {reportState
              ? `${reportState.labelCount} labels / ${reportState.reviewCounts.needsReview ?? 0} need review`
              : "No Tier 1 report yet."}
          </p>
          <Button onClick={() => void buildDatasets()} disabled={busyAction !== null} variant="secondary">
            Build Tier 1 datasets
          </Button>
        </Card>
      </div>

      <Card className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Label audit</h2>
            <p className="text-sm text-muted-foreground">Review weak labels before serious training.</p>
          </div>
          <select
            className="rounded-2xl border border-line bg-panel px-3 py-2 text-sm text-foreground"
            value={taskFilter}
            onChange={(event) => {
              const next = event.target.value as MlTaskName | "all";
              setTaskFilter(next);
              void getTier1AuditLabels(next === "all" ? undefined : next).then(setLabelsState);
            }}
          >
            <option value="all">All tasks</option>
            {tasks.map((task) => (
              <option key={task.value} value={task.value}>
                {task.label}
              </option>
            ))}
          </select>
        </div>
        {visibleLabels.length ? (
          <div className="space-y-3">
            {visibleLabels.slice(0, 12).map((label) => {
              const task = tasks.find((item) => item.value === label.taskName);
              return (
                <div key={label.id} className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-foreground">{label.documentTitle}</p>
                      <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                        {label.taskName} / {label.ruleName} / confidence {Math.round(label.confidenceScore * 100)}%
                      </p>
                      <p className="max-w-4xl text-sm leading-6 text-muted-foreground">{label.evidenceText}</p>
                    </div>
                    <StatusBadge status={label.needsReview ? "Needs Review" : "Ready"} />
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-[220px_1fr_auto]">
                    <select
                      className="rounded-2xl border border-line bg-panel px-3 py-2 text-sm text-foreground"
                      value={labelEdits[label.id] ?? label.label}
                      onChange={(event) => setLabelEdits((current) => ({ ...current, [label.id]: event.target.value }))}
                    >
                      {(task?.options ?? [label.label]).map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                    <input
                      className="rounded-2xl border border-line bg-panel px-3 py-2 text-sm text-foreground"
                      placeholder="Reviewer note"
                      value={reviewerNotes[label.id] ?? ""}
                      onChange={(event) => setReviewerNotes((current) => ({ ...current, [label.id]: event.target.value }))}
                    />
                    <Button onClick={() => void approveLabel(label)} disabled={busyAction === label.id}>
                      Approve
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState title="No labels waiting for review" description="Import data or switch filters to inspect another task." />
        )}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="text-xl font-semibold tracking-tight">Dataset readiness</h2>
          {readinessState.length ? (
            <div className="space-y-3">
              {readinessState.map((item) => (
                <div key={item.taskName} className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-foreground">{item.taskName.replaceAll("_", " ")}</p>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {item.usableLabels} usable / {item.reviewedLabels} reviewed / {item.weakLabels} weak
                  </p>
                  <CountList counts={item.classDistribution} />
                  {item.warnings[0] ? <p className="mt-2 text-sm text-amber-100">{item.warnings[0]}</p> : null}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No readiness report yet" description="Import documents and build Tier 1 datasets first." />
          )}
        </Card>

        <Card className="space-y-4">
          <Download className="size-5 text-accent" />
          <h2 className="text-xl font-semibold tracking-tight">Training export</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Exports JSONL splits, metadata reports, and a zip bundle. It does not train models or include secrets.
          </p>
          <Button onClick={() => void exportBundle()} disabled={busyAction !== null}>
            Export training bundle
          </Button>
          {exportResult ? (
            <div className="rounded-2xl border border-line bg-white/[0.03] p-4 text-sm text-muted-foreground">
              <p>Directory: {exportResult.exportDir}</p>
              <p>Zip: {exportResult.zipPath}</p>
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
