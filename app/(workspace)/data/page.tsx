import { DataWorkspace } from "@/components/data/data-workspace";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import {
  getTier1AuditLabels,
  getTier1Documents,
  getTier1Readiness,
  getTier1Report,
} from "@/lib/api/client";
import type { Tier1Document, Tier1Label, Tier1Readiness, Tier1Report } from "@/types";

export default async function DataPage() {
  let documents: Tier1Document[] = [];
  let auditLabels: Tier1Label[] = [];
  let readiness: Tier1Readiness[] = [];
  let report: Tier1Report | null = null;
  let loadError: unknown = null;

  try {
    [documents, auditLabels, readiness, report] = await Promise.all([
      getTier1Documents().catch(() => []),
      getTier1AuditLabels().catch(() => []),
      getTier1Readiness().catch(() => []),
      getTier1Report().catch(() => null),
    ]);
  } catch (error) {
    loadError = error;
  }

  if (loadError) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Tier 1 data"
          title="Training data preparation"
          description="The Tier 1 data workspace could not be loaded."
        />
        <ErrorState
          title="Tier 1 data unavailable"
          message={
            loadError instanceof Error
              ? loadError.message
              : "Unable to load the Tier 1 data preparation layer."
          }
        />
      </div>
    );
  }

  return (
    <DataWorkspace
      documents={documents}
      auditLabels={auditLabels}
      readiness={readiness}
      report={report}
    />
  );
}
