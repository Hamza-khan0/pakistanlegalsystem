"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { DatabaseZap, Globe2, Languages, ScanSearch } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { SearchInput } from "@/components/common/search-input";
import { SectionCard } from "@/components/common/section-card";
import { StatusBadge } from "@/components/common/status-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  buildRetrievalIndex,
  buildCorpus,
  evaluateRetrieval,
  exportCorpus,
  forceOcrCrawledDocument,
  getCorpusEntries,
  getCrawledDocuments,
  getCrawlJobs,
  getRetrievalBenchmark,
  runRetrievalBenchmark,
  hybridRetrievalSearch,
  processCrawledDocument,
  runCrawl,
  semanticRetrievalSearch,
} from "@/lib/api/client";
import { cn, formatDateTime } from "@/lib/utils";
import type {
  CorpusBuildResult,
  CorpusEntry,
  CorpusExportResult,
  CrawledDocument,
  CrawlJob,
  CrawlSource,
  EmbeddingIndexMetadata,
  RetrievalBenchmarkRun,
  RetrievalLeaderboard,
  RetrievalMode,
  RetrievalSearchResult,
} from "@/types";

export function KnowledgeWorkspace({
  sources,
  jobs,
  documents,
  corpusEntries,
  indexStatus,
  retrievalLeaderboard,
  benchmarkRuns,
  latestBenchmark,
}: {
  sources: CrawlSource[];
  jobs: CrawlJob[];
  documents: CrawledDocument[];
  corpusEntries: CorpusEntry[];
  indexStatus: EmbeddingIndexMetadata | null;
  retrievalLeaderboard: RetrievalLeaderboard;
  benchmarkRuns: RetrievalBenchmarkRun[];
  latestBenchmark: RetrievalBenchmarkRun | null;
}) {
  const [sourcesState] = useState(sources);
  const [jobsState, setJobsState] = useState(jobs);
  const [documentsState, setDocumentsState] = useState(documents);
  const [corpusState, setCorpusState] = useState(corpusEntries);
  const [selectedSourceId, setSelectedSourceId] = useState(sources[0]?.id ?? "");
  const [selectedDocumentId, setSelectedDocumentId] = useState(documents[0]?.id ?? "");
  const [search, setSearch] = useState("");
  const [runningSourceId, setRunningSourceId] = useState<string | null>(null);
  const [processingDocumentId, setProcessingDocumentId] = useState<string | null>(null);
  const [buildingCorpus, setBuildingCorpus] = useState(false);
  const [exportingCorpus, setExportingCorpus] = useState(false);
  const [buildingIndex, setBuildingIndex] = useState(false);
  const [indexState, setIndexState] = useState(indexStatus);
  const [leaderboardState, setLeaderboardState] = useState(retrievalLeaderboard);
  const [benchmarkRunsState, setBenchmarkRunsState] = useState(benchmarkRuns);
  const [selectedBenchmark, setSelectedBenchmark] = useState<RetrievalBenchmarkRun | null>(latestBenchmark);
  const [retrievalQuery, setRetrievalQuery] = useState("order vii rule 11 plaint rejection jurisdiction objections");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("Hybrid");
  const [retrievalLoading, setRetrievalLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [retrievalResult, setRetrievalResult] = useState<RetrievalSearchResult | null>(null);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const deferredSearch = useDeferredValue(search);

  const selectedSource =
    sourcesState.find((source) => source.id === selectedSourceId) ?? null;

  const filteredDocuments = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    return documentsState.filter((document) => {
      const matchesSource = !selectedSourceId || document.sourceId === selectedSourceId;
      if (!matchesSource) {
        return false;
      }
      if (!query) {
        return true;
      }
      return (
        document.title.toLowerCase().includes(query) ||
        document.documentType.toLowerCase().includes(query) ||
        document.language.toLowerCase().includes(query) ||
        document.sourceName.toLowerCase().includes(query)
      );
    });
  }, [deferredSearch, documentsState, selectedSourceId]);

  const selectedDocument =
    filteredDocuments.find((document) => document.id === selectedDocumentId) ??
    documentsState.find((document) => document.id === selectedDocumentId) ??
    null;

  const benchmarkGroups = useMemo(() => {
    if (!selectedBenchmark?.results.length) {
      return [];
    }
    const groups = new Map<string, RetrievalBenchmarkRun["results"]>();
    selectedBenchmark.results.forEach((result) => {
      const current = groups.get(result.query) ?? [];
      current.push(result);
      groups.set(result.query, current);
    });
    return Array.from(groups.entries()).map(([query, results]) => ({
      query,
      results: [...results].sort((left, right) => left.mode.localeCompare(right.mode)),
    }));
  }, [selectedBenchmark]);

  async function refreshAfterCrawl() {
    const [nextJobs, nextDocuments] = await Promise.all([
      getCrawlJobs(),
      getCrawledDocuments(),
    ]);
    setJobsState(nextJobs);
    setDocumentsState(nextDocuments);
    if (!selectedDocumentId && nextDocuments[0]) {
      setSelectedDocumentId(nextDocuments[0].id);
    }
  }

  async function handleRunCrawl(sourceId: string) {
    setRunningSourceId(sourceId);
    setFeedback({
      tone: "info",
      message: "Running the crawl pipeline and persisting discovered legal materials...",
    });

    try {
      const job = await runCrawl(sourceId);
      await refreshAfterCrawl();
      setFeedback({
        tone: job.status === "Completed" ? "success" : "error",
        message:
          job.status === "Completed"
            ? `Crawl completed. ${job.documentsSaved} new legal documents were stored for Phase 6 processing.`
            : "Crawl finished with failures. Review the latest crawl job metadata for details.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to start the crawl job.",
      });
    } finally {
      setRunningSourceId(null);
    }
  }

  async function handleProcessDocument(forceOcr = false) {
    if (!selectedDocument) {
      return;
    }

    setProcessingDocumentId(selectedDocument.id);
    setFeedback({
      tone: "info",
      message: forceOcr
        ? "Running forced OCR on the selected crawled document..."
        : "Processing the selected crawled document and extracting retrieval-ready text...",
    });

    try {
      const processed = forceOcr
        ? await forceOcrCrawledDocument(selectedDocument.id)
        : await processCrawledDocument(selectedDocument.id);
      setDocumentsState((current) =>
        current.map((document) =>
          document.id === processed.id ? processed : document,
        ),
      );
      setSelectedDocumentId(processed.id);
      setFeedback({
        tone: processed.processingStatus === "Failed" ? "error" : "success",
        message:
          processed.processingStatus === "Failed"
            ? String(processed.errorsJson.message ?? "Document processing failed.")
            : `Document processed. Language: ${processed.languageDetected}. Status: ${processed.processingStatus}.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to process the selected crawled document.",
      });
    } finally {
      setProcessingDocumentId(null);
    }
  }

  async function handleBuildCorpus() {
    setBuildingCorpus(true);
    setFeedback({
      tone: "info",
      message: "Promoting processed crawl results into the retrieval and training corpus...",
    });

    try {
      const stats: CorpusBuildResult = await buildCorpus();
      const nextCorpus = await getCorpusEntries();
      setCorpusState(nextCorpus);
      setFeedback({
        tone: "success",
        message: `Corpus built. ${stats.legalSourcesUpserted} legal sources and ${stats.corpusEntriesUpserted} corpus entries were refreshed.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to build the corpus.",
      });
    } finally {
      setBuildingCorpus(false);
    }
  }

  async function handleExportCorpus() {
    setExportingCorpus(true);
    setFeedback({
      tone: "info",
      message: "Exporting retrieval, classification, and bilingual datasets for downstream DNN work...",
    });

    try {
      const stats: CorpusExportResult = await exportCorpus();
      setFeedback({
        tone: "success",
        message: `Dataset export completed. ${stats.retrievalRecords} retrieval records were written to ${stats.outputDir}.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to export the corpus.",
      });
    } finally {
      setExportingCorpus(false);
    }
  }

  const corpusReadyCount = corpusState.filter((entry) => entry.readyForRetrieval).length;
  const bilingualCount = documentsState.filter((document) =>
    ["Urdu", "Mixed"].includes(document.languageDetected || document.language),
  ).length;

  async function handleBuildSemanticIndex() {
    setBuildingIndex(true);
    setFeedback({
      tone: "info",
      message: "Building multilingual semantic embeddings for the legal corpus...",
    });
    try {
      const nextIndex = await buildRetrievalIndex();
      const nextLeaderboard = await evaluateRetrieval();
      setIndexState(nextIndex);
      setLeaderboardState(nextLeaderboard);
      setFeedback({
        tone: "success",
        message: `Semantic index built with ${nextIndex.sourceCount} encoded source chunks using ${nextIndex.modelName}.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to build the semantic retrieval index.",
      });
    } finally {
      setBuildingIndex(false);
    }
  }

  async function handleRunBenchmark() {
    setBenchmarkLoading(true);
    setFeedback({
      tone: "info",
      message: "Running lexical, semantic, and hybrid retrieval benchmarks with the Phase 9 reranking layer...",
    });
    try {
      const benchmark = await runRetrievalBenchmark();
      setSelectedBenchmark(benchmark);
      setBenchmarkRunsState((current) => [
        benchmark,
        ...current.filter((item) => item.id !== benchmark.id),
      ]);
      setFeedback({
        tone: "success",
        message: `Retrieval benchmark completed across ${benchmark.queryCount} benchmark queries.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to run retrieval benchmarks.",
      });
    } finally {
      setBenchmarkLoading(false);
    }
  }

  async function handleRetrievalSearch() {
    if (!retrievalQuery.trim()) {
      return;
    }
    setRetrievalLoading(true);
    setFeedback({
      tone: "info",
      message: `Running ${retrievalMode.toLowerCase()} retrieval over the legal corpus...`,
    });
    try {
      const result =
        retrievalMode === "Semantic"
          ? await semanticRetrievalSearch({ query: retrievalQuery, taskType: "research_memo", limit: 6 })
          : await hybridRetrievalSearch({ query: retrievalQuery, taskType: "research_memo", limit: 6 });
      setRetrievalResult(result);
      setFeedback({
        tone: "success",
        message: result.summary,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Unable to run retrieval over the legal corpus.",
      });
    } finally {
      setRetrievalLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Knowledge"
        title="Legal corpus and OCR lab"
        description="Run configured legal-source crawls, inspect stored documents, process OCR and bilingual extraction, and build export-ready corpora for retrieval and later DNN phases."
        meta={[
          `${sourcesState.length} registered sources`,
          `${documentsState.length} crawled documents`,
          `${corpusReadyCount} retrieval-ready corpus entries`,
          indexState ? `${indexState.status} semantic index` : "Semantic index not built",
        ]}
        actions={
          <>
            <Button
              onClick={handleBuildCorpus}
              disabled={buildingCorpus}
              variant="secondary"
            >
              {buildingCorpus ? "Building corpus..." : "Build corpus"}
            </Button>
            <Button onClick={handleExportCorpus} disabled={exportingCorpus}>
              {exportingCorpus ? "Exporting..." : "Export datasets"}
            </Button>
          </>
        }
      />

      {feedback ? (
        <InlineFeedback message={feedback.message} tone={feedback.tone} />
      ) : null}

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          icon={Globe2}
          label="Registered sources"
          value={`${sourcesState.length}`}
          detail="Config-driven crawl sources ready for repeatable acquisition."
        />
        <MetricCard
          icon={ScanSearch}
          label="Crawled documents"
          value={`${documentsState.length}`}
          detail="Stored raw or processed legal documents from the crawl layer."
        />
        <MetricCard
          icon={DatabaseZap}
          label="Corpus entries"
          value={`${corpusReadyCount}`}
          detail="Retrieval-ready and training-ready records available to the chamber."
        />
        <MetricCard
          icon={Languages}
          label="Urdu / mixed"
          value={`${bilingualCount}`}
          detail="Documents with Urdu or mixed-language signals preserved for downstream tasks."
        />
      </div>

      <SectionCard
        title="Semantic retrieval"
        description="Phase 8 semantic embeddings, hybrid fusion, and reranking diagnostics for the legal corpus."
        action={
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleRunBenchmark} disabled={benchmarkLoading} variant="outline">
              {benchmarkLoading ? "Running benchmark..." : "Run benchmark"}
            </Button>
            <Button onClick={handleBuildSemanticIndex} disabled={buildingIndex} variant="secondary">
              {buildingIndex ? "Building semantic index..." : "Build semantic index"}
            </Button>
          </div>
        }
      >
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            <label className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                Retrieval experiment query
              </span>
              <SearchInput
                value={retrievalQuery}
                onChange={setRetrievalQuery}
                placeholder="Search Pakistani legal materials with semantic or hybrid retrieval"
              />
            </label>
            <div className="flex flex-wrap gap-3">
              <select
                className="h-11 rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50"
                value={retrievalMode}
                onChange={(event) => setRetrievalMode(event.target.value as RetrievalMode)}
              >
                <option value="Hybrid">Hybrid retrieval</option>
                <option value="Semantic">Semantic retrieval</option>
              </select>
              <Button onClick={handleRetrievalSearch} disabled={retrievalLoading}>
                {retrievalLoading ? "Searching..." : "Run retrieval"}
              </Button>
            </div>
            {retrievalResult ? (
              <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                  {retrievalResult.mode} / {retrievalResult.status}
                </p>
                <p className="mt-2 text-sm leading-6 text-foreground/88">
                  {retrievalResult.summary}
                </p>
                <div className="mt-4 space-y-3">
                  {retrievalResult.sources.map((source) => (
                    <div key={`${source.sourceId}-${source.chunkId ?? "source"}`} className="rounded-2xl border border-line bg-white/[0.03] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                            {source.sourceType}
                            {source.sectionLabel ? ` / ${source.sectionLabel}` : ""}
                          </p>
                          <p className="mt-1 text-sm font-medium text-foreground">
                            {source.citationLabel || source.title}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                          <span>{(source.relevanceScore ?? 0).toFixed(2)} final</span>
                          {source.lexicalScore !== null && source.lexicalScore !== undefined ? (
                            <span>lex {source.lexicalScore.toFixed(2)}</span>
                          ) : null}
                          {source.semanticScore !== null && source.semanticScore !== undefined ? (
                            <span>sem {source.semanticScore.toFixed(2)}</span>
                          ) : null}
                        </div>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">{source.excerpt}</p>
                      {source.explanation ? (
                        <p className="mt-2 text-xs uppercase tracking-[0.16em] text-subtle">
                          {source.explanation}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-4">
            <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">Index status</p>
              {indexState ? (
                <>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{indexState.modelName}</p>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {indexState.sourceCount} sources / {indexState.vectorDimension} dimensions
                      </p>
                    </div>
                    <StatusBadge status={indexState.status} />
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Corpus version {indexState.corpusVersion}
                  </p>
                </>
              ) : (
                <EmptyState
                  title="No semantic index yet"
                  description="Build the semantic index to unlock embedding-based legal retrieval and hybrid reranking."
                />
              )}
            </Card>

            <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">Retrieval leaderboard</p>
              {leaderboardState.entries.length ? (
                leaderboardState.entries.slice(0, 6).map((entry, index) => (
                  <div key={`${entry.mode}-${entry.query}-${index}`} className="rounded-2xl border border-line bg-panel-highlight p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-foreground">{entry.mode}</p>
                      <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                        {entry.averageScore.toFixed(2)} avg
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{entry.query}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  Build the semantic index to populate retrieval comparisons.
                </p>
              )}
            </Card>

            <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">Benchmark posture</p>
              {selectedBenchmark ? (
                <>
                  <div className="rounded-2xl border border-line bg-panel-highlight p-3">
                    <p className="text-sm font-medium text-foreground">{selectedBenchmark.name}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      {selectedBenchmark.queryCount} benchmark queries / {formatDateTime(selectedBenchmark.createdAt)}
                    </p>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(
                      (selectedBenchmark.metricsJson.aggregate as Record<string, { averageHitAtK?: number; averageMrr?: number }>) ?? {},
                    ).map(([mode, metrics]) => (
                      <div key={`${selectedBenchmark.id}-${mode}`} className="rounded-2xl border border-line bg-white/[0.03] p-3">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-medium text-foreground">{mode}</p>
                          <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                            hit@k {(metrics.averageHitAtK ?? 0).toFixed(2)}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">
                          MRR {(metrics.averageMrr ?? 0).toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  Run the benchmark suite to compare lexical, semantic, and hybrid retrieval quality.
                </p>
              )}
            </Card>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Retrieval benchmarking"
        description="Benchmark lexical, semantic, and hybrid retrieval with Phase 9 reranking signals, heuristic relevance checks, and query-level comparison."
      >
        {selectedBenchmark ? (
          <div className="space-y-4">
            <InlineFeedback
              tone="info"
              message="Benchmark relevance remains heuristic for the current seeded corpus subset. Use these results as a readiness signal, not a final retrieval benchmark."
            />
            <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
              <div className="space-y-3">
                <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
                  <p className="text-xs uppercase tracking-[0.18em] text-subtle">Recent benchmark runs</p>
                  {benchmarkRunsState.slice(0, 5).map((benchmark) => (
                    <button
                      key={benchmark.id}
                      className={cn(
                        "w-full rounded-2xl border p-3 text-left transition-colors",
                        selectedBenchmark.id === benchmark.id
                          ? "border-accent/40 bg-accent/8"
                          : "border-line bg-panel-highlight hover:border-accent/25",
                      )}
                      onClick={async () => {
                        if (benchmark.id === selectedBenchmark.id) {
                          return;
                        }
                        const detail = await getRetrievalBenchmark(benchmark.id);
                        setSelectedBenchmark(detail);
                      }}
                      type="button"
                    >
                      <p className="text-sm font-medium text-foreground">{benchmark.name}</p>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {benchmark.queryCount} queries / {formatDateTime(benchmark.createdAt)}
                      </p>
                    </button>
                  ))}
                </Card>

                <Card className="space-y-3 rounded-[24px] border-line bg-white/[0.03]">
                  <p className="text-xs uppercase tracking-[0.18em] text-subtle">Reranking mode</p>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Hybrid retrieval now passes through a heuristic legal reranker that combines lexical score, semantic score, source type, citation matches, and language match. The interface remains cross-encoder ready for later training.
                  </p>
                </Card>
              </div>

              <div className="space-y-4">
                {benchmarkGroups.slice(0, 4).map((group) => (
                  <Card key={`${selectedBenchmark.id}-${group.query}`} className="space-y-4 rounded-[24px] border-line bg-white/[0.03]">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">Benchmark query</p>
                        <h3 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                          {group.query}
                        </h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {group.results[0]?.expectedLabels.map((label) => (
                          <span
                            key={`${group.query}-${label}`}
                            className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                          >
                            {label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                      {group.results.map((result) => (
                        <div
                          key={`${group.query}-${result.mode}`}
                          className="rounded-2xl border border-line bg-panel-highlight p-4"
                        >
                          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                            {result.mode}
                          </p>
                          <p className="mt-2 text-sm font-medium text-foreground">
                            hit@k {Number(result.metricsJson.hitAtK ?? 0).toFixed(0)}
                          </p>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">
                            MRR {Number(result.metricsJson.mrr ?? 0).toFixed(2)}
                          </p>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">
                            Top: {String((result.resultsJson[0] as Record<string, unknown> | undefined)?.citationLabel ?? "No match")}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <EmptyState
            title="No retrieval benchmark runs yet"
            description="Run the benchmark suite to compare lexical, semantic, and hybrid retrieval quality."
            action={
              <Button onClick={handleRunBenchmark} variant="secondary">
                Run benchmark
              </Button>
            }
          />
        )}
      </SectionCard>

      <Card className="rounded-[28px]">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
          <label className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
              Active crawl source
            </span>
            <select
              className="h-11 w-full rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50"
              value={selectedSourceId}
              onChange={(event) => setSelectedSourceId(event.target.value)}
            >
              {sourcesState.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </select>
          </label>

          <div className="flex flex-wrap items-end gap-3">
            <Button
              onClick={() => selectedSourceId && handleRunCrawl(selectedSourceId)}
              disabled={!selectedSourceId || runningSourceId === selectedSourceId}
            >
              {runningSourceId === selectedSourceId ? "Running crawl..." : "Run crawl"}
            </Button>
          </div>
        </div>

        {selectedSource ? (
          <div className="mt-4 rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{selectedSource.name}</span>
            {" · "}
            {selectedSource.category}
            {" · "}
            {selectedSource.languageHint}
            {" · "}
            {Array.isArray(selectedSource.configJson.entryUrls)
              ? selectedSource.configJson.entryUrls.length
              : 0}{" "}
            configured entry points
          </div>
        ) : null}
      </Card>

      <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <SectionCard
            title="Source registry"
            description="Configured crawl definitions for statutes, case law, and bilingual legal material."
          >
            <div className="grid gap-4 xl:grid-cols-2">
              {sourcesState.map((source) => {
                const active = selectedSourceId === source.id;
                const selectSource = () => setSelectedSourceId(source.id);
                return (
                  <div
                    key={source.id}
                    role="button"
                    tabIndex={0}
                    className={cn(
                      "rounded-[24px] border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/45",
                      active
                        ? "border-accent/40 bg-accent/8"
                        : "border-line bg-white/[0.03] hover:border-accent/25",
                    )}
                    onClick={selectSource}
                    onKeyDown={(event) => {
                      if (event.currentTarget !== event.target) {
                        return;
                      }
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        selectSource();
                      }
                    }}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          {source.sourceType} / {source.crawlMode}
                        </p>
                        <h3 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                          {source.name}
                        </h3>
                      </div>
                      <StatusBadge status={source.isActive ? "Active" : "Disabled"} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">
                      Category: {source.category}. Language hint: {source.languageHint}. Entry URLs:{" "}
                      {Array.isArray(source.configJson.entryUrls)
                        ? source.configJson.entryUrls.length
                        : 0}
                    </p>
                    <div className="mt-4 flex justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleRunCrawl(source.id);
                        }}
                        disabled={runningSourceId === source.id}
                      >
                        {runningSourceId === source.id ? "Running..." : "Run crawl"}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </SectionCard>

          <SectionCard
            title="Recent crawl jobs"
            description="Stored crawl history with source status, volume, and warnings."
          >
            {jobsState.length ? (
              <div className="space-y-3">
                {jobsState.map((job) => (
                  <div
                    key={job.id}
                    className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {job.sourceName}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          Pages: {job.pagesFetched} / Documents: {job.documentsDiscovered} / Saved:{" "}
                          {job.documentsSaved}
                        </p>
                      </div>
                      <StatusBadge status={job.status} />
                    </div>
                    <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                      {formatDateTime(job.startedAt)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No crawl jobs yet"
                description="Run one of the registered legal-source crawls to begin expanding the chamber corpus."
              />
            )}
          </SectionCard>

          <SectionCard
            title="Crawled documents"
            description="Stored legal documents from the crawl layer. Process a record to extract OCR or retrieval-ready text."
          >
            <div className="space-y-4">
              <SearchInput
                placeholder="Search title, source, language, document type"
                value={search}
                onChange={setSearch}
              />

              {filteredDocuments.length ? (
                <div className="space-y-3">
                  {filteredDocuments.map((document) => {
                    const selectDocument = () => setSelectedDocumentId(document.id);
                    return (
                      <div
                        key={document.id}
                        role="button"
                        tabIndex={0}
                        className={cn(
                          "w-full rounded-[24px] border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/45",
                          selectedDocumentId === document.id
                            ? "border-accent/40 bg-accent/8"
                            : "border-line bg-white/[0.03] hover:border-accent/25",
                        )}
                        onClick={selectDocument}
                      onKeyDown={(event) => {
                        if (event.currentTarget !== event.target) {
                          return;
                        }
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          selectDocument();
                          }
                        }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                              {document.sourceName} / {document.documentType}
                            </p>
                            <p className="mt-1 text-sm font-medium text-foreground">
                              {document.title}
                            </p>
                          </div>
                          <StatusBadge status={document.processingStatus} />
                        </div>
                        <p className="mt-3 text-sm leading-6 text-muted-foreground">
                          {document.extractedTextPreview ||
                            "No processed text yet. Run processing to create retrieval-ready content."}
                        </p>
                        <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                          {document.languageDetected || document.language} / {document.mimeType}
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <EmptyState
                  title="No crawled documents match the current view"
                  description="Run a crawl or adjust the search and source filters."
                />
              )}
            </div>
          </SectionCard>

          <SectionCard
            title="Corpus readiness"
            description="Recent corpus entries prepared for retrieval and later DNN tasks."
          >
            {corpusState.length ? (
              <div className="space-y-3">
                {corpusState.slice(0, 8).map((entry) => (
                  <div
                    key={entry.id}
                    className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {entry.title}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {entry.sourceKind} / {entry.language} / {entry.chunkCount} chunks
                        </p>
                      </div>
                      <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        {entry.datasetSplit}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="Corpus not built yet"
                description="Build the corpus after processing crawled documents to create retrieval-ready and training-ready records."
              />
            )}
          </SectionCard>
        </div>

        <SectionCard
          title="Selected document"
          description="Inspect OCR posture, language, provenance, and extracted content for the selected crawled record."
        >
          {selectedDocument ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                  {selectedDocument.sourceName}
                </p>
                <h3 className="text-lg font-semibold tracking-tight text-foreground">
                  {selectedDocument.title}
                </h3>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge status={selectedDocument.crawlStatus} />
                  <StatusBadge status={selectedDocument.processingStatus} />
                  <StatusBadge status={selectedDocument.ocrStatus || "Not Started"} />
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {selectedDocument.rawHtmlUrl ? (
                  <a
                    className={buttonVariants({ size: "sm", variant: "secondary" })}
                    href={selectedDocument.rawHtmlUrl}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Open raw HTML
                  </a>
                ) : null}
                {selectedDocument.downloadedFileUrl ? (
                  <a
                    className={buttonVariants({ size: "sm", variant: "secondary" })}
                    href={selectedDocument.downloadedFileUrl}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Open downloaded file
                  </a>
                ) : null}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void handleProcessDocument(false)}
                  disabled={processingDocumentId === selectedDocument.id}
                >
                  {processingDocumentId === selectedDocument.id
                    ? "Processing..."
                    : "Process document"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void handleProcessDocument(true)}
                  disabled={processingDocumentId === selectedDocument.id}
                >
                  Force OCR
                </Button>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-line bg-white/[0.03] p-4 text-sm text-muted-foreground">
                  <p>Language hint: {selectedDocument.language}</p>
                  <p>Detected language: {selectedDocument.languageDetected}</p>
                  <p>Document type: {selectedDocument.documentType}</p>
                  <p>OCR engine: {selectedDocument.ocrEngine || "Not used yet"}</p>
                  <p>
                    OCR confidence:{" "}
                    {selectedDocument.ocrConfidenceSummary !== null
                      ? selectedDocument.ocrConfidenceSummary.toFixed(2)
                      : "n/a"}
                  </p>
                </div>
                <div className="rounded-2xl border border-line bg-white/[0.03] p-4 text-sm text-muted-foreground">
                  <p>Jurisdiction: {selectedDocument.jurisdiction}</p>
                  <p>Pages: {selectedDocument.pageCount}</p>
                  <p>Source URL: {selectedDocument.sourceUrl}</p>
                  <p>Linked legal source: {selectedDocument.legalSourceId ?? "Not promoted yet"}</p>
                </div>
              </div>

              {selectedDocument.errorsJson.message ? (
                <InlineFeedback
                  message={String(selectedDocument.errorsJson.message)}
                  tone="error"
                />
              ) : null}

              <div className="rounded-[24px] border border-line bg-[#0f151d] p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
                  Extracted text preview
                </p>
                <p className="mt-4 whitespace-pre-line text-sm leading-7 text-foreground/88">
                  {selectedDocument.extractedText ||
                    selectedDocument.extractedTextPreview ||
                    "This crawled document has not been processed yet."}
                </p>
              </div>

              {Array.isArray(selectedDocument.metadataJson.pageExtractions) &&
              selectedDocument.metadataJson.pageExtractions.length ? (
                <div className="space-y-3">
                  {selectedDocument.metadataJson.pageExtractions
                    .slice(0, 4)
                    .map((page, index) => {
                      if (!page || typeof page !== "object") {
                        return null;
                      }
                      const record = page as Record<string, unknown>;
                      return (
                        <div
                          key={`${selectedDocument.id}-trace-${index}`}
                          className="rounded-2xl border border-line bg-white/[0.03] p-4"
                        >
                          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                            Page {String(record.pageNumber ?? index + 1)} / {String(record.method ?? "unknown")}
                          </p>
                          <p className="mt-2 text-sm leading-6 text-muted-foreground">
                            {String(record.textPreview ?? "")}
                          </p>
                        </div>
                      );
                    })}
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState
              title="No crawled document selected"
              description="Run a crawl and select one of the stored documents to inspect OCR and corpus readiness."
            />
          )}
        </SectionCard>
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
  icon: typeof Globe2;
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
