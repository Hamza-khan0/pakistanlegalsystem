import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { KnowledgeWorkspace } from "@/components/knowledge/knowledge-workspace";
import {
  getRetrievalBenchmark,
  getRetrievalBenchmarks,
  getRetrievalIndexStatus,
  getRetrievalLeaderboard,
  getCorpusEntries,
  getCrawledDocuments,
  getCrawlJobs,
  getCrawlSources,
} from "@/lib/api/client";

export default async function KnowledgePage() {
  const result = await loadKnowledgeData();

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Knowledge"
          title="Legal corpus and OCR lab"
          description="The Phase 6 corpus surface could not be loaded."
        />
        <ErrorState
          title="Knowledge workspace unavailable"
          message={`${result.message} Confirm the backend is running and the Phase 6 migration/seed steps have been applied.`}
        />
      </div>
    );
  }

  return (
    <KnowledgeWorkspace
      sources={result.sources}
      jobs={result.jobs}
      documents={result.documents}
      corpusEntries={result.corpusEntries}
      indexStatus={result.indexStatus}
      retrievalLeaderboard={result.retrievalLeaderboard}
      benchmarkRuns={result.benchmarkRuns}
      latestBenchmark={result.latestBenchmark}
    />
  );
}

async function loadKnowledgeData() {
  try {
    const [sources, jobs, documents, corpusEntries, indexStatus, retrievalLeaderboard, benchmarkRuns] = await Promise.all([
      getCrawlSources(),
      getCrawlJobs(),
      getCrawledDocuments(),
      getCorpusEntries(),
      getRetrievalIndexStatus().catch(() => null),
      getRetrievalLeaderboard().catch(() => ({ generatedAt: new Date().toISOString(), entries: [] })),
      getRetrievalBenchmarks().catch(() => []),
    ]);
    const latestBenchmark = benchmarkRuns[0]
      ? await getRetrievalBenchmark(benchmarkRuns[0].id).catch(() => null)
      : null;

    return {
      ok: true as const,
      sources,
      jobs,
      documents,
      corpusEntries,
      indexStatus,
      retrievalLeaderboard,
      benchmarkRuns,
      latestBenchmark,
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load knowledge data.",
    };
  }
}
