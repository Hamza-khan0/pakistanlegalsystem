import Link from "next/link";
import { notFound } from "next/navigation";

import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { StatusBadge } from "@/components/common/status-badge";
import { EditableDraftCard } from "@/components/research/editable-draft-card";
import { buttonVariants } from "@/components/ui/button";
import {
  ApiClientError,
  getResearchPdfUrl,
  getResearchMarkdownUrl,
  getResearchRun,
} from "@/lib/api/client";
import { formatDate } from "@/lib/utils";

export default async function ResearchRunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  const result = await loadResearchRun(runId);

  if (!result.ok) {
    if (result.notFound) {
      notFound();
    }

    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Research & Draft"
          title="Run unavailable"
          description="The stored research run could not be loaded."
        />
        <ErrorState
          title="Research run unavailable"
          message={`${result.message} Confirm FastAPI is running and the run exists.`}
        />
      </div>
    );
  }

  const run = result.run;
  const draft = run.generatedDraft;
  const sourcesByOrigin = Object.entries(run.sourcesByOrigin);

  return (
    <div className="mx-auto w-full max-w-[1600px] min-w-0 space-y-6">
      <PageHeader
        eyebrow="Research & Draft"
        title={draft?.title || run.researchMemo.recommendedDraftType.replaceAll("_", " ")}
        description={`Stored run from ${formatDate(run.createdAt)}. This page displays the memo, draft, sources, critic report, and artifacts without rerunning the workflow.`}
        meta={[
          `Run ${run.runId.slice(0, 8)}`,
          `Case ${run.caseId}`,
          run.liveWebUsed ? "Live web used" : "Local/fallback research",
          run.llmUsedForDrafting ? "LLM draft" : "Deterministic draft",
        ]}
        actions={
          <div className="flex flex-wrap gap-2">
            <Link
              className={buttonVariants({ variant: "secondary" })}
              href={`/cases/${run.caseId}?runs=1`}
            >
              Back to case
            </Link>
            <a
              className={buttonVariants({ variant: "outline" })}
              href={getResearchMarkdownUrl(run.runId)}
              rel="noreferrer"
              target="_blank"
            >
              Open markdown
            </a>
            {run.pdfPath ? (
              <a
                className={buttonVariants()}
                href={getResearchPdfUrl(run.runId)}
                rel="noreferrer"
                target="_blank"
              >
                Download PDF
              </a>
            ) : null}
          </div>
        }
      />

      <SectionCard className="min-w-0" title="Status and Provider Trace">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge
            status={
              run.status === "completed"
                ? "Completed"
                : run.status === "failed"
                  ? "Failed"
                  : "Needs Review"
            }
          />
          <span className="legal-text-wrap text-sm text-muted-foreground">{run.legalAuthorityWarning}</span>
        </div>
        {run.privacyNotice ? (
          <p className="legal-text-wrap mt-4 text-sm leading-6 text-muted-foreground">
            {run.privacyNotice}
          </p>
        ) : null}
      </SectionCard>

      <SectionCard className="min-w-0" title="Detected Issues">
        <div className="flex flex-wrap gap-2">
          {run.detectedIssues.map((issue) => (
            <span
              className="rounded-full border border-line px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
              key={`${issue.label}-${issue.source}`}
            >
              {issue.label.replaceAll("_", " ")}
              {typeof issue.probability === "number"
                ? ` · ${Math.round(issue.probability * 100)}%`
                : ""}
            </span>
          ))}
        </div>
      </SectionCard>

      <SectionCard className="min-w-0" title="Sources Used">
        <div className="space-y-5">
          {sourcesByOrigin.map(([origin, value]) => {
            const sources = Array.isArray(value) ? value : [];
            return (
              <div className="space-y-3" key={origin}>
                <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-subtle">
                  {origin.replaceAll("_", " ")} ({sources.length})
                </h3>
                {sources.length ? (
                  <div className="grid gap-3">
                    {sources.slice(0, 8).map((source, index) => (
                      <div
                        className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4"
                        key={`${origin}-${source.id ?? source.url ?? index}`}
                      >
                        <p className="legal-text-wrap font-medium text-foreground">{source.title}</p>
                        <p className="legal-url-wrap mt-1 text-xs uppercase tracking-[0.16em] text-subtle">
                          {source.citation || source.sourceType}
                        </p>
                        <p className="legal-text-wrap mt-2 text-sm leading-6 text-muted-foreground">
                          {source.excerpt}
                        </p>
                        {source.url ? (
                          <a
                            className="legal-url-wrap mt-2 inline-flex max-w-full text-sm font-medium text-accent"
                            href={source.url}
                            rel="noreferrer"
                            target="_blank"
                          >
                            Open source
                          </a>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No sources in this group.</p>
                )}
              </div>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard className="min-w-0" title="Structured Research Memo">
        <MemoList title="Factual basis" items={run.researchMemo.factualBasis} />
        <MemoList title="Arguments for client" items={run.researchMemo.argumentsForClient} />
        <MemoList title="Arguments against client" items={run.researchMemo.argumentsAgainstClient} />
        <MemoList title="Research gaps" items={run.researchMemo.researchGaps} />
      </SectionCard>

      <SectionCard className="min-w-0" title="Generated Draft">
        <EditableDraftCard run={run} />
      </SectionCard>

      <SectionCard className="min-w-0" title="Critic Report">
        <div className="grid min-w-0 gap-4 md:grid-cols-2">
          <MemoList title="Required lawyer checks" items={run.criticReport.requiredLawyerChecks ?? []} />
          <MemoList title="Drafting defects" items={run.criticReport.draftingDefects ?? []} />
          <MemoList title="Missing authorities" items={run.criticReport.missingAuthorities} />
          <MemoList title="Overclaiming warnings" items={run.criticReport.overclaimingWarnings} />
        </div>
        <p className="legal-text-wrap mt-4 text-sm leading-6 text-muted-foreground">
          {run.criticReport.recommendation}
        </p>
      </SectionCard>
    </div>
  );
}

function MemoList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mb-5 min-w-0 space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-subtle">{title}</h3>
      {items.length ? (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              className="legal-text-wrap rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm leading-6 text-muted-foreground"
              key={`${title}-${index}`}
            >
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">None reported.</p>
      )}
    </div>
  );
}

async function loadResearchRun(runId: string) {
  try {
    const run = await getResearchRun(runId);
    return { ok: true as const, run };
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 404) {
      return {
        ok: false as const,
        notFound: true as const,
        message: "Research run not found.",
      };
    }
    return {
      ok: false as const,
      notFound: false as const,
      message: error instanceof Error ? error.message : "Unable to load research run.",
    };
  }
}
