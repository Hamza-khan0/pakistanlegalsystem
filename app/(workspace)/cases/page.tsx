import { CasesView } from "@/components/cases/cases-view";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { getApiBaseUrl, getCases } from "@/lib/api/client";

export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<{ create?: string; edit?: string }>;
}) {
  const result = await loadCases();
  const intent = await searchParams;

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Cases"
          title="Matter portfolio"
          description="The live case portfolio could not be loaded."
        />
        <ErrorState
          title="Cases unavailable"
          message={`${result.message} Could not load the live case portfolio from ${getApiBaseUrl()}. Confirm FastAPI is running on that URL, then run migrations and seed data if the API returns an empty portfolio.`}
        />
      </div>
    );
  }

  const editCase = intent.edit
    ? result.cases.find((caseItem) => caseItem.id === intent.edit) ?? null
    : null;
  const initialMode = editCase ? "edit" : intent.create === "1" ? "create" : null;

  return (
    <CasesView
      key={`cases-${intent.create ?? "none"}-${intent.edit ?? "none"}`}
      cases={result.cases}
      initialEditCaseId={editCase?.id ?? null}
      initialMode={initialMode}
    />
  );
}

async function loadCases() {
  try {
    return {
      ok: true as const,
      cases: await getCases(),
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load cases.",
    };
  }
}
