import { AgentsWorkspace } from "@/components/agents/agents-workspace";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { getCases } from "@/lib/api/client";

export default async function AgentsPage({
  searchParams,
}: {
  searchParams: Promise<{ caseId?: string }>;
}) {
  const result = await loadAgentsData();
  const params = await searchParams;

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Agents"
          title="Multi-agent chamber operations"
          description="The agent operations workspace could not be loaded."
        />
        <ErrorState
          title="Agents workspace unavailable"
          message={`${result.message} Confirm the backend API is running so the agent surfaces can load live matters.`}
        />
      </div>
    );
  }

  return (
    <AgentsWorkspace
      cases={result.cases}
      initialCaseId={params.caseId ?? result.cases[0]?.id ?? null}
    />
  );
}

async function loadAgentsData() {
  try {
    return {
      ok: true as const,
      cases: await getCases(),
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load agent matters.",
    };
  }
}
