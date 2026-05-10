"use client";

import { useMemo, useState, useTransition } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  getResearchMarkdownUrl,
  getResearchPdfUrl,
  regenerateResearchDraft,
  regenerateResearchPdf,
  updateResearchDraft,
} from "@/lib/api/client";
import { formatDateTime } from "@/lib/utils";
import type { GeneratedDraft, PdfMode, ResearchWorkflowResponse } from "@/types";

type EditableDraftCardProps = {
  run: ResearchWorkflowResponse;
  onRunUpdated?: (run: ResearchWorkflowResponse) => void;
};

function finalDraftText(draft: GeneratedDraft | null | undefined) {
  return draft?.finalDraftMarkdown || draft?.editedDraftMarkdown || draft?.draftMarkdown || "";
}

export function EditableDraftCard({ run, onRunUpdated }: EditableDraftCardProps) {
  const [localDraft, setLocalDraft] = useState<GeneratedDraft | null>(null);
  const [localPdfPath, setLocalPdfPath] = useState<string | null>(null);
  const [localRunId, setLocalRunId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [pdfMode, setPdfMode] = useState<PdfMode>("draft_with_research");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const draft = localRunId === run.runId ? localDraft ?? run.generatedDraft ?? null : run.generatedDraft ?? null;
  const pdfPath = localRunId === run.runId ? localPdfPath ?? run.pdfPath ?? null : run.pdfPath ?? null;
  const displayedText = useMemo(() => finalDraftText(draft), [draft]);
  const isEdited = Boolean(draft?.editedDraftMarkdown);
  const pdfStale = Boolean(draft?.pdfStale);
  const draftTypeLooksMemo = draft?.draftType === "research_memo";

  function updateParent(nextDraft: GeneratedDraft, nextPdfPath = pdfPath) {
    onRunUpdated?.({
      ...run,
      generatedDraft: nextDraft,
      pdfPath: nextPdfPath,
    });
  }

  function handleSave() {
    setError(null);
    setMessage(null);
    startTransition(() => {
      void (async () => {
        try {
          const response = await updateResearchDraft(
            run.runId,
            draftText,
            "Edited in browser draft workspace.",
          );
          setLocalRunId(run.runId);
          setLocalDraft(response.generatedDraft);
          setDraftText(response.finalDraftMarkdown);
          setIsEditing(false);
          setMessage("Draft saved. Regenerate the PDF to include the latest edits.");
          updateParent(response.generatedDraft);
        } catch (saveError) {
          setError(saveError instanceof Error ? saveError.message : "Unable to save draft.");
        }
      })();
    });
  }

  function handleRegeneratePdf() {
    setError(null);
    setMessage(null);
    startTransition(() => {
      void (async () => {
        try {
          const response = await regenerateResearchPdf(run.runId, true, pdfMode);
          setLocalRunId(run.runId);
          setLocalPdfPath(response.pdfPath);
          const nextDraft = draft ? { ...draft, pdfStale: false, pdfGeneratedAt: new Date().toISOString() } : draft;
          if (nextDraft) {
            setLocalDraft(nextDraft);
            updateParent(nextDraft, response.pdfPath);
          }
          setMessage(`PDF regenerated from the final draft (${Math.round(response.fileSizeBytes / 1024)} KB).`);
        } catch (pdfError) {
          setError(pdfError instanceof Error ? pdfError.message : "Unable to regenerate PDF.");
        }
      })();
    });
  }

  function handleRegenerateWritDraft() {
    setError(null);
    setMessage(null);
    startTransition(() => {
      void (async () => {
        try {
          const response = await regenerateResearchDraft(run.runId, "writ_petition", true);
          setLocalRunId(run.runId);
          setLocalDraft(response.generatedDraft);
          setDraftText(response.finalDraftMarkdown);
          setIsEditing(false);
          setMessage("Draft regenerated as a writ petition. Review it, then regenerate the PDF.");
          updateParent(response.generatedDraft);
        } catch (draftError) {
          setError(draftError instanceof Error ? draftError.message : "Unable to regenerate writ petition draft.");
        }
      })();
    });
  }

  if (!draft) {
    return (
      <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
        <p className="text-sm text-muted-foreground">No full legal draft was generated for this run.</p>
      </div>
    );
  }

  return (
    <div className="min-w-0 rounded-[28px] border border-line bg-white/[0.03] p-4 sm:p-5 lg:p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.2em] text-subtle">Generated legal draft</p>
          <h4 className="legal-text-wrap mt-1 text-lg font-semibold text-foreground">{draft.title}</h4>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {draft.draftType.replaceAll("_", " ")}
            </span>
            {isEdited ? (
              <span className="rounded-full border border-accent/40 bg-accent/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-accent">
                Edited
              </span>
            ) : null}
            {draft.lastEditedAt ? (
              <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Last edited {formatDateTime(draft.lastEditedAt)}
              </span>
            ) : null}
          </div>
        </div>
      </div>

      {message ? (
        <div className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-3 text-sm text-emerald-100">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}
      {pdfStale ? (
        <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100">
          Draft was edited after the last PDF was generated. Regenerate PDF to include latest edits.
        </div>
      ) : null}
      {draftTypeLooksMemo ? (
        <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100">
          Draft type appears to be memo only. If this matter needs filing, regenerate it as a Writ Petition.
        </div>
      ) : null}

      {isEditing ? (
        <textarea
          className="legal-text-wrap mt-5 min-h-[620px] w-full resize-y rounded-[24px] border border-line bg-panel p-5 text-[15px] leading-7 text-foreground outline-none focus:border-accent sm:p-6"
          onChange={(event) => setDraftText(event.target.value)}
          value={draftText}
        />
      ) : (
        <div className="legal-text-wrap mt-5 max-w-full rounded-[24px] border border-line bg-panel p-5 text-[15px] leading-8 text-foreground/88 sm:p-6">
          {displayedText}
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        {isEditing ? (
          <>
            <Button disabled={isPending || !draftText.trim()} onClick={handleSave} size="sm" type="button">
              {isPending ? "Saving..." : "Save Draft"}
            </Button>
            <Button
              disabled={isPending}
              onClick={() => {
                setDraftText(displayedText);
                setIsEditing(false);
                setError(null);
              }}
              size="sm"
              type="button"
              variant="secondary"
            >
              Cancel Edit
            </Button>
          </>
        ) : (
          <Button
            onClick={() => {
              setDraftText(displayedText);
              setIsEditing(true);
            }}
            size="sm"
            type="button"
          >
            Edit Draft
          </Button>
        )}
        <Button disabled={isPending} onClick={handleRegeneratePdf} size="sm" type="button" variant="secondary">
          {pdfPath ? "Regenerate PDF" : "Generate PDF"}
        </Button>
        <label className="flex min-w-0 flex-wrap items-center gap-2 rounded-full border border-line px-3 py-1.5 text-xs text-muted-foreground">
          PDF mode
          <select
            className="max-w-full bg-panel text-foreground outline-none"
            disabled={isPending}
            onChange={(event) => setPdfMode(event.target.value as PdfMode)}
            value={pdfMode}
          >
            <option value="draft_with_research">Draft with research</option>
            <option value="draft_only">Draft only</option>
            <option value="full_trace">Full trace/debug</option>
          </select>
        </label>
        {draftTypeLooksMemo ? (
          <Button disabled={isPending} onClick={handleRegenerateWritDraft} size="sm" type="button" variant="secondary">
            Regenerate Draft as Writ Petition
          </Button>
        ) : null}
        <Button
          onClick={() => {
            void navigator.clipboard?.writeText(displayedText);
            setMessage("Draft copied to clipboard.");
          }}
          size="sm"
          type="button"
          variant="outline"
        >
          Copy Draft
        </Button>
        <a
          className={buttonVariants({ size: "sm", variant: "outline" })}
          href={getResearchMarkdownUrl(run.runId)}
          rel="noreferrer"
          target="_blank"
        >
          Open Markdown
        </a>
        {pdfPath ? (
          <>
            <a
              className={buttonVariants({ size: "sm", variant: "outline" })}
              href={getResearchPdfUrl(run.runId)}
              rel="noreferrer"
              target="_blank"
            >
              Open PDF
            </a>
            <a
              className={buttonVariants({ size: "sm", variant: "outline" })}
              href={getResearchPdfUrl(run.runId, true)}
              rel="noreferrer"
              target="_blank"
            >
              Download PDF
            </a>
          </>
        ) : (
          <span className="legal-text-wrap rounded-full border border-line px-3 py-2 text-xs text-muted-foreground">
            PDF has not been generated yet. Click Generate PDF.
          </span>
        )}
      </div>

      {draft.lawyerReviewChecklist.length ? (
        <div className="mt-5 min-w-0 rounded-2xl border border-line bg-panel-highlight p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-subtle">Lawyer review checklist</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
            {draft.lawyerReviewChecklist.slice(0, 8).map((item) => (
              <li className="legal-text-wrap" key={`${run.runId}-check-${item}`}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
