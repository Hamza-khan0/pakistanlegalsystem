import { notFound } from "next/navigation";

import { CaseDetailView } from "@/components/cases/case-detail-view";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import {
  ApiClientError,
  getCaseDetail,
  getCasePredictionExplanations,
  getCasePredictions,
  getCaseQualitySummary,
  getDatasetReadiness,
} from "@/lib/api/client";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const result = await loadCaseDetail(id);

  if (!result.ok) {
    if (result.notFound) {
      notFound();
    }

    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Case"
          title="Matter workspace"
          description="The live case workspace could not be loaded."
        />
        <ErrorState
          title="Case data unavailable"
          message={`${result.message} Confirm the backend API is running and the requested case exists in the seeded database.`}
        />
      </div>
    );
  }

  return (
    <CaseDetailView
      key={id}
      caseItem={result.detail.caseItem}
      documents={result.detail.documents}
      timeline={result.detail.timeline}
      notes={result.detail.notes}
      research={result.detail.research}
      intelligence={result.detail.intelligence}
      agentOutputs={result.detail.agentOutputs}
      runs={result.detail.runs}
      legalBasis={result.detail.legalBasis}
      predictions={result.predictions}
      predictionExplanations={result.predictionExplanations}
      datasetReadiness={result.datasetReadiness}
      caseQualitySummary={result.caseQualitySummary}
    />
  );
}

async function loadCaseDetail(id: string) {
  try {
    const [detail, predictions, predictionExplanations, datasetReadiness, caseQualitySummary] = await Promise.all([
      getCaseDetail(id),
      getCasePredictions(id).catch(() => []),
      getCasePredictionExplanations(id).catch(() => []),
      getDatasetReadiness().catch(() => []),
      getCaseQualitySummary(id).catch(() => null),
    ]);
    return {
      ok: true as const,
      detail,
      predictions,
      predictionExplanations,
      datasetReadiness,
      caseQualitySummary,
    };
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 404) {
      return {
        ok: false as const,
        notFound: true as const,
        message: "Case not found.",
      };
    }

    return {
      ok: false as const,
      notFound: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load case detail.",
    };
  }
}
