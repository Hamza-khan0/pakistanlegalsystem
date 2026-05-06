import type { ReactNode } from "react";
import { FileStack, ScanLine } from "lucide-react";

import { PriorityBadge } from "@/components/common/priority-badge";
import { StatusBadge } from "@/components/common/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { CaseDocument } from "@/types";
import { formatDate } from "@/lib/utils";

interface DocumentPreviewProps {
  document: CaseDocument | null;
  action?: ReactNode;
  feedback?: ReactNode;
}

export function DocumentPreview({
  document,
  action,
  feedback,
}: DocumentPreviewProps) {
  if (!document) {
    return (
      <Card className="flex h-full min-h-[420px] items-center justify-center rounded-[30px] border-dashed bg-panel-muted/70 text-center">
        <div className="space-y-3">
          <p className="text-sm font-medium text-foreground">Select a document</p>
          <p className="max-w-xs text-sm leading-6 text-muted-foreground">
            Preview extracted content, metadata, and indexing status here.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="space-y-5 rounded-[30px] bg-panel-muted/95">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">
          Document Preview
        </p>
        <h3 className="text-xl font-semibold tracking-tight text-foreground">
          {document.name}
        </h3>
        <p className="text-sm leading-6 text-muted-foreground">{document.summary}</p>
        <div className="flex flex-wrap gap-3">
          {document.fileUrl ? (
            <a
              className={buttonVariants({ size: "sm", variant: "secondary" })}
              href={document.fileUrl}
              rel="noreferrer"
              target="_blank"
            >
              Open stored file
            </a>
          ) : null}
          {action}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <StatusBadge status={document.status} />
        <StatusBadge status={document.extractionStatus} />
        <StatusBadge status={document.intelligenceStatus} />
        {document.casePriority ? (
          <PriorityBadge priority={document.casePriority} />
        ) : null}
      </div>

      {feedback}

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
            <FileStack className="size-3.5" />
            Metadata
          </div>
          <div className="mt-3 space-y-2 text-sm text-muted-foreground">
            <p>Type: {document.type}</p>
            <p>Pages: {document.pages}</p>
            <p>Uploaded: {formatDate(document.uploadDate)}</p>
            <p>Filed by: {document.filedBy}</p>
            {document.detectedLanguage ? <p>Language: {document.detectedLanguage}</p> : null}
            {document.processedAt ? <p>Processed: {formatDate(document.processedAt)}</p> : null}
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
            <ScanLine className="size-3.5" />
            Case Link
          </div>
          <div className="mt-3 space-y-2 text-sm text-muted-foreground">
            <p>{document.caseTitle}</p>
            <p>{document.caseNumber}</p>
            <p>{document.caseForum}</p>
            {document.ocrOutcome ? <p>OCR outcome: {document.ocrOutcome}</p> : null}
            {document.ocrEngine ? <p>Engine: {document.ocrEngine}</p> : null}
            {document.ocrConfidence !== null && document.ocrConfidence !== undefined ? (
              <p>OCR confidence: {document.ocrConfidence.toFixed(2)}</p>
            ) : null}
          </div>
        </div>
      </div>

      {document.extractionError ? (
        <div className="rounded-[24px] border border-rose-400/20 bg-rose-400/8 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-rose-100">
            Processing error
          </p>
          <p className="mt-3 text-sm leading-7 text-rose-50/90">
            {document.extractionError}
          </p>
        </div>
      ) : null}

      <div className="rounded-[24px] border border-line bg-[#0f151d] p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
          Extracted Text Snapshot
        </p>
        <p className="mt-4 text-sm leading-7 text-foreground/88">
          {document.extractedText || document.previewText || "This document has not been processed yet."}
        </p>
      </div>

      {document.pageExtractions?.length ? (
        <div className="rounded-[24px] border border-line bg-white/[0.03] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
            Page extraction trace
          </p>
          <div className="mt-4 space-y-3">
            {document.pageExtractions.slice(0, 4).map((page) => (
              <div
                key={`${document.id}-page-${page.pageNumber}`}
                className="rounded-2xl border border-line bg-panel-highlight p-4"
              >
                <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                  Page {page.pageNumber} / {page.method}
                  {page.confidence !== null && page.confidence !== undefined
                    ? ` / ${page.confidence.toFixed(2)} confidence`
                    : ""}
                </p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {page.textPreview}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {document.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            {tag}
          </span>
        ))}
      </div>
    </Card>
  );
}
