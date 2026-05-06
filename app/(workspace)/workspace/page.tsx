import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { CommandWorkspace } from "@/components/workspace/command-workspace";
import { getCases } from "@/lib/api/client";

export default async function WorkspacePage({
  searchParams,
}: {
  searchParams: Promise<{ caseId?: string }>;
}) {
  const result = await loadWorkspaceData();
  const params = await searchParams;

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Workspace"
          title="Legal command chamber"
          description="The chamber command surface could not be loaded."
        />
        <ErrorState
          title="Workspace unavailable"
          message={`${result.message} Confirm the backend API is running so the command workspace can load live matters.`}
        />
      </div>
    );
  }

  return (
    <CommandWorkspace
      cases={result.cases}
      initialCaseId={params.caseId ?? result.cases[0]?.id ?? null}
    />
  );
}

async function loadWorkspaceData() {
  try {
    return {
      ok: true as const,
      cases: await getCases(),
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load workspace matters.",
    };
  }
}
