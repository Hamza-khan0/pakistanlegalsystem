import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { DocumentsView } from "@/components/documents/documents-view";
import { getCases, getDocuments } from "@/lib/api/client";

export default async function DocumentsPage({
  searchParams,
}: {
  searchParams: Promise<{ upload?: string; caseId?: string }>;
}) {
  const result = await loadDocumentsData();
  const intent = await searchParams;

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Documents"
          title="Central document library"
          description="The live document index could not be loaded."
        />
        <ErrorState
          title="Documents unavailable"
          message={`${result.message} Start the backend and seed the database to populate the document library.`}
        />
      </div>
    );
  }

  return (
    <DocumentsView
      key={`documents-${intent.upload ?? "none"}-${intent.caseId ?? "none"}`}
      documents={result.documents}
      cases={result.cases}
      initialCaseId={intent.caseId ?? null}
      initialUploadOpen={intent.upload === "1" || Boolean(intent.caseId)}
    />
  );
}

async function loadDocumentsData() {
  try {
    const [documents, cases] = await Promise.all([getDocuments(), getCases()]);
    return {
      ok: true as const,
      documents,
      cases,
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load documents.",
    };
  }
}
