import { ModelsWorkspace } from "@/components/models/models-workspace";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { getDatasetReadiness, getEvaluationReports, getMlDatasets, getMlModels } from "@/lib/api/client";

export default async function ModelsPage() {
  let datasets;
  let models;
  let readiness;
  let reports;
  try {
    [datasets, models, readiness, reports] = await Promise.all([
      getMlDatasets(),
      getMlModels(),
      getDatasetReadiness().catch(() => []),
      getEvaluationReports().catch(() => []),
    ]);
  } catch (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Models"
          title="Prediction engine lab"
          description="The ML workspace could not be loaded."
        />
        <ErrorState
          title="ML data unavailable"
          message={
            error instanceof Error
              ? error.message
              : "Unable to load the Phase 7 model registry."
          }
        />
      </div>
    );
  }

  return (
    <ModelsWorkspace
      datasets={datasets}
      models={models}
      readiness={readiness}
      reports={reports}
    />
  );
}
