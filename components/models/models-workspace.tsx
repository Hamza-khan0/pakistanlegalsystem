"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BrainCircuit,
  ChartColumn,
  FlaskConical,
  Languages,
  ShieldCheck,
} from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  buildEvaluationReport,
  buildMlDatasets,
  buildModelCalibration,
  getDatasetReadiness,
  getModelCalibration,
  trainMlModel,
} from "@/lib/api/client";
import { formatDateTime } from "@/lib/utils";
import type {
  CalibrationRecord,
  DatasetReadiness,
  EvaluationReport,
  MlDataset,
  MlModel,
  MlModelFamily,
  MlTaskName,
} from "@/types";

const taskMeta: Array<{ task: MlTaskName; title: string; baseline: MlModelFamily; dnn: MlModelFamily }> = [
  {
    task: "case_outcome",
    title: "Case outcome prediction",
    baseline: "Baseline",
    dnn: "Transformer",
  },
  {
    task: "maintainability",
    title: "Maintainability prediction",
    baseline: "Baseline",
    dnn: "Hybrid MLP",
  },
  {
    task: "risk_scoring",
    title: "Risk scoring",
    baseline: "Baseline",
    dnn: "Hybrid MLP",
  },
  {
    task: "case_type",
    title: "Case type classification",
    baseline: "Baseline",
    dnn: "Transformer",
  },
];

function metricValue(model: MlModel) {
  const value = model.metricsJson.primaryMetric;
  return typeof value === "number" ? value.toFixed(3) : "0.000";
}

function languageCoverage(model: MlModel) {
  return Array.isArray(model.metadataJson.languageCoverage)
    ? model.metadataJson.languageCoverage.join(", ")
    : "Not recorded";
}

function readinessTone(status: DatasetReadiness["status"]) {
  if (status === "strong" || status === "usable_for_training") {
    return "success" as const;
  }
  if (status === "usable_for_demo") {
    return "info" as const;
  }
  return "error" as const;
}

function bestModelForFamily(models: MlModel[], family: MlModelFamily) {
  return models
    .filter((model) => model.modelFamily === family)
    .sort((left, right) => {
      const leftMetric =
        typeof left.metricsJson.primaryMetric === "number"
          ? left.metricsJson.primaryMetric
          : 0;
      const rightMetric =
        typeof right.metricsJson.primaryMetric === "number"
          ? right.metricsJson.primaryMetric
          : 0;
      return rightMetric - leftMetric;
    })[0];
}

export function ModelsWorkspace({
  datasets,
  models,
  readiness,
  reports,
}: {
  datasets: MlDataset[];
  models: MlModel[];
  readiness: DatasetReadiness[];
  reports: EvaluationReport[];
}) {
  const [datasetsState, setDatasetsState] = useState(datasets);
  const [modelsState, setModelsState] = useState(models);
  const [readinessState, setReadinessState] = useState(readiness);
  const [reportsState, setReportsState] = useState(reports);
  const [calibrationState, setCalibrationState] = useState<Record<string, CalibrationRecord>>({});
  const [building, setBuilding] = useState(false);
  const [trainingKey, setTrainingKey] = useState<string | null>(null);
  const [calibrating, setCalibrating] = useState(false);
  const [buildingReport, setBuildingReport] = useState(false);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const datasetsByTask = useMemo(() => {
    return new Map(datasetsState.map((dataset) => [dataset.taskName, dataset]));
  }, [datasetsState]);

  const readinessByTask = useMemo(() => {
    return new Map(readinessState.map((item) => [item.taskName, item]));
  }, [readinessState]);

  const modelsByTask = useMemo(() => {
    return taskMeta.reduce<Record<string, MlModel[]>>((accumulator, item) => {
      accumulator[item.task] = modelsState
        .filter((model) => model.taskName === item.task)
        .sort((left, right) => {
          const leftMetric =
            typeof left.metricsJson.primaryMetric === "number"
              ? left.metricsJson.primaryMetric
              : 0;
          const rightMetric =
            typeof right.metricsJson.primaryMetric === "number"
              ? right.metricsJson.primaryMetric
              : 0;
          return rightMetric - leftMetric;
        });
      return accumulator;
    }, {});
  }, [modelsState]);

  const latestReadyModels = useMemo(() => {
    return taskMeta
      .map((task) => modelsByTask[task.task]?.find((model) => model.status === "Ready"))
      .filter((model): model is MlModel => Boolean(model));
  }, [modelsByTask]);

  useEffect(() => {
    let cancelled = false;

    async function loadCalibrations() {
      const targets = latestReadyModels.slice(0, 6);
      if (!targets.length) {
        if (!cancelled) {
          setCalibrationState({});
        }
        return;
      }

      const entries = await Promise.all(
        targets.map(async (model) => {
          try {
            const record = await getModelCalibration(model.id);
            return [model.id, record] as const;
          } catch {
            return null;
          }
        }),
      );

      if (!cancelled) {
        setCalibrationState(
          Object.fromEntries(entries.filter((entry): entry is readonly [string, CalibrationRecord] => Boolean(entry))),
        );
      }
    }

    void loadCalibrations();

    return () => {
      cancelled = true;
    };
  }, [latestReadyModels]);

  async function handleBuildDatasets() {
    setBuilding(true);
    setFeedback({
      tone: "info",
      message:
        "Constructing supervised records from cases, documents, research, drafts, intelligence artifacts, and chamber runs...",
    });
    try {
      const nextDatasets = await buildMlDatasets();
      const nextReadiness = await getDatasetReadiness().catch(() => readinessState);
      setDatasetsState(nextDatasets);
      setReadinessState(nextReadiness);
      setFeedback({
        tone: "success",
        message: `Built ${nextDatasets.length} task datasets for the Phase 9 evaluation pipeline.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to build ML datasets.",
      });
    } finally {
      setBuilding(false);
    }
  }

  async function handleTrain(task: MlTaskName, family: MlModelFamily) {
    const dataset = datasetsByTask.get(task);
    if (!dataset) {
      setFeedback({
        tone: "error",
        message: "Build datasets before starting model training.",
      });
      return;
    }

    if (family !== "Baseline") {
      const confirmed = window.confirm(
        `${family} training can be CPU/GPU intensive and should normally be run after Tier 1 data import. Continue with this MVP training run?`,
      );
      if (!confirmed) {
        setFeedback({
          tone: "info",
          message:
            "DNN training was not started. Use lightweight baseline training locally, and reserve transformer or hybrid runs for explicit manual/cloud training.",
        });
        return;
      }
    }

    const key = `${task}:${family}`;
    setTrainingKey(key);
    setFeedback({
      tone: "info",
      message: `Training ${family} model for ${task.replaceAll("_", " ")}...`,
    });

    try {
      const model = await trainMlModel({
        datasetId: dataset.id,
        modelFamily: family,
      });
      setModelsState((current) => [model, ...current]);
      setFeedback({
        tone: model.status === "Ready" ? "success" : "error",
        message:
          model.status === "Ready"
            ? `${family} model trained with primary metric ${metricValue(model)}.`
            : `Training failed: ${model.trainingSummary}`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to train the selected model.",
      });
    } finally {
      setTrainingKey(null);
    }
  }

  async function handleRefreshCalibrations() {
    if (!latestReadyModels.length) {
      setFeedback({
        tone: "error",
        message: "Train at least one ready model before building calibration scaffolds.",
      });
      return;
    }

    setCalibrating(true);
    setFeedback({
      tone: "info",
      message: "Building calibration scaffolds and reliability diagnostics for the latest ready models...",
    });

    try {
      const records = await Promise.all(
        latestReadyModels.map((model) => buildModelCalibration(model.id)),
      );
      setCalibrationState(
        Object.fromEntries(records.map((record) => [record.modelId, record])),
      );
      setFeedback({
        tone: "success",
        message: `Calibration scaffolds refreshed for ${records.length} models.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to build model calibration scaffolds.",
      });
    } finally {
      setCalibrating(false);
    }
  }

  async function handleBuildReport() {
    setBuildingReport(true);
    setFeedback({
      tone: "info",
      message: "Building the exportable Phase 9 evaluation report for the semester-project review pack...",
    });
    try {
      const report = await buildEvaluationReport();
      setReportsState((current) => [report, ...current.filter((item) => item.id !== report.id)]);
      setFeedback({
        tone: "success",
        message: "Evaluation report generated and stored in the backend artifact registry.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to build the evaluation report.",
      });
    } finally {
      setBuildingReport(false);
    }
  }

  const readyModels = modelsState.filter((model) => model.status === "Ready").length;
  const trainingReadyTasks = readinessState.filter((item) =>
    ["usable_for_training", "strong"].includes(item.status),
  ).length;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Models"
        title="Training readiness and evaluation lab"
        description="Validate dataset quality, benchmark baseline vs DNN performance, review calibration scaffolding, and export evaluation reports before serious real-data training."
        meta={[
          `${datasetsState.length} datasets`,
          `${readyModels} trained models`,
          `${trainingReadyTasks} tasks training-ready`,
        ]}
        actions={
          <>
            <Button onClick={handleBuildDatasets} disabled={building} variant="secondary">
              {building ? "Building datasets..." : "Build datasets"}
            </Button>
            <Button onClick={handleRefreshCalibrations} disabled={calibrating} variant="outline">
              {calibrating ? "Refreshing calibration..." : "Refresh calibration"}
            </Button>
            <Button onClick={handleBuildReport} disabled={buildingReport}>
              {buildingReport ? "Building report..." : "Build report"}
            </Button>
          </>
        }
      />

      {feedback ? <InlineFeedback message={feedback.message} tone={feedback.tone} /> : null}

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          icon={FlaskConical}
          label="Task datasets"
          value={`${datasetsState.length}`}
          detail="Outcome, maintainability, risk, and case-type records available for readiness checks."
        />
        <MetricCard
          icon={ChartColumn}
          label="Ready models"
          value={`${readyModels}`}
          detail="Persisted baseline and DNN artifacts with stored metrics and diagnostics."
        />
        <MetricCard
          icon={ShieldCheck}
          label="Training-ready tasks"
          value={`${trainingReadyTasks}`}
          detail="Tasks that currently clear the readiness bar for serious training passes."
        />
        <MetricCard
          icon={Languages}
          label="Reports exported"
          value={`${reportsState.length}`}
          detail="Markdown and JSON evaluation reports available for the semester-project review story."
        />
      </div>

      <SectionCard
        title="Dataset readiness"
        description="Phase 9 checks for label quality, split health, leakage risk, class imbalance, language mix, and OCR quality before expensive training runs."
      >
        <div className="grid gap-4 xl:grid-cols-2">
          {taskMeta.map((task) => {
            const readinessItem = readinessByTask.get(task.task);
            return (
              <Card key={task.task} className="space-y-4 rounded-[24px] border-line bg-white/[0.03]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      {task.task.replaceAll("_", " ")}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                      {task.title}
                    </h3>
                  </div>
                  <StatusBadge status={readinessItem?.status ?? "not_ready"} />
                </div>

                {readinessItem ? (
                  <>
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4 text-sm text-muted-foreground">
                        <p>{readinessItem.totalExamples} examples</p>
                        <p>{readinessItem.uniqueCases} unique matters</p>
                        <p>{readinessItem.splitCounts.validation ?? 0} validation / {readinessItem.splitCounts.test ?? 0} test</p>
                      </div>
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4 text-sm text-muted-foreground">
                        <p>Readiness score: {readinessItem.score}</p>
                        <p>Class imbalance: {readinessItem.classImbalanceRatio}</p>
                        <p>Weak labels: {readinessItem.weakLabelPercentage}%</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(readinessItem.languageDistribution).map(([label, count]) => (
                        <span
                          key={`${task.task}-${label}`}
                          className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                        >
                          {label}: {count}
                        </span>
                      ))}
                    </div>
                    {readinessItem.warnings.length ? (
                      <InlineFeedback
                        tone={readinessTone(readinessItem.status)}
                        message={readinessItem.warnings[0]}
                      />
                    ) : (
                      <InlineFeedback
                        tone="success"
                        message="Dataset checks look stable enough for the next training pass."
                      />
                    )}
                    {readinessItem.recommendations.length ? (
                      <p className="text-sm leading-6 text-muted-foreground">
                        Next fix: {readinessItem.recommendations[0]}
                      </p>
                    ) : null}
                  </>
                ) : (
                  <EmptyState
                    title="No readiness report yet"
                    description="Build the dataset for this task to unlock Phase 9 readiness checks."
                  />
                )}
              </Card>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        title="Task leaderboard"
        description="Clean baseline-vs-DNN comparison with dataset context, multilingual coverage, and training-readiness posture per task."
      >
        <div className="grid gap-4 xl:grid-cols-2">
          {taskMeta.map((task) => {
            const dataset = datasetsByTask.get(task.task);
            const readinessItem = readinessByTask.get(task.task);
            const taskModels = modelsByTask[task.task] ?? [];
            const baselineBest = bestModelForFamily(taskModels, "Baseline");
            const dnnBest =
              bestModelForFamily(taskModels, "Transformer") ??
              bestModelForFamily(taskModels, "Hybrid MLP");

            return (
              <Card key={task.task} className="space-y-4 rounded-[24px] border-line bg-white/[0.03]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      {task.task.replaceAll("_", " ")}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                      {task.title}
                    </h3>
                  </div>
                  <StatusBadge status={dataset?.status ?? "Missing"} />
                </div>

                {dataset ? (
                  <div className="rounded-2xl border border-line bg-panel-highlight p-4 text-sm text-muted-foreground">
                    {dataset.recordCount} records / version {dataset.version}
                    {readinessItem ? ` / readiness ${readinessItem.status}` : ""}
                  </div>
                ) : (
                  <EmptyState
                    title="Dataset not built"
                    description="Build the supervised dataset to unlock training and evaluation for this task."
                  />
                )}

                <div className="flex flex-wrap gap-3">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => void handleTrain(task.task, task.baseline)}
                    disabled={!dataset || trainingKey === `${task.task}:${task.baseline}`}
                  >
                    {trainingKey === `${task.task}:${task.baseline}`
                      ? "Training baseline..."
                      : `Train ${task.baseline}`}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void handleTrain(task.task, task.dnn)}
                    disabled={!dataset || trainingKey === `${task.task}:${task.dnn}`}
                  >
                    {trainingKey === `${task.task}:${task.dnn}`
                      ? "Training DNN..."
                      : `Train ${task.dnn}`}
                  </Button>
                </div>

                {(baselineBest || dnnBest) && (
                  <div className="rounded-2xl border border-line bg-white/[0.03] p-4 text-sm text-muted-foreground">
                    <p>
                      Baseline best: {baselineBest ? `${baselineBest.name} (${metricValue(baselineBest)})` : "not trained"}
                    </p>
                    <p className="mt-1">
                      DNN best: {dnnBest ? `${dnnBest.name} (${metricValue(dnnBest)})` : "not trained"}
                    </p>
                  </div>
                )}

                {taskModels.length ? (
                  <div className="space-y-3">
                    {taskModels.slice(0, 4).map((model) => (
                      <div
                        key={model.id}
                        className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-medium text-foreground">{model.name}</p>
                            <p className="mt-1 text-sm leading-6 text-muted-foreground">
                              {model.modelFamily} / {formatDateTime(model.createdAt)}
                            </p>
                          </div>
                          <StatusBadge status={model.status} />
                        </div>
                        <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                          Primary metric: {metricValue(model)}
                        </p>
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">
                          Languages: {languageCoverage(model)}
                        </p>
                        {readinessItem?.warnings.length ? (
                          <p className="mt-2 text-xs uppercase tracking-[0.16em] text-amber-200">
                            Dataset warning: {readinessItem.warnings[0]}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </Card>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        title="Calibration and reports"
        description="Probability reliability scaffolding and exportable evaluation artifacts for the academic presentation layer."
      >
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-4">
            {latestReadyModels.length ? (
              latestReadyModels.map((model) => {
                const calibration = calibrationState[model.id];
                return (
                  <Card key={model.id} className="space-y-4 rounded-[24px] border-line bg-white/[0.03]">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          {model.taskName.replaceAll("_", " ")}
                        </p>
                        <h3 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                          {model.name}
                        </h3>
                      </div>
                      <StatusBadge status={model.modelFamily} />
                    </div>
                    {calibration ? (
                      <>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-2xl border border-line bg-panel-highlight p-4 text-sm text-muted-foreground">
                            <p>Samples: {calibration.sampleCount}</p>
                            <p>
                              ECE: {typeof calibration.metricsJson.expectedCalibrationError === "number"
                                ? Number(calibration.metricsJson.expectedCalibrationError).toFixed(3)
                                : "n/a"}
                            </p>
                          </div>
                          <div className="rounded-2xl border border-line bg-panel-highlight p-4 text-sm text-muted-foreground">
                            <p>
                              Brier: {typeof calibration.metricsJson.brierScore === "number"
                                ? Number(calibration.metricsJson.brierScore).toFixed(3)
                                : "n/a"}
                            </p>
                            <p>{calibration.calibrationMethod}</p>
                          </div>
                        </div>
                        <p className="text-sm leading-6 text-muted-foreground">
                          {calibration.notes}
                        </p>
                        {Array.isArray(calibration.reliabilityJson.warnings) &&
                        calibration.reliabilityJson.warnings.length ? (
                          <InlineFeedback
                            tone="info"
                            message={String(calibration.reliabilityJson.warnings[0])}
                          />
                        ) : null}
                      </>
                    ) : (
                      <EmptyState
                        title="Calibration scaffold not loaded"
                        description="Refresh calibration to generate reliability bins and confidence diagnostics."
                      />
                    )}
                  </Card>
                );
              })
            ) : (
              <EmptyState
                title="No ready models for calibration"
                description="Train at least one baseline or DNN model to populate reliability diagnostics."
              />
            )}
          </div>

          <div className="space-y-4">
            <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">Report export</p>
              <p className="text-sm leading-6 text-muted-foreground">
                Build a Markdown and JSON report that summarizes readiness, model comparisons, and retrieval benchmarking for the semester-project review pack.
              </p>
              <Button onClick={handleBuildReport} disabled={buildingReport} variant="secondary">
                {buildingReport ? "Building report..." : "Generate report"}
              </Button>
            </Card>

            <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">Recent reports</p>
              {reportsState.length ? (
                reportsState.slice(0, 5).map((report) => (
                  <div key={report.id} className="rounded-2xl border border-line bg-panel-highlight p-3">
                    <p className="text-sm font-medium text-foreground">{report.title}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      {formatDateTime(report.createdAt)}
                    </p>
                    {report.markdownPath ? (
                      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-subtle">
                        Stored at {report.markdownPath}
                      </p>
                    ) : null}
                  </div>
                ))
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  No evaluation reports have been generated yet.
                </p>
              )}
            </Card>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof BrainCircuit;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <Card className="space-y-4 rounded-[24px] border-line bg-white/[0.03]">
      <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
        <Icon className="size-5" />
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.18em] text-subtle">{label}</p>
        <h3 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">{value}</h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
      </div>
    </Card>
  );
}
