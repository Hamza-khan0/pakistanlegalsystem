"use client";

import type { FormEvent, HTMLInputTypeAttribute } from "react";
import { useDeferredValue, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { SlidersHorizontal, X } from "lucide-react";

import { CaseCard } from "@/components/cases/case-card";
import { CaseTable } from "@/components/cases/case-table";
import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { PageHeader } from "@/components/common/page-header";
import { RightPanel } from "@/components/common/right-panel";
import { SearchInput } from "@/components/common/search-input";
import { SectionCard } from "@/components/common/section-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  archiveCase,
  createCase,
  type CaseMutationInput,
  updateCase,
} from "@/lib/api/client";
import type { CaseMatter, CaseStatus, PriorityLevel } from "@/types";

const statusFilters: Array<CaseStatus | "All"> = [
  "All",
  "Active",
  "Hearing Due",
  "Awaiting Filing",
  "Research",
  "Drafting",
];

const priorityFilters: Array<PriorityLevel | "All"> = [
  "All",
  "Critical",
  "High",
  "Medium",
  "Low",
];

const matterTypes = [
  "Civil Suit",
  "Constitutional Petition",
  "Bail Matter",
  "Property Dispute",
  "Revenue Matter",
  "Service Matter",
  "Tax Petition",
  "Commercial Recovery",
];

type SortOption = "hearing" | "priority" | "title";
type NoticeTone = "success" | "error" | "info";

const priorityRank: Record<PriorityLevel, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
};

interface CaseFormState {
  title: string;
  caseNumber: string;
  forum: string;
  matterType: string;
  status: CaseStatus;
  priority: PriorityLevel;
  client: string;
  opposingParty: string;
  summary: string;
  nextHearingDate: string;
  stage: string;
  assignedCounsel: string;
  issues: string;
  reliefSought: string;
  riskFlags: string;
  tags: string;
  importantNotes: string;
}

const emptyCaseForm: CaseFormState = {
  title: "",
  caseNumber: "",
  forum: "",
  matterType: "Civil Suit",
  status: "Active",
  priority: "Medium",
  client: "",
  opposingParty: "",
  summary: "",
  nextHearingDate: "",
  stage: "",
  assignedCounsel: "",
  issues: "",
  reliefSought: "",
  riskFlags: "",
  tags: "",
  importantNotes: "",
};

function splitList(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toDateInputValue(value: string | undefined) {
  return value ? value.slice(0, 10) : "";
}

function toCaseFormState(caseItem?: CaseMatter): CaseFormState {
  if (!caseItem) {
    return emptyCaseForm;
  }

  return {
    title: caseItem.title,
    caseNumber: caseItem.caseNumber,
    forum: caseItem.forum,
    matterType: caseItem.matterType,
    status: caseItem.status,
    priority: caseItem.priority,
    client: caseItem.client,
    opposingParty: caseItem.opposingParty,
    summary: caseItem.summary,
    nextHearingDate: toDateInputValue(caseItem.nextHearingDate),
    stage: caseItem.stage,
    assignedCounsel: caseItem.assignedCounsel.join(", "),
    issues: caseItem.issues.join(", "),
    reliefSought: caseItem.reliefSought.join("\n"),
    riskFlags: caseItem.riskFlags.join(", "),
    tags: caseItem.tags.join(", "),
    importantNotes: caseItem.importantNotes.join("\n"),
  };
}

function buildCaseInput(formState: CaseFormState): CaseMutationInput {
  return {
    title: formState.title.trim(),
    caseNumber: formState.caseNumber.trim(),
    forum: formState.forum.trim(),
    matterType: formState.matterType.trim(),
    status: formState.status,
    priority: formState.priority,
    client: formState.client.trim(),
    opposingParty: formState.opposingParty.trim(),
    summary: formState.summary.trim(),
    nextHearingDate: formState.nextHearingDate || null,
    stage: formState.stage.trim(),
    assignedCounsel: splitList(formState.assignedCounsel),
    issues: splitList(formState.issues),
    reliefSought: splitList(formState.reliefSought),
    riskFlags: splitList(formState.riskFlags),
    tags: splitList(formState.tags),
    importantNotes: splitList(formState.importantNotes),
  };
}

function validateCaseForm(formState: CaseFormState) {
  const requiredFields = [
    ["title", formState.title],
    ["facts / case summary", formState.summary],
  ] as const;

  const missing = requiredFields.find(([, value]) => !value.trim());
  if (missing) {
    return `Please provide the ${missing[0]}.`;
  }

  return null;
}

export function CasesView({
  cases,
  initialMode = null,
  initialEditCaseId = null,
}: {
  cases: CaseMatter[];
  initialMode?: "create" | "edit" | null;
  initialEditCaseId?: string | null;
}) {
  const router = useRouter();
  const initialEditCase = initialEditCaseId
    ? cases.find((caseItem) => caseItem.id === initialEditCaseId) ?? null
    : null;

  const [casesState, setCasesState] = useState(cases);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<CaseStatus | "All">("All");
  const [priorityFilter, setPriorityFilter] = useState<PriorityLevel | "All">("All");
  const [sort, setSort] = useState<SortOption>("hearing");
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(initialMode);
  const [editingCaseId, setEditingCaseId] = useState<string | null>(
    initialEditCase?.id ?? null,
  );
  const [formState, setFormState] = useState<CaseFormState>(
    initialEditCase ? toCaseFormState(initialEditCase) : emptyCaseForm,
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [pageNotice, setPageNotice] = useState<{
    tone: NoticeTone;
    message: string;
  } | null>(null);
  const [saving, setSaving] = useState(false);
  const [archiving, setArchiving] = useState(false);

  const deferredSearch = useDeferredValue(search);

  const filteredCases = useMemo(() => {
    return casesState
      .filter((caseItem) => {
        const query = deferredSearch.trim().toLowerCase();
        const matchesQuery =
          !query ||
          caseItem.title.toLowerCase().includes(query) ||
          caseItem.client.toLowerCase().includes(query) ||
          caseItem.caseNumber.toLowerCase().includes(query) ||
          caseItem.forum.toLowerCase().includes(query);

        const matchesStatus =
          statusFilter === "All" || caseItem.status === statusFilter;
        const matchesPriority =
          priorityFilter === "All" || caseItem.priority === priorityFilter;

        return matchesQuery && matchesStatus && matchesPriority;
      })
      .sort((left, right) => {
        if (sort === "priority") {
          return priorityRank[left.priority] - priorityRank[right.priority];
        }

        if (sort === "title") {
          return left.title.localeCompare(right.title);
        }

        return +new Date(left.nextHearingDate) - +new Date(right.nextHearingDate);
      });
  }, [casesState, deferredSearch, priorityFilter, sort, statusFilter]);

  const editingCase = editingCaseId
    ? casesState.find((caseItem) => caseItem.id === editingCaseId) ?? null
    : null;

  function openCreateForm() {
    setFormMode("create");
    setEditingCaseId(null);
    setFormState(emptyCaseForm);
    setFormError(null);
    setFormSuccess(null);
  }

  function openEditForm(caseItem: CaseMatter) {
    setFormMode("edit");
    setEditingCaseId(caseItem.id);
    setFormState(toCaseFormState(caseItem));
    setFormError(null);
    setFormSuccess(null);
  }

  function closeForm() {
    setFormMode(null);
    setEditingCaseId(null);
    setFormState(emptyCaseForm);
    setFormError(null);
    setFormSuccess(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const shouldResearch = submitter?.dataset.intent === "research";

    const validationMessage = validateCaseForm(formState);
    if (validationMessage) {
      setFormError(validationMessage);
      setFormSuccess(null);
      return;
    }

    setSaving(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      if (formMode === "edit" && editingCaseId) {
        const updatedCase = await updateCase(editingCaseId, buildCaseInput(formState));
        setCasesState((current) =>
          current.map((caseItem) =>
            caseItem.id === updatedCase.id ? updatedCase : caseItem,
          ),
        );
        setFormSuccess("Matter updated successfully.");
        setPageNotice({
          tone: "success",
          message: `${updatedCase.title} is now updated across the chamber view.`,
        });
      } else {
        const createdCase = await createCase(buildCaseInput(formState));
        setCasesState((current) => [createdCase, ...current]);
        setFormState(emptyCaseForm);
        setFormSuccess("Case created successfully.");
        setPageNotice({
          tone: "success",
          message: `${createdCase.title} is now saved and ready for Research & Draft.`,
        });
        router.push(`/cases/${createdCase.id}${shouldResearch ? "?research=1" : ""}`);
      }
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Unable to save the matter.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive() {
    if (!editingCaseId || !editingCase) {
      return;
    }

    setArchiving(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      await archiveCase(editingCaseId);
      setCasesState((current) =>
        current.filter((caseItem) => caseItem.id !== editingCaseId),
      );
      closeForm();
      setPageNotice({
        tone: "success",
        message: `${editingCase.title} has been archived from the active portfolio.`,
      });
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Unable to archive the matter.",
      );
    } finally {
      setArchiving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Cases"
        title="Cases"
        description="Create a case, open its workspace, and run Research & Draft from one clear place."
        meta={[
          `${casesState.length} saved cases`,
          "Court-aware statuses",
          "Research & Draft ready",
        ]}
        actions={<Button onClick={openCreateForm}>+ New Case</Button>}
      />

      {pageNotice ? (
        <InlineFeedback
          message={pageNotice.message}
          tone={pageNotice.tone}
        />
      ) : null}

      {formMode ? (
        <SectionCard
          title={formMode === "create" ? "New Case" : "Edit Case"}
          description={
            formMode === "create"
              ? "Only title and facts are required. Extra court, party, and relief details improve research quality."
              : "Update the saved case record, or archive it from the active portfolio."
          }
          action={
            <button
              className="flex size-10 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
              onClick={closeForm}
              type="button"
            >
              <X className="size-4" />
            </button>
          }
        >
          <form className="space-y-5" onSubmit={handleSubmit}>
            {formError ? (
              <InlineFeedback message={formError} tone="error" />
            ) : null}
            {formSuccess ? (
              <InlineFeedback message={formSuccess} tone="success" />
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              <Field
                label="Case title"
                value={formState.title}
                onChange={(value) => setFormState((current) => ({ ...current, title: value }))}
                placeholder="Green Valley Cooperative Housing Society v LDA"
              />
              <Field
                label="Case number"
                value={formState.caseNumber}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, caseNumber: value }))
                }
                placeholder="W.P. No. 2145/2026"
              />
              <Field
                label="Forum"
                value={formState.forum}
                onChange={(value) => setFormState((current) => ({ ...current, forum: value }))}
                placeholder="Lahore High Court, Lahore"
              />
              <SelectField
                label="Matter type"
                value={formState.matterType}
                options={matterTypes}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, matterType: value }))
                }
              />
              <SelectField
                label="Status"
                value={formState.status}
                options={statusFilters.filter((item) => item !== "All")}
                onChange={(value) =>
                  setFormState((current) => ({
                    ...current,
                    status: value as CaseStatus,
                  }))
                }
              />
              <SelectField
                label="Priority"
                value={formState.priority}
                options={priorityFilters.filter((item) => item !== "All")}
                onChange={(value) =>
                  setFormState((current) => ({
                    ...current,
                    priority: value as PriorityLevel,
                  }))
                }
              />
              <Field
                label="Client name"
                value={formState.client}
                onChange={(value) => setFormState((current) => ({ ...current, client: value }))}
                placeholder="Green Valley Cooperative Housing Society"
              />
              <Field
                label="Opposing party"
                value={formState.opposingParty}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, opposingParty: value }))
                }
                placeholder="Lahore Development Authority"
              />
              <Field
                label="Next hearing date"
                type="date"
                value={formState.nextHearingDate}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, nextHearingDate: value }))
                }
              />
              <Field
                label="Filing stage"
                value={formState.stage}
                onChange={(value) => setFormState((current) => ({ ...current, stage: value }))}
                placeholder="Interim injunction application pending"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Field
                label="Assigned counsel"
                value={formState.assignedCounsel}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, assignedCounsel: value }))
                }
                placeholder="Hamza Khan, Areeba Malik"
              />
              <Field
                label="Tags"
                value={formState.tags}
                onChange={(value) => setFormState((current) => ({ ...current, tags: value }))}
                placeholder="Maintainability, Urgent Relief, Property"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Field
                label="Legal issues"
                value={formState.issues}
                onChange={(value) => setFormState((current) => ({ ...current, issues: value }))}
                placeholder="Alternate remedy, cancellation without notice"
              />
              <Field
                label="Risk flags"
                value={formState.riskFlags}
                onChange={(value) =>
                  setFormState((current) => ({ ...current, riskFlags: value }))
                }
                placeholder="Sanctioned plan still missing, urgency scrutiny"
              />
            </div>

            <TextAreaField
              label="Facts / case summary"
              value={formState.summary}
              onChange={(value) => setFormState((current) => ({ ...current, summary: value }))}
              placeholder="Summarize the matter posture, core dispute, and why the file needs attention."
            />
            <TextAreaField
              label="Relief sought"
              value={formState.reliefSought}
              onChange={(value) =>
                setFormState((current) => ({ ...current, reliefSought: value }))
              }
              placeholder={"Permanent injunction\nSuspension of cancellation letter"}
            />
            <TextAreaField
              label="Important notes"
              value={formState.importantNotes}
              onChange={(value) =>
                setFormState((current) => ({ ...current, importantNotes: value }))
              }
              placeholder="Internal matter reminders and context for the next hearing."
            />

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5">
              <div className="text-sm text-muted-foreground">
                Required: case title and facts. Other fields can be filled later.
              </div>
              <div className="flex flex-wrap gap-3">
                {formMode === "edit" ? (
                  <Button
                    disabled={saving || archiving}
                    onClick={handleArchive}
                    type="button"
                    variant="outline"
                  >
                    {archiving ? "Archiving..." : "Archive matter"}
                  </Button>
                ) : null}
                <Button
                  disabled={saving}
                  type="submit"
                  variant={formMode === "edit" ? "secondary" : "default"}
                >
                  {saving
                    ? formMode === "edit"
                      ? "Saving changes..."
                      : "Creating matter..."
                    : formMode === "edit"
                      ? "Save changes"
                      : "Save Case"}
                </Button>
                {formMode === "create" ? (
                  <Button
                    data-intent="research"
                    disabled={saving}
                    type="submit"
                    variant="secondary"
                  >
                    {saving ? "Saving..." : "Save & Research"}
                  </Button>
                ) : null}
              </div>
            </div>
          </form>
        </SectionCard>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <Card className="space-y-5">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
              <SlidersHorizontal className="size-4" />
              Search and filters
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
              <SearchInput
                placeholder="Search by title, case number, party, forum"
                value={search}
                onChange={setSearch}
              />

              <select
                className="h-11 rounded-2xl border border-line bg-panel px-4 text-sm text-foreground outline-none"
                value={sort}
                onChange={(event) => setSort(event.target.value as SortOption)}
              >
                <option value="hearing">Sort by hearing date</option>
                <option value="priority">Sort by priority</option>
                <option value="title">Sort alphabetically</option>
              </select>
            </div>

            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
                Status
              </p>
              <div className="flex flex-wrap gap-2">
                {statusFilters.map((status) => (
                  <button
                    key={status}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] transition-colors ${
                      status === statusFilter
                        ? "border-accent/40 bg-accent/10 text-accent"
                        : "border-line text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => setStatusFilter(status)}
                    type="button"
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
                Priority
              </p>
              <div className="flex flex-wrap gap-2">
                {priorityFilters.map((priority) => (
                  <button
                    key={priority}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] transition-colors ${
                      priority === priorityFilter
                        ? "border-accent/40 bg-accent/10 text-accent"
                        : "border-line text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => setPriorityFilter(priority)}
                    type="button"
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              Showing{" "}
              <span className="font-semibold text-foreground">
                {filteredCases.length}
              </span>{" "}
              matters ready for review.
            </div>
          </Card>

          {filteredCases.length ? (
            <>
              <div className="hidden xl:block">
                <CaseTable cases={filteredCases} onEdit={openEditForm} />
              </div>

              <div className="grid gap-4 xl:hidden">
                {filteredCases.map((caseItem) => (
                  <CaseCard
                    key={caseItem.id}
                    caseItem={caseItem}
                    onEdit={openEditForm}
                  />
                ))}
              </div>
            </>
          ) : (
            <EmptyState
              title="No matters match the current filters"
              description="Try widening the search, clearing a filter, or create a fresh matter intake."
              action={
                <Button onClick={openCreateForm} variant="secondary">
                  + New Case
                </Button>
              }
            />
          )}
        </div>

        <RightPanel
          title="Portfolio intelligence"
          description="Quick signals across the active matter book."
          sections={[
            {
              title: "Operational status",
              items: [
                {
                  label: "Live matter mutations",
                  value: "Enabled",
                  tone: "success",
                  detail:
                    "New matters, edits, and archival now persist against the backend case registry.",
                },
                {
                  label: "Export docket view",
                  value: "Coming soon",
                  detail:
                    "Export workflows are intentionally deferred so there are no dead controls in this phase.",
                },
              ],
            },
            {
              title: "Current working set",
              items: [
                {
                  label: "Visible matters",
                  value: `${filteredCases.length}`,
                  detail:
                    "This count responds to the current search, status filter, priority filter, and sort order.",
                },
                {
                  label: "Editing context",
                  value: formMode === "edit" && editingCase ? "Open" : "Idle",
                  detail:
                    formMode === "edit" && editingCase
                      ? `${editingCase.title} is loaded in the matter editor.`
                      : "Open a matter editor from the list to update live case data.",
                },
              ],
            },
          ]}
        />
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: HTMLInputTypeAttribute;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
        {label}
      </span>
      <Input
        placeholder={placeholder}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
        {label}
      </span>
      <select
        className="h-11 w-full rounded-2xl border border-line bg-white/[0.03] px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50 focus:bg-white/[0.05]"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
        {label}
      </span>
      <Textarea
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
