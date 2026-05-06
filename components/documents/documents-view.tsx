"use client";

import type { FormEvent } from "react";
import { useDeferredValue, useMemo, useState } from "react";
import Link from "next/link";
import { FileUp, Layers3, X } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { SearchInput } from "@/components/common/search-input";
import { SectionCard } from "@/components/common/section-card";
import { DocumentPreview } from "@/components/documents/document-preview";
import { DocumentTable } from "@/components/documents/document-table";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { processDocument, uploadDocument } from "@/lib/api/client";
import type { CaseDocument, CaseMatter, DocumentType, ExtractionStatus } from "@/types";

const typeFilters: Array<DocumentType | "All"> = [
  "All",
  "Plaint",
  "Written Statement",
  "Affidavit",
  "Rejoinder",
  "Application",
  "Annexure",
  "Order Sheet",
  "Judgment",
  "Vakalatnama",
  "Brief",
];

const documentStatuses = [
  "Reference",
  "Filed",
  "Draft",
  "Under Review",
  "Pending Signature",
];

const extractionFilters: Array<ExtractionStatus | "All"> = [
  "All",
  "Parsed",
  "OCR Running",
  "Manual Review",
  "Ready for Indexing",
];

interface UploadFormState {
  caseId: string;
  name: string;
  type: DocumentType;
  status: string;
  category: string;
  tags: string;
  summary: string;
  filedBy: string;
  previewText: string;
  pages: string;
  file: File | null;
}

const emptyUploadForm: UploadFormState = {
  caseId: "",
  name: "",
  type: "Plaint",
  status: "Reference",
  category: "Primary pleading",
  tags: "",
  summary: "",
  filedBy: "",
  previewText: "",
  pages: "0",
  file: null,
};

function splitTags(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function DocumentsView({
  documents,
  cases,
  initialUploadOpen = false,
  initialCaseId = null,
}: {
  documents: CaseDocument[];
  cases: CaseMatter[];
  initialUploadOpen?: boolean;
  initialCaseId?: string | null;
}) {
  const [documentsState, setDocumentsState] = useState(documents);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<DocumentType | "All">("All");
  const [statusFilter, setStatusFilter] = useState<ExtractionStatus | "All">("All");
  const [selectedDocumentId, setSelectedDocumentId] = useState(documents[0]?.id ?? null);
  const [uploadOpen, setUploadOpen] = useState(initialUploadOpen);
  const [uploadState, setUploadState] = useState<UploadFormState>({
    ...emptyUploadForm,
    caseId: initialCaseId ?? "",
  });
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processingDocumentId, setProcessingDocumentId] = useState<string | null>(null);
  const [processFeedback, setProcessFeedback] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const deferredSearch = useDeferredValue(search);

  const filteredDocuments = useMemo(() => {
    return documentsState.filter((document) => {
      const query = deferredSearch.trim().toLowerCase();
      const matchesQuery =
        !query ||
        document.name.toLowerCase().includes(query) ||
        document.summary.toLowerCase().includes(query) ||
        document.tags.join(" ").toLowerCase().includes(query);

      const matchesType = typeFilter === "All" || document.type === typeFilter;
      const matchesStatus =
        statusFilter === "All" || document.extractionStatus === statusFilter;

      return matchesQuery && matchesType && matchesStatus;
    });
  }, [deferredSearch, documentsState, statusFilter, typeFilter]);

  const selectedDocument =
    filteredDocuments.find((document) => document.id === selectedDocumentId) ??
    documentsState.find((document) => document.id === selectedDocumentId) ??
    null;

  function openUploadForm() {
    setUploadOpen(true);
    setUploadError(null);
    setUploadSuccess(null);
  }

  function closeUploadForm() {
    setUploadOpen(false);
    setUploadError(null);
    setUploadSuccess(null);
  }

  async function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!uploadState.caseId) {
      setUploadError("Please select the matter this document belongs to.");
      setUploadSuccess(null);
      return;
    }

    if (!uploadState.file) {
      setUploadError("Please choose a file to upload.");
      setUploadSuccess(null);
      return;
    }

    if (!uploadState.name.trim()) {
      setUploadError("Please provide the document name.");
      setUploadSuccess(null);
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const uploaded = await uploadDocument({
        caseId: uploadState.caseId,
        name: uploadState.name.trim(),
        type: uploadState.type,
        status: uploadState.status,
        category: uploadState.category.trim(),
        tags: splitTags(uploadState.tags),
        summary: uploadState.summary.trim(),
        filedBy: uploadState.filedBy.trim(),
        previewText: uploadState.previewText.trim(),
        pages: Number(uploadState.pages || "0"),
        file: uploadState.file,
      });

      setDocumentsState((current) => [uploaded, ...current]);
      setSelectedDocumentId(uploaded.id);
      setProcessFeedback({
        tone: "info",
        message:
          "Document uploaded. Process it to extract text and make it usable for chamber intelligence.",
      });
      setUploadSuccess("Document uploaded and linked to the document engine.");
      setUploadState({
        ...emptyUploadForm,
        caseId: uploadState.caseId,
      });
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : "Unable to upload the document.",
      );
    } finally {
      setUploading(false);
    }
  }

  function updateUploadField<K extends keyof UploadFormState>(
    key: K,
    value: UploadFormState[K],
  ) {
    setUploadState((current) => ({ ...current, [key]: value }));
  }

  async function handleProcessDocument() {
    if (!selectedDocument) {
      setProcessFeedback({
        tone: "error",
        message: "Select a document before starting the processing pipeline.",
      });
      return;
    }

    setProcessingDocumentId(selectedDocument.id);
    setProcessFeedback({
      tone: "info",
      message: "Processing document and extracting chamber-usable text...",
    });

    try {
      const processed = await processDocument(selectedDocument.id);
      setDocumentsState((current) =>
        current.map((document) =>
          document.id === processed.id ? processed : document,
        ),
      );
      setSelectedDocumentId(processed.id);
      setProcessFeedback({
        tone: processed.intelligenceStatus === "Failed" ? "error" : "success",
        message:
          processed.intelligenceStatus === "Failed"
            ? processed.extractionError ||
              "Document processing failed and needs manual review."
            : "Document processed successfully. Extracted text is now available in the preview panel.",
      });
    } catch (error) {
      setProcessFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to process the selected document.",
      });
    } finally {
      setProcessingDocumentId(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Documents"
        title="Central document library"
        description="A chamber-grade document surface with live uploads, case association, indexing placeholders, OCR status markers, and preview-ready metadata."
        meta={[
          `${documentsState.length} live documents`,
          "Local upload pipeline",
          "Process and extract text",
        ]}
        actions={
          <>
            <Link
              className={buttonVariants({ size: "default", variant: "secondary" })}
              href="/knowledge"
            >
              Open knowledge lab
            </Link>
            <Button onClick={openUploadForm}>Upload documents</Button>
          </>
        }
      />

      <Card className="rounded-[30px] border-dashed border-accent/25 bg-[linear-gradient(180deg,rgba(142,165,194,0.08),rgba(142,165,194,0.02))]">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
              <FileUp className="size-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-foreground">
                Intake and extraction zone
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
                Upload a real filing, annexure, order sheet, or brief to the
                document engine. Metadata persists immediately, and supported
                files can now be processed into extraction-backed chamber text.
                {" "}
                <Link className="text-accent hover:text-accent-soft" href="/knowledge">
                  The broader crawl, OCR, and corpus pipeline now lives in the knowledge workspace.
                </Link>
              </p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric
              label="Processed"
              value={`${documentsState.filter((item) => item.intelligenceStatus === "Processed").length}`}
            />
            <Metric
              label="Needs review"
              value={`${documentsState.filter((item) => item.extractionStatus === "Manual Review" || item.intelligenceStatus === "Failed").length}`}
            />
            <Metric
              label="Pending processing"
              value={`${documentsState.filter((item) => item.intelligenceStatus === "Not Processed" || item.intelligenceStatus === "Processing").length}`}
            />
          </div>
        </div>

        {uploadOpen ? (
          <div className="mt-6 border-t border-line pt-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                  Upload form
                </p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  Attach a file, link it to a matter, and store the metadata in the
                  live backend.
                </p>
              </div>
              <button
                className="flex size-10 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                onClick={closeUploadForm}
                type="button"
              >
                <X className="size-4" />
              </button>
            </div>

            <form className="space-y-5" onSubmit={handleUploadSubmit}>
              {uploadError ? (
                <InlineFeedback message={uploadError} tone="error" />
              ) : null}
              {uploadSuccess ? (
                <InlineFeedback message={uploadSuccess} tone="success" />
              ) : null}

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Linked matter
                  </span>
                  <select
                    className="h-11 w-full rounded-2xl border border-line bg-white/[0.03] px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50 focus:bg-white/[0.05]"
                    value={uploadState.caseId}
                    onChange={(event) => updateUploadField("caseId", event.target.value)}
                  >
                    <option value="">Select matter</option>
                    {cases.map((caseItem) => (
                      <option key={caseItem.id} value={caseItem.id}>
                        {caseItem.caseNumber} · {caseItem.title}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Document name
                  </span>
                  <Input
                    placeholder="Interim injunction application"
                    value={uploadState.name}
                    onChange={(event) => updateUploadField("name", event.target.value)}
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    File
                  </span>
                  <Input
                    accept=".pdf,.txt,.md,.markdown,.json"
                    className="file:mr-3 file:rounded-xl file:border-0 file:bg-accent/12 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-accent"
                    type="file"
                    onChange={(event) => {
                      const nextFile = event.target.files?.[0] ?? null;
                      updateUploadField("file", nextFile);
                      if (nextFile && !uploadState.name.trim()) {
                        const inferredName = nextFile.name.replace(/\.[^/.]+$/, "");
                        updateUploadField("name", inferredName);
                      }
                    }}
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Document type
                  </span>
                  <select
                    className="h-11 w-full rounded-2xl border border-line bg-white/[0.03] px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50 focus:bg-white/[0.05]"
                    value={uploadState.type}
                    onChange={(event) =>
                      updateUploadField("type", event.target.value as DocumentType)
                    }
                  >
                    {typeFilters
                      .filter((item) => item !== "All")
                      .map((typeOption) => (
                        <option key={typeOption} value={typeOption}>
                          {typeOption}
                        </option>
                      ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Library status
                  </span>
                  <select
                    className="h-11 w-full rounded-2xl border border-line bg-white/[0.03] px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50 focus:bg-white/[0.05]"
                    value={uploadState.status}
                    onChange={(event) => updateUploadField("status", event.target.value)}
                  >
                    {documentStatuses.map((statusOption) => (
                      <option key={statusOption} value={statusOption}>
                        {statusOption}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Category
                  </span>
                  <Input
                    placeholder="Urgent application"
                    value={uploadState.category}
                    onChange={(event) =>
                      updateUploadField("category", event.target.value)
                    }
                  />
                </label>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Filed by
                  </span>
                  <Input
                    placeholder="Hamza Khan"
                    value={uploadState.filedBy}
                    onChange={(event) =>
                      updateUploadField("filedBy", event.target.value)
                    }
                  />
                </label>
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Page count
                  </span>
                  <Input
                    min="0"
                    type="number"
                    value={uploadState.pages}
                    onChange={(event) => updateUploadField("pages", event.target.value)}
                  />
                </label>
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Tags
                  </span>
                  <Input
                    placeholder="Injunction, Annexure P-3, Urgent"
                    value={uploadState.tags}
                    onChange={(event) => updateUploadField("tags", event.target.value)}
                  />
                </label>
              </div>

              <label className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                  Summary
                </span>
                <Textarea
                  placeholder="Short internal summary for the chamber document table."
                  value={uploadState.summary}
                  onChange={(event) => updateUploadField("summary", event.target.value)}
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                  Extracted text preview
                </span>
                <Textarea
                  placeholder="Optional text snapshot or first-page summary for quick preview."
                  value={uploadState.previewText}
                  onChange={(event) =>
                    updateUploadField("previewText", event.target.value)
                  }
                />
              </label>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5">
                <div className="text-sm text-muted-foreground">
                  Uploads are stored locally in Phase 3. Process a document after
                  upload to extract text and prepare it for chamber intelligence.
                </div>
                <Button disabled={uploading} type="submit">
                  {uploading ? "Uploading..." : "Upload to library"}
                </Button>
              </div>
            </form>
          </div>
        ) : null}
      </Card>

      <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SectionCard
            title="Search and filters"
            description="Refine the library by content, document type, or extraction stage."
          >
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_repeat(2,minmax(220px,1fr))]">
              <SearchInput
                placeholder="Search by name, tag, extracted concept"
                value={search}
                onChange={setSearch}
              />
              <select
                className="h-11 rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none"
                value={typeFilter}
                onChange={(event) =>
                  setTypeFilter(event.target.value as DocumentType | "All")
                }
              >
                {typeFilters.map((typeOption) => (
                  <option key={typeOption} value={typeOption}>
                    {typeOption === "All" ? "All document types" : typeOption}
                  </option>
                ))}
              </select>
              <select
                className="h-11 rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none"
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value as ExtractionStatus | "All")
                }
              >
                {extractionFilters.map((statusOption) => (
                  <option key={statusOption} value={statusOption}>
                    {statusOption === "All" ? "All extraction stages" : statusOption}
                  </option>
                ))}
              </select>
            </div>
            <div className="text-sm text-muted-foreground">
              {filteredDocuments.length} documents visible in the current index.
            </div>
          </SectionCard>

          <SectionCard
            title="Document index"
            description="Select a document to inspect the preview and extraction metadata."
            action={
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                <Layers3 className="size-3.5" />
                Multi-matter view
              </div>
            }
          >
            {filteredDocuments.length ? (
              <DocumentTable
                documents={filteredDocuments}
                selectedId={selectedDocumentId}
                onSelect={setSelectedDocumentId}
              />
            ) : (
              <EmptyState
                title="No documents match the current filters"
                description="Clear a filter or upload a new document to grow the live document index."
                action={
                  <Button onClick={openUploadForm} variant="secondary">
                    Upload a document
                  </Button>
                }
              />
            )}
          </SectionCard>
        </div>

        <DocumentPreview
          document={selectedDocument}
          action={
            selectedDocument ? (
              <Button
                onClick={handleProcessDocument}
                disabled={processingDocumentId === selectedDocument.id}
                size="sm"
                variant="outline"
              >
                {processingDocumentId === selectedDocument.id
                  ? "Processing..."
                  : selectedDocument.intelligenceStatus === "Processed"
                    ? "Reprocess document"
                    : "Process document"}
              </Button>
            ) : null
          }
          feedback={
            processFeedback ? (
              <InlineFeedback
                message={processFeedback.message}
                tone={processFeedback.tone}
              />
            ) : null
          }
        />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-line bg-panel p-4">
      <p className="text-xs uppercase tracking-[0.18em] text-subtle">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground">
        {value}
      </p>
    </div>
  );
}
