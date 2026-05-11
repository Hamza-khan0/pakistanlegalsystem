"use client";

import type { FormEvent, HTMLInputTypeAttribute } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowUpRight, Scale, Sparkles, X } from "lucide-react";

import { ChamberRunPanel } from "@/components/chamber/chamber-run-panel";
import { TimelineList } from "@/components/cases/timeline-list";
import { AvatarStack } from "@/components/common/avatar-stack";
import { EmptyState } from "@/components/common/empty-state";
import { InlineFeedback } from "@/components/common/inline-feedback";
import { LegalSourceList } from "@/components/common/legal-source-list";
import { PriorityBadge } from "@/components/common/priority-badge";
import { RightPanel } from "@/components/common/right-panel";
import { SectionCard } from "@/components/common/section-card";
import { StatusBadge } from "@/components/common/status-badge";
import { DocumentPreview } from "@/components/documents/document-preview";
import { DocumentTable } from "@/components/documents/document-table";
import { EditableDraftCard } from "@/components/research/editable-draft-card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  createAgentLog,
  createCaseRun,
  createDraft,
  createNote,
  createResearchEntry,
  createTimelineEvent,
  type AgentLogMutationInput,
  generateCaseIssues,
  generateCaseSummary,
  generateDraftAssistance,
  generateResearchNote,
  getCaseDetail,
  getCaseQualitySummary,
  getCasePredictionExplanations,
  getResearchHealth,
  getResearchMarkdownUrl,
  getResearchPdfUrl,
  getResearchRun,
  getRun,
  listCaseResearchRuns,
  predictCase,
  runCaseResearchDraft,
  updateDraft,
  updateNote,
} from "@/lib/api/client";
import type {
  AgentOutput,
  CaseQualitySummary,
  CasePrediction,
  PredictionExplanation,
  CaseDocument,
  CaseMatter,
  ChamberRun,
  ChamberRunSummary,
  ChamberTaskType,
  DatasetReadiness,
  DraftArtifact,
  IntelligenceArtifact,
  GroundingSource,
  NoteEntry,
  ResearchWorkflowResponse,
  RetrievedLegalSource,
  ResearchHealth,
  ResearchNote,
  TimelineEntry,
} from "@/types";
import { formatDate } from "@/lib/utils";

const tabs = [
  { value: "overview", label: "Overview" },
  { value: "facts", label: "Facts" },
  { value: "documents", label: "Documents" },
  { value: "timeline", label: "Timeline" },
  { value: "research", label: "Research" },
  { value: "drafts", label: "Drafts" },
  { value: "agent-output", label: "Agent Output" },
];

const noteTypes = [
  "Internal Note",
  "Client Note",
  "Strategy Note",
  "Hearing Note",
];

const timelineTypes = [
  "Filing",
  "Hearing",
  "Notice",
  "Research",
  "Draft",
  "Order",
];

const researchStatuses = ["Fresh", "Verified", "Needs Review"];
const draftStatuses = ["Drafting", "Reviewing", "Ready for Filing"];
const agentStatuses = ["Queued", "Running", "Completed", "Needs Review", "Failed"];
const chamberTaskTypes: Array<{ value: ChamberTaskType; label: string }> = [
  { value: "summary", label: "Matter summary" },
  { value: "issue_spotting", label: "Issue spotting" },
  { value: "preliminary_objections", label: "Preliminary objections" },
  { value: "hearing_notes", label: "Hearing notes" },
  { value: "draft_outline", label: "Draft outline" },
  { value: "draft_review", label: "Draft review" },
  { value: "research_memo", label: "Research memo" },
  { value: "procedural_check", label: "Procedural check" },
];

interface CaseDetailViewProps {
  caseItem: CaseMatter;
  documents: CaseDocument[];
  timeline: TimelineEntry[];
  notes: NoteEntry[];
  research: ResearchNote[];
  intelligence: IntelligenceArtifact[];
  agentOutputs: AgentOutput[];
  runs: ChamberRunSummary[];
  legalBasis: GroundingSource[];
  predictions: CasePrediction[];
  predictionExplanations: PredictionExplanation[];
  datasetReadiness: DatasetReadiness[];
  caseQualitySummary: CaseQualitySummary | null;
}

interface NoteFormState {
  title: string;
  noteType: string;
  author: string;
  content: string;
}

interface TimelineFormState {
  title: string;
  type: string;
  actor: string;
  date: string;
  description: string;
}

interface ResearchFormState {
  title: string;
  status: string;
  author: string;
  sourceType: string;
  query: string;
  citations: string;
  summary: string;
  nextQuestion: string;
}

interface DraftFormState {
  title: string;
  type: string;
  status: string;
  owner: string;
  version: string;
  summary: string;
  content: string;
}

interface AgentLogFormState {
  agentName: string;
  title: string;
  taskType: string;
  status: string;
  confidenceScore: string;
  inputSummary: string;
  outputSummary: string;
  citations: string;
  nextAction: string;
}

interface DraftAssistFormState {
  draftType: string;
  instructions: string;
}

interface ResearchGenerationFormState {
  issue: string;
  instructions: string;
}

interface ResearchWorkflowOptions {
  useLiveWeb: boolean;
  useLlm: boolean;
  generateFullDraft: boolean;
  draftType: string;
  maxSources: string;
  maxLiveSources: string;
}

interface ChamberRunFormState {
  instruction: string;
  taskType: ChamberTaskType | "";
}

const emptyNoteForm: NoteFormState = {
  title: "",
  noteType: "Internal Note",
  author: "",
  content: "",
};

const emptyTimelineForm: TimelineFormState = {
  title: "",
  type: "Filing",
  actor: "",
  date: "",
  description: "",
};

const emptyResearchForm: ResearchFormState = {
  title: "",
  status: "Fresh",
  author: "",
  sourceType: "Internal Research",
  query: "",
  citations: "",
  summary: "",
  nextQuestion: "",
};

const emptyDraftForm: DraftFormState = {
  title: "",
  type: "Written statement",
  status: "Drafting",
  owner: "",
  version: "1",
  summary: "",
  content: "",
};

const emptyAgentForm: AgentLogFormState = {
  agentName: "Research Agent",
  title: "",
  taskType: "Authority review",
  status: "Completed",
  confidenceScore: "0.82",
  inputSummary: "",
  outputSummary: "",
  citations: "",
  nextAction: "",
};

const emptyDraftAssistForm: DraftAssistFormState = {
  draftType: "Preliminary objections outline",
  instructions: "",
};

const emptyResearchGenerationForm: ResearchGenerationFormState = {
  issue: "",
  instructions: "",
};

const defaultResearchWorkflowOptions: ResearchWorkflowOptions = {
  useLiveWeb: false,
  useLlm: false,
  generateFullDraft: true,
  draftType: "auto",
  maxSources: "12",
  maxLiveSources: "8",
};

const researchDraftTypeOptions = [
  "auto",
  "writ_petition",
  "plaint",
  "injunction_application",
  "bail_application",
  "legal_notice",
  "written_statement",
  "research_memo",
];

const emptyChamberRunForm: ChamberRunFormState = {
  instruction: "",
  taskType: "",
};

function splitList(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function sortTimelineEntries(entries: TimelineEntry[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.date) - +new Date(left.date),
  );
}

function sortNotes(entries: NoteEntry[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.updatedAt) - +new Date(left.updatedAt),
  );
}

function sortResearchEntries(entries: ResearchNote[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.updatedAt) - +new Date(left.updatedAt),
  );
}

function sortDrafts(entries: DraftArtifact[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.updatedAt) - +new Date(left.updatedAt),
  );
}

function sortIntelligence(entries: IntelligenceArtifact[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.updatedAt) - +new Date(left.updatedAt),
  );
}

function sortAgentOutputs(entries: AgentOutput[]) {
  return [...entries].sort(
    (left, right) => +new Date(right.generatedAt) - +new Date(left.generatedAt),
  );
}

function toNoteFormState(note?: NoteEntry): NoteFormState {
  if (!note) {
    return emptyNoteForm;
  }

  return {
    title: note.title,
    noteType: note.noteType,
    author: note.author,
    content: note.content,
  };
}

function toDraftFormState(draft?: DraftArtifact): DraftFormState {
  if (!draft) {
    return emptyDraftForm;
  }

  return {
    title: draft.title,
    type: draft.type,
    status: draft.status,
    owner: draft.owner,
    version: String(draft.version ?? 1),
    summary: draft.summary,
    content: draft.content ?? "",
  };
}

function mergeUniqueStrings(...collections: Array<string[] | undefined>) {
  const seen = new Set<string>();
  const items: string[] = [];
  collections.forEach((collection) => {
    collection?.forEach((item) => {
      const value = item.trim();
      if (!value) {
        return;
      }
      const key = value.toLowerCase();
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      items.push(value);
    });
  });
  return items;
}

function sourceGroupCount(value: unknown) {
  if (Array.isArray(value)) {
    return value.length;
  }
  return typeof value === "number" ? value : 0;
}

function sourceGroupEntries(
  groups: ResearchWorkflowResponse["sourcesByOrigin"],
): Array<[string, RetrievedLegalSource[]]> {
  return Object.entries(groups).map(([origin, value]) => [
    origin,
    Array.isArray(value)
      ? value.map((source) => {
          const raw = source as RetrievedLegalSource & Record<string, unknown>;
          return {
            ...source,
            id: source.id ?? (typeof raw.source_id === "string" ? raw.source_id : null),
            sourceType:
              source.sourceType ??
              (typeof raw.source_type === "string" ? raw.source_type : "unknown"),
            relevanceScore:
              source.relevanceScore ??
              (typeof raw.relevance_score === "number" ? raw.relevance_score : null),
            retrievalMethod:
              source.retrievalMethod ??
              (typeof raw.retrieval_method === "string" ? raw.retrieval_method : null),
            sourceOrigin:
              source.sourceOrigin ??
              (typeof raw.source_origin === "string" ? raw.source_origin : origin),
            sourceProvider:
              source.sourceProvider ??
              (typeof raw.source_provider === "string" ? raw.source_provider : null),
            localPath:
              source.localPath ??
              (typeof raw.local_path === "string" ? raw.local_path : null),
          };
        })
      : [],
  ]);
}

function providerValue(status: Record<string, unknown>, key: string) {
  const value = status[key];
  if (value === null || value === undefined) {
    return "not reported";
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function readStringList(
  artifact: IntelligenceArtifact | undefined,
  key: string,
): string[] {
  const candidate = artifact?.structuredJson[key];
  return Array.isArray(candidate)
    ? candidate.filter((item): item is string => typeof item === "string")
    : [];
}

export function CaseDetailView({
  caseItem,
  documents,
  timeline,
  notes,
  research,
  intelligence,
  agentOutputs,
  runs,
  legalBasis,
  predictions,
  predictionExplanations,
  datasetReadiness,
  caseQualitySummary,
}: CaseDetailViewProps) {
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState(
    searchParams.get("research") === "1" || searchParams.get("runs") === "1"
      ? "research"
      : "overview",
  );
  const [caseState, setCaseState] = useState(caseItem);
  const [documentsState] = useState(documents);
  const [timelineState, setTimelineState] = useState(sortTimelineEntries(timeline));
  const [notesState, setNotesState] = useState(sortNotes(notes));
  const [researchState, setResearchState] = useState(sortResearchEntries(research));
  const [draftsState, setDraftsState] = useState(sortDrafts(caseItem.draftArtifacts));
  const [intelligenceState, setIntelligenceState] = useState(
    sortIntelligence(intelligence),
  );
  const [agentOutputsState, setAgentOutputsState] = useState(
    sortAgentOutputs(agentOutputs),
  );
  const [legalBasisState, setLegalBasisState] = useState(legalBasis);
  const [predictionsState, setPredictionsState] = useState(predictions);
  const [predictionExplanationsState, setPredictionExplanationsState] = useState(
    predictionExplanations,
  );
  const [caseQualitySummaryState, setCaseQualitySummaryState] = useState(caseQualitySummary);
  const [runsState, setRunsState] = useState<ChamberRunSummary[]>(runs);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(runs[0]?.id ?? null);
  const [selectedRun, setSelectedRun] = useState<ChamberRun | null>(null);
  const [runFormOpen, setRunFormOpen] = useState(false);
  const [runForm, setRunForm] = useState<ChamberRunFormState>(emptyChamberRunForm);
  const [runSaving, setRunSaving] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runDetailLoading, setRunDetailLoading] = useState(Boolean(runs[0]?.id));
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(
    documentsState[0]?.id ?? null,
  );
  const [pageNotice, setPageNotice] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);
  const [predicting, setPredicting] = useState(false);

  const [noteEditor, setNoteEditor] = useState<{
    mode: "create" | "edit";
    noteId?: string;
  } | null>(null);
  const [noteForm, setNoteForm] = useState<NoteFormState>(emptyNoteForm);
  const [noteSaving, setNoteSaving] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);

  const [timelineOpen, setTimelineOpen] = useState(false);
  const [timelineForm, setTimelineForm] = useState<TimelineFormState>(emptyTimelineForm);
  const [timelineSaving, setTimelineSaving] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);

  const [researchOpen, setResearchOpen] = useState(false);
  const [researchForm, setResearchForm] = useState<ResearchFormState>(emptyResearchForm);
  const [researchSaving, setResearchSaving] = useState(false);
  const [researchError, setResearchError] = useState<string | null>(null);
  const [researchWorkflowRuns, setResearchWorkflowRuns] = useState<
    ResearchWorkflowResponse[]
  >([]);
  const [researchWorkflowLoading, setResearchWorkflowLoading] = useState(false);
  const [researchWorkflowSaving, setResearchWorkflowSaving] = useState(false);
  const [researchWorkflowError, setResearchWorkflowError] = useState<string | null>(
    null,
  );
  const [researchHealth, setResearchHealth] = useState<ResearchHealth | null>(null);
  const [researchWorkflowOptions, setResearchWorkflowOptions] =
    useState<ResearchWorkflowOptions>(defaultResearchWorkflowOptions);

  const [draftEditor, setDraftEditor] = useState<{
    mode: "create" | "edit";
    draftId?: string;
  } | null>(null);
  const [draftForm, setDraftForm] = useState<DraftFormState>(emptyDraftForm);
  const [draftSaving, setDraftSaving] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);

  const [agentOpen, setAgentOpen] = useState(false);
  const [agentForm, setAgentForm] = useState<AgentLogFormState>(emptyAgentForm);
  const [agentSaving, setAgentSaving] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [summaryGenerating, setSummaryGenerating] = useState(false);
  const [issuesGenerating, setIssuesGenerating] = useState(false);
  const [draftAssistOpen, setDraftAssistOpen] = useState(false);
  const [draftAssistForm, setDraftAssistForm] = useState<DraftAssistFormState>(
    emptyDraftAssistForm,
  );
  const [draftAssistSaving, setDraftAssistSaving] = useState(false);
  const [draftAssistError, setDraftAssistError] = useState<string | null>(null);
  const [researchGenerationOpen, setResearchGenerationOpen] = useState(false);
  const [researchGenerationForm, setResearchGenerationForm] =
    useState<ResearchGenerationFormState>({
      ...emptyResearchGenerationForm,
      issue: caseItem.issues[0] ?? "",
    });
  const [researchGenerationSaving, setResearchGenerationSaving] = useState(false);
  const [researchGenerationError, setResearchGenerationError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }

    let cancelled = false;

    void getRun(selectedRunId)
      .then((run) => {
        if (!cancelled) {
          setRunError(null);
          setSelectedRun(run);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setRunError(
            error instanceof Error
              ? error.message
              : "Unable to load the selected chamber run.",
          );
          setSelectedRun(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setRunDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve()
      .then(() => {
        if (!cancelled) {
          setResearchWorkflowLoading(true);
        }
        return Promise.all([
          getResearchHealth().catch(() => null),
          listCaseResearchRuns(caseItem.id),
        ]);
      })
      .then(async ([health, runs]) => {
        const detailedRuns = await Promise.all(
          runs.slice(0, 3).map((run) => getResearchRun(run.runId).catch(() => null)),
        );
        if (!cancelled) {
          if (health) {
            setResearchHealth(health);
            setResearchWorkflowOptions((current) => ({
              ...current,
              useLiveWeb: health.liveWebSearchAvailable,
              useLlm: health.llmAvailable,
            }));
          }
          setResearchWorkflowRuns(
            detailedRuns.filter((run): run is ResearchWorkflowResponse => Boolean(run)),
          );
          setResearchWorkflowError(null);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setResearchWorkflowError(
            error instanceof Error
              ? error.message
              : "Unable to load research workflow runs.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setResearchWorkflowLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [caseItem.id]);

  async function refreshCaseWorkspace() {
    const [detail, qualitySummary] = await Promise.all([
      getCaseDetail(caseState.id),
      getCaseQualitySummary(caseState.id).catch(() => null),
    ]);
    setCaseState(detail.caseItem);
    setTimelineState(sortTimelineEntries(detail.timeline));
    setNotesState(sortNotes(detail.notes));
    setResearchState(sortResearchEntries(detail.research));
    setDraftsState(sortDrafts(detail.drafts));
    setIntelligenceState(sortIntelligence(detail.intelligence));
    setAgentOutputsState(sortAgentOutputs(detail.agentOutputs));
    setLegalBasisState(detail.legalBasis);
    setRunsState(detail.runs);
    setCaseQualitySummaryState(qualitySummary);
    return detail;
  }

  const selectedDocument =
    documentsState.find((document) => document.id === selectedDocumentId) ?? null;

  const summaryArtifacts = intelligenceState.filter(
    (artifact) =>
      artifact.artifactType === "Factual Summary" ||
      artifact.artifactType === "Procedural Summary",
  );
  const issueArtifacts = intelligenceState.filter(
    (artifact) =>
      artifact.artifactType === "Issue Spotting" ||
      artifact.artifactType === "Risk Assessment",
  );
  const draftIntelligence = intelligenceState.filter((artifact) =>
    [
      "Draft Outline",
      "Preliminary Objections",
      "Petition Skeleton",
      "Reply Skeleton",
      "Hearing Note",
      "Case Memo",
      "Strategy Note",
    ].includes(artifact.artifactType),
  );
  const generatedResearchArtifacts = intelligenceState.filter(
    (artifact) => artifact.artifactType === "Research Note",
  );

  const intelligenceSections = [
    {
      title: "Risk flags",
      items: caseState.riskFlags.length
        ? caseState.riskFlags.map((flag, index) => ({
            id: `flag-${index}`,
            label: flag,
            value: "Watch",
            tone: "warning" as const,
          }))
        : [
            {
              id: "flag-empty",
              label: "No immediate risk flags recorded",
              value: "Clear",
              tone: "success" as const,
            },
          ],
    },
    {
      title: "Procedural reminders",
      items: caseState.proceduralAlerts.length
        ? caseState.proceduralAlerts.map((alert, index) => ({
            id: `alert-${index}`,
            label: alert,
            value: "Open",
          }))
        : [
            {
              id: "alert-empty",
              label: "No procedural reminders stored",
              value: "Stable",
              tone: "success" as const,
            },
          ],
    },
    {
      title: "Legal basis",
      items: legalBasisState.length
        ? legalBasisState.slice(0, 3).map((source) => ({
            id: `${source.sourceId}-${source.chunkId ?? "source"}`,
            label: source.citationLabel || source.title,
            value: source.usageType,
            detail: source.excerpt,
          }))
        : [
            {
              id: "legal-basis-empty",
              label: "No grounded legal basis stored yet",
              value: "Idle",
            },
          ],
    },
    {
      title: "Recent reasoning",
      items: intelligenceState.length
        ? intelligenceState.slice(0, 2).map((artifact) => ({
            id: artifact.id,
            label: artifact.title,
            value: artifact.status,
            detail:
              typeof artifact.structuredJson.nextAction === "string"
                ? artifact.structuredJson.nextAction
                : artifact.source,
          }))
        : [
          {
              id: "reasoning-empty",
              label: "No agent logs have been recorded yet",
              value: "Idle",
            },
          ],
    },
    {
      title: "Chamber quality",
      items: caseQualitySummaryState
        ? [
            {
              id: `${caseQualitySummaryState.caseId}-quality`,
              label: `Grounded runs ${caseQualitySummaryState.groundedRunCount}/${caseQualitySummaryState.recentRunCount}`,
              value:
                caseQualitySummaryState.latestRunQuality?.groundingStrength?.toUpperCase() ??
                "NO RUNS",
              detail:
                caseQualitySummaryState.qualityWarnings[0] ??
                "Latest chamber runs remain critic-reviewed and grounded.",
              tone:
                caseQualitySummaryState.criticalWarningCount > 0
                  ? ("warning" as const)
                  : ("success" as const),
            },
          ]
        : [
            {
              id: "quality-summary-empty",
              label: "No case quality summary available yet",
              value: "Idle",
            },
          ],
    },
  ];

  function openCreateNote() {
    setActiveTab("overview");
    setNoteEditor({ mode: "create" });
    setNoteForm(emptyNoteForm);
    setNoteError(null);
  }

  function openEditNote(note: NoteEntry) {
    setActiveTab("overview");
    setNoteEditor({ mode: "edit", noteId: note.id });
    setNoteForm(toNoteFormState(note));
    setNoteError(null);
  }

  function closeNoteEditor() {
    setNoteEditor(null);
    setNoteForm(emptyNoteForm);
    setNoteError(null);
  }

  async function handleNoteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!noteForm.title.trim() || !noteForm.content.trim()) {
      setNoteError("Please provide both a note title and note content.");
      return;
    }

    setNoteSaving(true);
    setNoteError(null);

    try {
      if (noteEditor?.mode === "edit" && noteEditor.noteId) {
        const updated = await updateNote(noteEditor.noteId, {
          title: noteForm.title.trim(),
          noteType: noteForm.noteType,
          author: noteForm.author.trim(),
          content: noteForm.content.trim(),
        });
        setNotesState((current) =>
          sortNotes(
            current.map((note) => (note.id === updated.id ? updated : note)),
          ),
        );
        setPageNotice({
          tone: "success",
          message: `${updated.title} was updated in the matter notes.`,
        });
      } else {
        const created = await createNote(caseState.id, {
          title: noteForm.title.trim(),
          noteType: noteForm.noteType,
          author: noteForm.author.trim(),
          content: noteForm.content.trim(),
        });
        setNotesState((current) => sortNotes([created, ...current]));
        setPageNotice({
          tone: "success",
          message: `${created.title} was added to the matter notes.`,
        });
      }

      closeNoteEditor();
    } catch (error) {
      setNoteError(
        error instanceof Error ? error.message : "Unable to save the note.",
      );
    } finally {
      setNoteSaving(false);
    }
  }

  async function handleTimelineSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!timelineForm.title.trim() || !timelineForm.date) {
      setTimelineError("Please provide the event title and event date.");
      return;
    }

    setTimelineSaving(true);
    setTimelineError(null);

    try {
      const created = await createTimelineEvent(caseState.id, {
        title: timelineForm.title.trim(),
        type: timelineForm.type,
        actor: timelineForm.actor.trim(),
        date: timelineForm.date,
        description: timelineForm.description.trim(),
      });

      setTimelineState((current) => sortTimelineEntries([created, ...current]));
      setTimelineOpen(false);
      setTimelineForm(emptyTimelineForm);
      setPageNotice({
        tone: "success",
        message: `${created.title} was added to the case timeline.`,
      });
    } catch (error) {
      setTimelineError(
        error instanceof Error
          ? error.message
          : "Unable to save the timeline event.",
      );
    } finally {
      setTimelineSaving(false);
    }
  }

  async function handleResearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!researchForm.title.trim() || !researchForm.summary.trim()) {
      setResearchError("Please provide the research title and summary.");
      return;
    }

    setResearchSaving(true);
    setResearchError(null);

    try {
      const created = await createResearchEntry(caseState.id, {
        title: researchForm.title.trim(),
        query: researchForm.query.trim(),
        summary: researchForm.summary.trim(),
        citations: splitList(researchForm.citations),
        sourceType: researchForm.sourceType.trim(),
        status: researchForm.status,
        author: researchForm.author.trim(),
        nextQuestion: researchForm.nextQuestion.trim(),
      });

      setResearchState((current) => sortResearchEntries([created, ...current]));
      setResearchOpen(false);
      setResearchForm(emptyResearchForm);
      setPageNotice({
        tone: "success",
        message: `${created.title} was saved to the research workspace.`,
      });
    } catch (error) {
      setResearchError(
        error instanceof Error
          ? error.message
          : "Unable to save the research entry.",
      );
    } finally {
      setResearchSaving(false);
    }
  }

  function openCreateDraft() {
    setActiveTab("drafts");
    setDraftEditor({ mode: "create" });
    setDraftForm(emptyDraftForm);
    setDraftError(null);
  }

  function openDraftAssist() {
    setActiveTab("drafts");
    setDraftAssistOpen(true);
    setDraftAssistError(null);
  }

  function openResearchGeneration() {
    setActiveTab("research");
    setResearchGenerationOpen(true);
    setResearchGenerationError(null);
    setResearchGenerationForm((current) => ({
      ...current,
      issue: current.issue || caseState.issues[0] || "",
    }));
  }

  async function handleResearchWorkflowRun() {
    setActiveTab("research");
    setResearchWorkflowSaving(true);
    setResearchWorkflowError(null);

    try {
      const run = await runCaseResearchDraft(caseState.id, {
        draftType: researchWorkflowOptions.draftType,
        focusIssues: caseState.issues.slice(0, 4),
        includeDocuments: true,
        includePriorNotes: true,
        includeTimeline: true,
        maxSources: Number.parseInt(researchWorkflowOptions.maxSources, 10) || 12,
        maxLiveSources:
          Number.parseInt(researchWorkflowOptions.maxLiveSources, 10) || 8,
        generatePdf: true,
        useLiveWeb: researchWorkflowOptions.useLiveWeb,
        useLlm: researchWorkflowOptions.useLlm,
        generateFullDraft: researchWorkflowOptions.generateFullDraft,
      });
      setResearchWorkflowRuns((current) => [
        run,
        ...current.filter((item) => item.runId !== run.runId),
      ]);
      await refreshCaseWorkspace();
      setPageNotice({
        tone: run.status === "completed" ? "success" : "info",
        message:
          run.status === "completed"
            ? "Research & Draft pipeline completed with grounded research output."
            : "Research & Draft pipeline completed with review warnings.",
      });
    } catch (error) {
      setResearchWorkflowError(
        error instanceof Error
          ? error.message
          : "Unable to run the research workflow.",
      );
    } finally {
      setResearchWorkflowSaving(false);
    }
  }

  function handleResearchRunUpdated(updatedRun: ResearchWorkflowResponse) {
    setResearchWorkflowRuns((current) =>
      current.map((run) => (run.runId === updatedRun.runId ? updatedRun : run)),
    );
  }

  function openEditDraft(draft: DraftArtifact) {
    setActiveTab("drafts");
    setDraftEditor({ mode: "edit", draftId: draft.id });
    setDraftForm(toDraftFormState(draft));
    setDraftError(null);
  }

  function closeDraftEditor() {
    setDraftEditor(null);
    setDraftForm(emptyDraftForm);
    setDraftError(null);
  }

  async function handleDraftSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!draftForm.title.trim() || !draftForm.summary.trim()) {
      setDraftError("Please provide the draft title and summary.");
      return;
    }

    setDraftSaving(true);
    setDraftError(null);

    try {
      if (draftEditor?.mode === "edit" && draftEditor.draftId) {
        const updated = await updateDraft(draftEditor.draftId, {
          title: draftForm.title.trim(),
          type: draftForm.type.trim(),
          status: draftForm.status,
          owner: draftForm.owner.trim(),
          version: Number(draftForm.version || "1"),
          summary: draftForm.summary.trim(),
          content: draftForm.content.trim(),
        });
        setDraftsState((current) =>
          sortDrafts(
            current.map((draft) => (draft.id === updated.id ? updated : draft)),
          ),
        );
        setCaseState((current) => ({
          ...current,
          draftArtifacts: sortDrafts(
            current.draftArtifacts.map((draft) =>
              draft.id === updated.id ? updated : draft,
            ),
          ),
        }));
        setPageNotice({
          tone: "success",
          message: `${updated.title} was updated in the draft workspace.`,
        });
      } else {
        const created = await createDraft(caseState.id, {
          title: draftForm.title.trim(),
          type: draftForm.type.trim(),
          status: draftForm.status,
          owner: draftForm.owner.trim(),
          version: Number(draftForm.version || "1"),
          summary: draftForm.summary.trim(),
          content: draftForm.content.trim(),
        });
        setDraftsState((current) => sortDrafts([created, ...current]));
        setCaseState((current) => ({
          ...current,
          draftArtifacts: sortDrafts([created, ...current.draftArtifacts]),
        }));
        setPageNotice({
          tone: "success",
          message: `${created.title} was added to the draft workspace.`,
        });
      }

      closeDraftEditor();
    } catch (error) {
      setDraftError(
        error instanceof Error ? error.message : "Unable to save the draft.",
      );
    } finally {
      setDraftSaving(false);
    }
  }

  async function handleAgentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!agentForm.agentName.trim() || !agentForm.taskType.trim()) {
      setAgentError("Please provide the agent name and task type.");
      return;
    }

    setAgentSaving(true);
    setAgentError(null);

    try {
      const payload: AgentLogMutationInput = {
        agentName: agentForm.agentName.trim(),
        title: agentForm.title.trim(),
        taskType: agentForm.taskType.trim(),
        status: agentForm.status,
        confidenceScore: agentForm.confidenceScore
          ? Number(agentForm.confidenceScore)
          : null,
        inputSummary: agentForm.inputSummary.trim(),
        outputSummary: agentForm.outputSummary.trim(),
        citations: splitList(agentForm.citations),
        nextAction: agentForm.nextAction.trim(),
      };
      const created = await createAgentLog(caseState.id, payload);
      setAgentOutputsState((current) => sortAgentOutputs([created, ...current]));
      setCaseState((current) => ({
        ...current,
        teamAgents: Array.from(new Set([...current.teamAgents, created.agentId])),
      }));
      setAgentOpen(false);
      setAgentForm(emptyAgentForm);
      setPageNotice({
        tone: "success",
        message: `${created.agentId} log saved to the agent output panel.`,
      });
    } catch (error) {
      setAgentError(
        error instanceof Error
          ? error.message
          : "Unable to save the agent log entry.",
      );
    } finally {
      setAgentSaving(false);
    }
  }

  async function handleGenerateSummary() {
    setSummaryGenerating(true);

    try {
      const generated = await generateCaseSummary(caseState.id);
      setIntelligenceState((current) =>
        sortIntelligence([...generated.artifacts, ...current]),
      );
      setAgentOutputsState((current) =>
        sortAgentOutputs([generated.agentOutput, ...current]),
      );
      setCaseState((current) => ({
        ...current,
        teamAgents: mergeUniqueStrings(current.teamAgents, [
          generated.agentOutput.agentId,
        ]),
      }));
      setPageNotice({
        tone: "success",
        message: "Case summary and procedural summary were generated and stored against this matter.",
      });
    } catch (error) {
      setPageNotice({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to generate the case summary.",
      });
    } finally {
      setSummaryGenerating(false);
    }
  }

  async function handleGenerateIssues() {
    setIssuesGenerating(true);

    try {
      const generated = await generateCaseIssues(caseState.id);
      const issueArtifact = generated.artifacts.find(
        (artifact) => artifact.artifactType === "Issue Spotting",
      );
      const riskArtifact = generated.artifacts.find(
        (artifact) => artifact.artifactType === "Risk Assessment",
      );

      setIntelligenceState((current) =>
        sortIntelligence([...generated.artifacts, ...current]),
      );
      setAgentOutputsState((current) =>
        sortAgentOutputs([generated.agentOutput, ...current]),
      );
      setCaseState((current) => ({
        ...current,
        issues: mergeUniqueStrings(current.issues, readStringList(issueArtifact, "legalIssues")),
        riskFlags: mergeUniqueStrings(
          current.riskFlags,
          readStringList(riskArtifact, "riskFlags"),
        ),
        proceduralAlerts: mergeUniqueStrings(
          current.proceduralAlerts,
          readStringList(riskArtifact, "recommendations"),
        ),
        teamAgents: mergeUniqueStrings(current.teamAgents, [
          generated.agentOutput.agentId,
        ]),
      }));
      setPageNotice({
        tone: "success",
        message: "Issue spotting and risk review were generated for this matter.",
      });
    } catch (error) {
      setPageNotice({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to generate issue spotting.",
      });
    } finally {
      setIssuesGenerating(false);
    }
  }

  async function handleDraftAssistSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!draftAssistForm.draftType.trim()) {
      setDraftAssistError("Choose the draft assistance type before running generation.");
      return;
    }

    setDraftAssistSaving(true);
    setDraftAssistError(null);

    try {
      const generated = await generateDraftAssistance(caseState.id, {
        draftType: draftAssistForm.draftType.trim(),
        instructions: draftAssistForm.instructions.trim(),
      });
      setDraftsState((current) => sortDrafts([generated.draft, ...current]));
      setIntelligenceState((current) =>
        sortIntelligence([generated.artifact, ...current]),
      );
      setAgentOutputsState((current) =>
        sortAgentOutputs([generated.agentOutput, ...current]),
      );
      setCaseState((current) => ({
        ...current,
        draftArtifacts: sortDrafts([generated.draft, ...current.draftArtifacts]),
        teamAgents: mergeUniqueStrings(current.teamAgents, [
          generated.agentOutput.agentId,
        ]),
      }));
      setDraftAssistOpen(false);
      setDraftAssistForm(emptyDraftAssistForm);
      setPageNotice({
        tone: "success",
        message: `${generated.draft.title} was generated as AI-assisted chamber draft support and stored in the draft workspace.`,
      });
    } catch (error) {
      setDraftAssistError(
        error instanceof Error
          ? error.message
          : "Unable to generate draft assistance.",
      );
    } finally {
      setDraftAssistSaving(false);
    }
  }

  async function handleResearchGenerationSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setResearchGenerationSaving(true);
    setResearchGenerationError(null);

    try {
      const generated = await generateResearchNote(caseState.id, {
        issue: researchGenerationForm.issue.trim(),
        instructions: researchGenerationForm.instructions.trim(),
      });
      setResearchState((current) => sortResearchEntries([generated.research, ...current]));
      setIntelligenceState((current) =>
        sortIntelligence([generated.artifact, ...current]),
      );
      setAgentOutputsState((current) =>
        sortAgentOutputs([generated.agentOutput, ...current]),
      );
      setCaseState((current) => ({
        ...current,
        teamAgents: mergeUniqueStrings(current.teamAgents, [
          generated.agentOutput.agentId,
        ]),
      }));
      setResearchGenerationOpen(false);
      setResearchGenerationForm({
        ...emptyResearchGenerationForm,
        issue: caseState.issues[0] ?? "",
      });
      setPageNotice({
        tone: "success",
        message: `${generated.research.title} was generated and stored in the research workspace.`,
      });
    } catch (error) {
      setResearchGenerationError(
        error instanceof Error
          ? error.message
          : "Unable to generate the research note.",
      );
    } finally {
      setResearchGenerationSaving(false);
    }
  }

  function openChamberRunForm() {
    setActiveTab("agent-output");
    setRunFormOpen(true);
    setRunError(null);
  }

  async function handleChamberRunSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!runForm.instruction.trim()) {
      setRunError("Enter the chamber instruction before starting the workflow.");
      return;
    }

    setRunSaving(true);
    setRunError(null);

    try {
      const createdRun = await createCaseRun(caseState.id, {
        instruction: runForm.instruction.trim(),
        taskType: runForm.taskType || undefined,
      });
      const detail = await refreshCaseWorkspace();
      setSelectedRun(createdRun);
      setSelectedRunId(createdRun.id);
      setRunsState(detail.runs);
      setRunFormOpen(false);
      setRunForm(emptyChamberRunForm);
      setPageNotice({
        tone: "success",
        message:
          "Coordinated chamber workflow completed and the run trace is now stored on this matter.",
      });
    } catch (error) {
      setRunError(
        error instanceof Error
          ? error.message
          : "Unable to start the chamber workflow.",
      );
    } finally {
      setRunSaving(false);
    }
  }

  async function handleRunPredictions() {
    setPredicting(true);
    setPageNotice({
      tone: "info",
      message:
        "Running predictive assistance across outcome, maintainability, risk, and case-type tasks...",
    });

    try {
      const nextPredictions = await predictCase({ caseId: caseState.id });
      const nextExplanations = await getCasePredictionExplanations(caseState.id).catch(
        () => [],
      );
      setPredictionsState(nextPredictions);
      setPredictionExplanationsState(nextExplanations);
      setPageNotice({
        tone: nextPredictions.length ? "success" : "error",
        message: nextPredictions.length
          ? "Predictions updated from the latest available trained models."
          : "No ready models were available yet. Train models in the prediction engine lab first.",
      });
    } catch (error) {
      setPageNotice({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to run predictive assistance for this matter.",
      });
    } finally {
      setPredicting(false);
    }
  }

  const latestPredictions = ["case_outcome", "maintainability", "risk_scoring", "case_type"]
    .map((taskName) =>
      predictionsState.find((prediction) => prediction.taskName === taskName),
    )
    .filter((prediction): prediction is CasePrediction => Boolean(prediction));

  const readinessByTask = new Map(datasetReadiness.map((item) => [item.taskName, item]));

  return (
    <div
      className={
        activeTab === "research"
          ? "w-full min-w-0 space-y-6"
          : "grid w-full min-w-0 gap-6 2xl:grid-cols-[minmax(0,1fr)_320px]"
      }
    >
      <div className="min-w-0 space-y-6">
        {pageNotice ? (
          <InlineFeedback message={pageNotice.message} tone={pageNotice.tone} />
        ) : null}

        <Card className="space-y-6 rounded-[32px]">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={caseState.status} />
                <PriorityBadge priority={caseState.priority} />
                <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  {caseState.matterType}
                </span>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-subtle">
                  {caseState.caseNumber}
                </p>
                <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-foreground">
                  {caseState.title}
                </h1>
              </div>
              <p className="legal-text-wrap max-w-5xl text-sm leading-7 text-muted-foreground">
                {caseState.summary}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                disabled={researchWorkflowSaving}
                onClick={handleResearchWorkflowRun}
              >
                {researchWorkflowSaving ? "Running Research & Draft..." : "Research & Draft"}
              </Button>
              <Button
                onClick={() => setActiveTab("research")}
                variant="outline"
              >
                View research runs
              </Button>
              <Button onClick={openCreateNote} variant="secondary">
                Add note
              </Button>
              <Button onClick={openChamberRunForm} variant="secondary">
                Run chamber workflow
              </Button>
              <Button onClick={openDraftAssist} variant="outline">
                Generate draft
              </Button>
              <Button
                onClick={handleGenerateSummary}
                disabled={summaryGenerating}
                variant="outline"
              >
                {summaryGenerating ? "Generating summary..." : "Generate summary"}
              </Button>
              <Link
                href={`/cases?edit=${caseState.id}`}
                className={buttonVariants({ variant: "secondary" })}
              >
                Edit matter
              </Link>
              <Link
                href={`/workspace?caseId=${caseState.id}`}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-accent/60 bg-accent px-4.5 text-sm font-semibold text-ink shadow-[0_16px_32px_rgba(187,167,129,0.18)] transition-colors hover:bg-accent-soft"
              >
                Open chamber
                <ArrowUpRight className="size-4" />
              </Link>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Forum" value={caseState.forum} />
            <MetricCard label="Client" value={caseState.client} />
            <MetricCard label="Opposing party" value={caseState.opposingParty} />
            <MetricCard
              label="Next hearing"
              value={formatDate(caseState.nextHearingDate)}
            />
          </div>

          <div className="flex flex-col gap-4 border-t border-line pt-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                Assigned counsel
              </p>
              <div className="mt-2 flex items-center gap-3">
                <AvatarStack names={caseState.assignedCounsel} />
                <div className="text-sm text-muted-foreground">
                  {caseState.assignedCounsel.join(" / ")}
                </div>
              </div>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                Filing stage
              </p>
              <p className="mt-2 text-sm font-medium text-foreground">
                {caseState.stage}
              </p>
            </div>
          </div>
        </Card>

        <Tabs tabs={tabs} value={activeTab} onValueChange={setActiveTab} />

        {activeTab === "overview" ? (
          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard
              className="xl:col-span-2"
              title="Generated chamber intelligence"
              description="Structured AI-assisted summaries and issue reviews generated from the live matter record and linked documents."
              action={
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={handleGenerateSummary}
                    disabled={summaryGenerating}
                    size="sm"
                    variant="secondary"
                  >
                    {summaryGenerating ? "Generating summary..." : "Generate summary"}
                  </Button>
                  <Button
                    onClick={handleGenerateIssues}
                    disabled={issuesGenerating}
                    size="sm"
                    variant="outline"
                  >
                    {issuesGenerating ? "Identifying issues..." : "Identify issues"}
                  </Button>
                </div>
              }
            >
              {summaryArtifacts.length || issueArtifacts.length ? (
                <div className="grid gap-4 xl:grid-cols-2">
                  {[...summaryArtifacts, ...issueArtifacts].map((artifact) => (
                    <Card
                      key={artifact.id}
                      className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                            {artifact.artifactType}
                          </p>
                          <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                            {artifact.title}
                          </h3>
                        </div>
                        <StatusBadge status={artifact.status} />
                      </div>
                      <p className="text-sm leading-6 text-muted-foreground">
                        {artifact.content}
                      </p>
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Legal grounding
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {artifact.groundingStatus}
                        </p>
                        <div className="mt-3">
                          <LegalSourceList
                            compact
                            sources={artifact.legalSources}
                            emptyMessage="No stored legal source was attached to this artifact."
                          />
                        </div>
                      </div>
                      {readStringList(artifact, "nextSteps").length ? (
                        <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                          <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                            Next steps
                          </p>
                          <div className="mt-2 space-y-2">
                            {readStringList(artifact, "nextSteps").map((step) => (
                              <p
                                key={step}
                                className="text-sm leading-6 text-foreground/88"
                              >
                                {step}
                              </p>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </Card>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No chamber-generated intelligence yet"
                  description="Generate a structured summary or issue review to persist AI-assisted work product against this matter."
                  action={
                    <Button onClick={handleGenerateSummary} variant="secondary">
                      Generate summary
                    </Button>
                  }
                />
              )}
            </SectionCard>

            <SectionCard
              title="Predictive assistance"
              description="Experimental ML outputs built from the Phase 7 supervised pipeline. These are informative signals, not guaranteed legal outcomes."
              action={
                <Button
                  onClick={handleRunPredictions}
                  disabled={predicting}
                  size="sm"
                  variant="secondary"
                >
                  {predicting ? "Running predictions..." : "Run predictions"}
                </Button>
              }
            >
              {caseQualitySummaryState ? (
                <div className="mb-4 rounded-2xl border border-line bg-panel-highlight p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                    Matter quality summary
                  </p>
                  <p className="mt-2 text-sm leading-6 text-foreground/88">
                    {caseQualitySummaryState.groundedRunCount} grounded run(s) / average run confidence{" "}
                    {typeof caseQualitySummaryState.averageRunConfidence === "number"
                      ? `${(caseQualitySummaryState.averageRunConfidence * 100).toFixed(0)}%`
                      : "n/a"}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    {caseQualitySummaryState.qualityWarnings[0] ??
                      "No major chamber quality warning is currently attached to this matter."}
                  </p>
                </div>
              ) : null}
              {latestPredictions.length ? (
                <div className="grid gap-4 xl:grid-cols-2">
                  {latestPredictions.map((prediction) => {
                    const topProbabilities = Object.entries(prediction.probabilitiesJson)
                      .sort((left, right) => right[1] - left[1])
                      .slice(0, 3);
                    const explanation = predictionExplanationsState.find(
                      (item) => item.taskName === prediction.taskName,
                    );
                    const readiness = readinessByTask.get(prediction.taskName);

                    return (
                      <Card
                        key={prediction.id}
                        className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                              {prediction.taskName.replaceAll("_", " ")}
                            </p>
                            <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                              {prediction.predictedLabel}
                            </h3>
                          </div>
                          <StatusBadge status={`${Math.round(prediction.confidence * 100)}%`} />
                        </div>

                        <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                          <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                            Model context
                          </p>
                          <p className="mt-2 text-sm leading-6 text-foreground/88">
                            {prediction.modelFamily} / {prediction.modelName}
                          </p>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">
                            Generated {formatDate(prediction.createdAt)}
                          </p>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">
                            Dataset version {String(prediction.metadataJson.datasetVersion ?? prediction.datasetId)}
                          </p>
                        </div>

                        {explanation ? (
                          <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                              Diagnostic note
                            </p>
                            <p className="mt-2 text-sm leading-6 text-muted-foreground">
                              {explanation.explanationNote}
                            </p>
                          </div>
                        ) : null}

                        {readiness ? (
                          <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                              Dataset readiness
                            </p>
                            <p className="mt-2 text-sm leading-6 text-foreground/88">
                              {readiness.status} / {readiness.totalExamples} examples
                            </p>
                            <p className="mt-1 text-sm leading-6 text-muted-foreground">
                              {readiness.warnings[0] ??
                                "No major readiness warning is currently recorded for this task."}
                            </p>
                          </div>
                        ) : null}

                        <div className="space-y-2">
                          <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                            Top probabilities
                          </p>
                          {topProbabilities.map(([label, score]) => (
                            <div
                              key={label}
                              className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm"
                            >
                              <span className="text-foreground">{label}</span>
                              <span className="text-muted-foreground">
                                {(score * 100).toFixed(1)}%
                              </span>
                            </div>
                          ))}
                        </div>

                        <p className="text-sm leading-6 text-muted-foreground">
                          {prediction.warningText}
                        </p>
                        {readiness && ["not_ready", "weak"].includes(readiness.status) ? (
                          <InlineFeedback
                            tone="info"
                            message="Prediction confidence may be unreliable because the current dataset for this task is still weak."
                          />
                        ) : null}
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <EmptyState
                  title="No predictions stored yet"
                  description="Run predictions after training at least one model for the Phase 7 tasks."
                  action={
                    <Button onClick={handleRunPredictions} variant="secondary">
                      Run predictions
                    </Button>
                  }
                />
              )}
            </SectionCard>

            <SectionCard
              title="Case summary"
              description="High-level matter narrative and current litigation posture."
            >
              <p className="text-sm leading-7 text-muted-foreground">{caseState.summary}</p>
            </SectionCard>

            <SectionCard
              title="Grounded legal basis"
              description="Retrieved Pakistani legal materials that currently support this matter's generated chamber work product."
            >
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-line px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                    {legalBasisState.length
                      ? `${legalBasisState.length} stored source${legalBasisState.length === 1 ? "" : "s"}`
                      : "No stored sources"}
                  </span>
                </div>
                <LegalSourceList
                  sources={legalBasisState}
                  emptyMessage="No grounded legal source has been attached to this matter yet. Run a grounded chamber workflow or generate grounded research to start building the legal basis."
                />
              </div>
            </SectionCard>

            <SectionCard
              title="Legal issues"
              description="Primary issues the chamber should keep live for research, drafting, and oral argument."
            >
              <div className="flex flex-wrap gap-2">
                {caseState.issues.map((issue) => (
                  <span
                    key={issue}
                    className="rounded-full border border-line px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-foreground"
                  >
                    {issue}
                  </span>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Relief sought">
              <div className="space-y-3">
                {caseState.reliefSought.map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm leading-6 text-foreground/88"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Important notes">
              <div className="space-y-3">
                {caseState.importantNotes.map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm leading-6 text-muted-foreground"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard
              title="Stored notes"
              action={
                <Button onClick={openCreateNote} size="sm" variant="secondary">
                  Add note
                </Button>
              }
            >
              {noteEditor ? (
                <form
                  className="space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                  onSubmit={handleNoteSubmit}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                        {noteEditor.mode === "edit" ? "Edit note" : "New note"}
                      </p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Persist a chamber note directly to this matter.
                      </p>
                    </div>
                    <button
                      className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                      onClick={closeNoteEditor}
                      type="button"
                    >
                      <X className="size-4" />
                    </button>
                  </div>

                  {noteError ? (
                    <InlineFeedback message={noteError} tone="error" />
                  ) : null}

                  <div className="grid gap-4 md:grid-cols-2">
                    <Field
                      label="Title"
                      value={noteForm.title}
                      onChange={(value) => setNoteForm((current) => ({ ...current, title: value }))}
                      placeholder="Hearing readiness note"
                    />
                    <SelectField
                      label="Note type"
                      value={noteForm.noteType}
                      options={noteTypes}
                      onChange={(value) =>
                        setNoteForm((current) => ({ ...current, noteType: value }))
                      }
                    />
                    <Field
                      label="Author"
                      value={noteForm.author}
                      onChange={(value) => setNoteForm((current) => ({ ...current, author: value }))}
                      placeholder="Hamza Khan"
                    />
                  </div>

                  <TextAreaField
                    label="Content"
                    value={noteForm.content}
                    onChange={(value) =>
                      setNoteForm((current) => ({ ...current, content: value }))
                    }
                    placeholder="Store internal strategy, client notes, or hearing preparation context."
                  />

                  <div className="flex justify-end">
                    <Button disabled={noteSaving} type="submit">
                      {noteSaving
                        ? noteEditor.mode === "edit"
                          ? "Saving note..."
                          : "Adding note..."
                        : noteEditor.mode === "edit"
                          ? "Save note"
                          : "Add note"}
                    </Button>
                  </div>
                </form>
              ) : null}

              <div className="space-y-3">
                {notesState.length ? (
                  notesState.map((note) => (
                    <div
                      key={note.id}
                      className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            {note.title}
                          </p>
                          <p className="mt-1 text-xs uppercase tracking-[0.18em] text-subtle">
                            {note.noteType} / {note.author}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <button
                            className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-foreground"
                            onClick={() => openEditNote(note)}
                            type="button"
                          >
                            Edit
                          </button>
                          <span className="text-xs uppercase tracking-[0.18em] text-subtle">
                            {formatDate(note.updatedAt)}
                          </span>
                        </div>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">
                        {note.content}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm text-muted-foreground">
                    No case notes have been stored yet.
                  </div>
                )}
              </div>
            </SectionCard>

            <SectionCard title="Linked statutes and precedent">
              <div className="space-y-4">
                <div>
                  <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
                    Statutes
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {caseState.linkedStatutes.map((statute) => (
                      <span
                        key={statute}
                        className="rounded-full border border-line px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-muted-foreground"
                      >
                        {statute}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
                    Precedent placeholders
                  </p>
                  <div className="space-y-2">
                    {caseState.precedents.map((precedent) => (
                      <div
                        key={precedent}
                        className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm text-foreground"
                      >
                        {precedent}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Matter staffing">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
                    <Scale className="size-3.5" />
                    Counsel
                  </div>
                  <p className="mt-3 text-sm leading-6 text-foreground">
                    {caseState.assignedCounsel.join(" / ")}
                  </p>
                </div>
                <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-subtle">
                    <Sparkles className="size-3.5" />
                    Assigned agents
                  </div>
                  <p className="mt-3 text-sm leading-6 text-foreground">
                    {caseState.teamAgents.length
                      ? caseState.teamAgents.join(" / ")
                      : "No agent runs logged yet"}
                  </p>
                </div>
              </div>
            </SectionCard>
          </div>
        ) : null}

        {activeTab === "facts" ? (
          <SectionCard
            title="Structured factual background"
            description="Matter facts arranged for neutral internal comprehension before legal framing."
          >
            <div className="space-y-4">
              {caseState.factsBackground.map((fact) => (
                <div
                  key={fact.label}
                  className="rounded-[24px] border border-line bg-white/[0.03] p-5"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
                    {fact.label}
                  </p>
                  <p className="mt-3 text-sm leading-7 text-muted-foreground">
                    {fact.text}
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>
        ) : null}

        {activeTab === "documents" ? (
          <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_360px]">
            <SectionCard
              title="Matter document library"
              description="Working papers, annexures, and filing documents linked to this matter."
              action={
                <Link
                  href={`/documents?upload=1&caseId=${caseState.id}`}
                  className={buttonVariants({ size: "sm", variant: "secondary" })}
                >
                  Upload document
                </Link>
              }
            >
              {documentsState.length ? (
                <DocumentTable
                  documents={documentsState}
                  selectedId={selectedDocumentId}
                  onSelect={setSelectedDocumentId}
                />
              ) : (
                <EmptyState
                  title="No documents linked yet"
                  description="Upload the first filing, annexure, or order sheet for this matter."
                  action={
                    <Link
                      href={`/documents?upload=1&caseId=${caseState.id}`}
                      className={buttonVariants({ variant: "secondary", size: "sm" })}
                    >
                      Upload document
                    </Link>
                  }
                />
              )}
            </SectionCard>
            <DocumentPreview document={selectedDocument} />
          </div>
        ) : null}

        {activeTab === "timeline" ? (
          <SectionCard
            title="Case timeline"
            description="Chronological litigation and drafting activity across the matter."
            action={
              <Button
                onClick={() => {
                  setTimelineOpen(true);
                  setTimelineError(null);
                }}
                size="sm"
                variant="secondary"
              >
                Add event
              </Button>
            }
          >
            {timelineOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleTimelineSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      New timeline event
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Persist a litigation event directly to the matter chronology.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setTimelineOpen(false);
                      setTimelineError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {timelineError ? (
                  <InlineFeedback message={timelineError} tone="error" />
                ) : null}

                <div className="grid gap-4 md:grid-cols-2">
                  <Field
                    label="Event title"
                    value={timelineForm.title}
                    onChange={(value) =>
                      setTimelineForm((current) => ({ ...current, title: value }))
                    }
                    placeholder="Interim injunction argued"
                  />
                  <SelectField
                    label="Event type"
                    value={timelineForm.type}
                    options={timelineTypes}
                    onChange={(value) =>
                      setTimelineForm((current) => ({ ...current, type: value }))
                    }
                  />
                  <Field
                    label="Actor"
                    value={timelineForm.actor}
                    onChange={(value) =>
                      setTimelineForm((current) => ({ ...current, actor: value }))
                    }
                    placeholder="Court / Counsel / Registry"
                  />
                  <Field
                    label="Event date"
                    type="date"
                    value={timelineForm.date}
                    onChange={(value) =>
                      setTimelineForm((current) => ({ ...current, date: value }))
                    }
                  />
                </div>

                <TextAreaField
                  label="Description"
                  value={timelineForm.description}
                  onChange={(value) =>
                    setTimelineForm((current) => ({ ...current, description: value }))
                  }
                  placeholder="Record what happened and why it matters."
                />

                <div className="flex justify-end">
                  <Button disabled={timelineSaving} type="submit">
                    {timelineSaving ? "Saving event..." : "Add event"}
                  </Button>
                </div>
              </form>
            ) : null}

            {timelineState.length ? (
              <TimelineList entries={timelineState} />
            ) : (
              <EmptyState
                title="No timeline events recorded"
                description="Add the first filing, hearing, notice, or order event for this matter."
                action={
                  <Button
                    onClick={() => {
                      setTimelineOpen(true);
                      setTimelineError(null);
                    }}
                    variant="secondary"
                  >
                    Add first event
                  </Button>
                }
              />
            )}
          </SectionCard>
        ) : null}

        {activeTab === "research" ? (
          <SectionCard
            title="Research notes"
            description="Authority mapping, maintainability notes, and next research questions."
            action={
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={researchWorkflowSaving}
                  onClick={handleResearchWorkflowRun}
                  size="sm"
                >
                  {researchWorkflowSaving ? "Researching..." : "Research & Draft"}
                </Button>
                <Button
                  onClick={openResearchGeneration}
                  size="sm"
                  variant="outline"
                >
                  Generate research
                </Button>
                <Button
                  onClick={() => {
                    setResearchOpen(true);
                    setResearchError(null);
                  }}
                  size="sm"
                  variant="secondary"
                >
                  Add research
                </Button>
              </div>
            }
          >
            {researchGenerationOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleResearchGenerationSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      AI-assisted research note
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Generate a structured research note tied to this matter and store it in the workspace.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setResearchGenerationOpen(false);
                      setResearchGenerationError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {researchGenerationError ? (
                  <InlineFeedback message={researchGenerationError} tone="error" />
                ) : null}

                <Field
                  label="Issue focus"
                  value={researchGenerationForm.issue}
                  onChange={(value) =>
                    setResearchGenerationForm((current) => ({
                      ...current,
                      issue: value,
                    }))
                  }
                  placeholder="Maintainability objections in the present matter"
                />
                <TextAreaField
                  label="Instructions"
                  value={researchGenerationForm.instructions}
                  onChange={(value) =>
                    setResearchGenerationForm((current) => ({
                      ...current,
                      instructions: value,
                    }))
                  }
                  placeholder="Optional chamber instruction for tone, issue emphasis, or hearing posture."
                />

                <div className="flex justify-end">
                  <Button disabled={researchGenerationSaving} type="submit">
                    {researchGenerationSaving
                      ? "Generating research..."
                      : "Generate research note"}
                  </Button>
                </div>
              </form>
            ) : null}

            {researchOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleResearchSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      New research entry
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Store the legal query, summary, authority list, and next question.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setResearchOpen(false);
                      setResearchError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {researchError ? (
                  <InlineFeedback message={researchError} tone="error" />
                ) : null}

                <div className="grid gap-4 md:grid-cols-2">
                  <Field
                    label="Title"
                    value={researchForm.title}
                    onChange={(value) =>
                      setResearchForm((current) => ({ ...current, title: value }))
                    }
                    placeholder="Maintainability review"
                  />
                  <SelectField
                    label="Status"
                    value={researchForm.status}
                    options={researchStatuses}
                    onChange={(value) =>
                      setResearchForm((current) => ({ ...current, status: value }))
                    }
                  />
                  <Field
                    label="Author"
                    value={researchForm.author}
                    onChange={(value) =>
                      setResearchForm((current) => ({ ...current, author: value }))
                    }
                    placeholder="Research Agent"
                  />
                  <Field
                    label="Source type"
                    value={researchForm.sourceType}
                    onChange={(value) =>
                      setResearchForm((current) => ({ ...current, sourceType: value }))
                    }
                    placeholder="Internal Research"
                  />
                </div>

                <TextAreaField
                  label="Research query"
                  value={researchForm.query}
                  onChange={(value) =>
                    setResearchForm((current) => ({ ...current, query: value }))
                  }
                  placeholder="What exact legal question was being researched?"
                />
                <TextAreaField
                  label="Summary"
                  value={researchForm.summary}
                  onChange={(value) =>
                    setResearchForm((current) => ({ ...current, summary: value }))
                  }
                  placeholder="Summarize the legal answer and how it affects the matter."
                />
                <Field
                  label="Citations"
                  value={researchForm.citations}
                  onChange={(value) =>
                    setResearchForm((current) => ({ ...current, citations: value }))
                  }
                  placeholder="PLD 2014 SC 123, 2021 CLC 908"
                />
                <TextAreaField
                  label="Next question"
                  value={researchForm.nextQuestion}
                  onChange={(value) =>
                    setResearchForm((current) => ({ ...current, nextQuestion: value }))
                  }
                  placeholder="What should counsel or the next agent verify after reading this note?"
                />

                <div className="flex justify-end">
                  <Button disabled={researchSaving} type="submit">
                    {researchSaving ? "Saving research..." : "Add research entry"}
                  </Button>
                </div>
              </form>
            ) : null}

            <Card className="mb-5 min-w-0 space-y-4 rounded-[24px] border-line bg-white/[0.03] p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                    Workflow options
                  </p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    Local retrieval is always used. Live web and LLM drafting only run when configured.
                  </p>
                </div>
                {researchHealth ? (
                  <div className="text-right text-xs uppercase tracking-[0.18em] text-subtle">
                    <p>Web: {researchHealth.liveWebSearchAvailable ? "available" : "local only"}</p>
                    <p>LLM: {researchHealth.llmAvailable ? researchHealth.llmModel : "fallback"}</p>
                  </div>
                ) : null}
              </div>
              <div className="grid gap-4 lg:grid-cols-4">
                <SelectField
                  label="Draft type"
                  onChange={(value) =>
                    setResearchWorkflowOptions((current) => ({
                      ...current,
                      draftType: value,
                    }))
                  }
                  options={researchDraftTypeOptions}
                  value={researchWorkflowOptions.draftType}
                />
                <Field
                  label="Max sources"
                  onChange={(value) =>
                    setResearchWorkflowOptions((current) => ({
                      ...current,
                      maxSources: value,
                    }))
                  }
                  type="number"
                  value={researchWorkflowOptions.maxSources}
                />
                <Field
                  label="Max live sources"
                  onChange={(value) =>
                    setResearchWorkflowOptions((current) => ({
                      ...current,
                      maxLiveSources: value,
                    }))
                  }
                  type="number"
                  value={researchWorkflowOptions.maxLiveSources}
                />
                <div className="space-y-3 rounded-2xl border border-line bg-panel-highlight p-4">
                  <label className="flex items-center gap-3 text-sm text-muted-foreground">
                    <input
                      checked={researchWorkflowOptions.useLiveWeb}
                      disabled={!researchHealth?.liveWebSearchAvailable}
                      onChange={(event) =>
                        setResearchWorkflowOptions((current) => ({
                          ...current,
                          useLiveWeb: event.target.checked,
                        }))
                      }
                      type="checkbox"
                    />
                    Use live web search
                  </label>
                  <label className="flex items-center gap-3 text-sm text-muted-foreground">
                    <input
                      checked={researchWorkflowOptions.useLlm}
                      disabled={!researchHealth?.llmAvailable}
                      onChange={(event) =>
                        setResearchWorkflowOptions((current) => ({
                          ...current,
                          useLlm: event.target.checked,
                        }))
                      }
                      type="checkbox"
                    />
                    Use LLM research/drafting
                  </label>
                  <label className="flex items-center gap-3 text-sm text-muted-foreground">
                    <input
                      checked={researchWorkflowOptions.generateFullDraft}
                      onChange={(event) =>
                        setResearchWorkflowOptions((current) => ({
                          ...current,
                          generateFullDraft: event.target.checked,
                        }))
                      }
                      type="checkbox"
                    />
                    Generate full draft
                  </label>
                </div>
              </div>
            </Card>

            {researchWorkflowError ? (
              <InlineFeedback message={researchWorkflowError} tone="error" />
            ) : null}

            {researchWorkflowLoading ? (
              <Card className="mb-5 rounded-[24px] border-line bg-white/[0.03] p-5 text-sm text-muted-foreground">
                Loading stored research workflow runs...
              </Card>
            ) : null}

            {researchWorkflowRuns.length ? (
              <div className="mb-5 min-w-0 space-y-5">
                {researchWorkflowRuns.map((run) => (
                  <Card
                    key={run.runId}
                    className="min-w-0 space-y-6 rounded-[28px] border-line bg-panel-highlight/45 p-4 sm:p-5 lg:p-6"
                  >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                          Research & Draft pipeline
                        </p>
                        <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                          {run.researchMemo.recommendedDraftType.replaceAll("_", " ")}
                        </h3>
                        <p className="legal-text-wrap mt-2 max-w-5xl text-sm leading-6 text-muted-foreground">
                          {run.legalAuthorityWarning}
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {Object.entries(run.sourcesByOrigin).map(([origin, group]) => (
                            <span
                              className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                              key={`${run.runId}-${origin}`}
                            >
                              {origin.replaceAll("_", " ")}: {sourceGroupCount(group)}
                            </span>
                          ))}
                          <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                            Live web: {run.liveWebUsed ? "used" : "not used"}
                          </span>
                          <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                            LLM draft: {run.llmUsedForDrafting ? "used" : "fallback"}
                          </span>
                        </div>
                      </div>
                      <StatusBadge
                        status={
                          run.status === "completed"
                            ? "Completed"
                            : run.status === "failed"
                              ? "Failed"
                              : "Needs Review"
                        }
                      />
                    </div>

                    <div className="grid min-w-0 gap-3 xl:grid-cols-2">
                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Provider status
                        </p>
                        <div className="mt-3 grid min-w-0 gap-2 text-sm leading-6 text-muted-foreground md:grid-cols-2">
                          <p className="legal-text-wrap">Local retrieval: {providerValue(run.providerStatus, "localRetrievalUsed")}</p>
                          <p className="legal-text-wrap">OpenAI web: {providerValue(run.providerStatus, "openaiWebSearchUsed")}</p>
                          <p className="legal-text-wrap">LLM research: {providerValue(run.providerStatus, "llmUsedForResearch")}</p>
                          <p className="legal-text-wrap">LLM drafting: {providerValue(run.providerStatus, "llmUsedForDrafting")}</p>
                          <p className="legal-text-wrap">Search provider: {providerValue(run.providerStatus, "searchProvider")}</p>
                          <p className="legal-text-wrap">Model: {providerValue(run.providerStatus, "llmModel")}</p>
                        </div>
                      </div>
                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Workflow stages
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {[
                            "Reading case",
                            "Detecting legal issues",
                            "Planning research",
                            "Searching local corpus",
                            run.liveWebUsed ? "Searching live web" : "Live web fallback",
                            "Validating sources",
                            "Writing research memo",
                            run.generatedDraft ? "Drafting legal document" : "Draft skipped",
                            "Critic review",
                            run.pdfPath ? "PDF generated" : "Markdown generated",
                          ].map((stage) => (
                            <span
                              className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                              key={`${run.runId}-${stage}`}
                            >
                              {stage}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {run.privacyNotice ? (
                      <InlineFeedback message={run.privacyNotice} tone="info" />
                    ) : null}

                    {run.warnings?.length ? (
                      <div className="rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-amber-200">
                          Workflow warnings
                        </p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-100/90">
                          {run.warnings.slice(0, 8).map((warning) => (
                            <li key={`${run.runId}-warning-${warning}`}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}

                    <div className="grid min-w-0 gap-3 xl:grid-cols-3">
                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Detected issues
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {run.detectedIssues.slice(0, 8).map((issue) => (
                            <span
                              key={`${run.runId}-${issue.label}`}
                              className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                            >
                              {issue.label.replaceAll("_", " ")}
                              {typeof issue.probability === "number"
                                ? ` ${Math.round(issue.probability * 100)}%`
                                : ""}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Query plan
                        </p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                          {run.queryPlan.slice(0, 4).map((query) => (
                            <li className="legal-text-wrap" key={`${run.runId}-${query.query}`}>
                              {query.query}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Critic review
                        </p>
                        <p className="legal-text-wrap mt-3 text-sm leading-6 text-muted-foreground">
                          {run.criticReport.recommendation}
                        </p>
                      </div>
                    </div>

                    <div className="grid min-w-0 gap-4 xl:grid-cols-2">
                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Arguments for client
                        </p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                          {run.researchMemo.argumentsForClient.map((item) => (
                            <li className="legal-text-wrap" key={`${run.runId}-for-${item}`}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Risks and gaps
                        </p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                          {[
                            ...run.researchMemo.argumentsAgainstClient,
                            ...run.researchMemo.researchGaps,
                          ]
                            .slice(0, 8)
                            .map((item) => (
                              <li className="legal-text-wrap" key={`${run.runId}-risk-${item}`}>{item}</li>
                            ))}
                        </ul>
                      </div>
                    </div>

                    <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Retrieved Pakistani legal sources
                      </p>
                      {sourceGroupEntries(run.sourcesByOrigin).some(([, sources]) => sources.length) ? (
                        <div className="mt-3 space-y-4">
                          {sourceGroupEntries(run.sourcesByOrigin).map(([origin, sources]) =>
                            sources.length ? (
                              <div key={`${run.runId}-origin-${origin}`}>
                                <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                                  {origin.replaceAll("_", " ")}
                                </p>
                                 <div className="mt-3 grid min-w-0 gap-3 xl:grid-cols-2">
                                  {sources.slice(0, 6).map((source) => (
                                    <div
                                      key={`${run.runId}-${origin}-${source.id ?? source.title}`}
                                      className="min-w-0 rounded-2xl border border-line bg-panel p-4"
                                    >
                                      <p className="legal-text-wrap text-sm font-semibold text-foreground">
                                        {source.title}
                                      </p>
                                      <p className="legal-url-wrap mt-1 text-xs uppercase tracking-[0.18em] text-subtle">
                                        {source.sourceType}
                                        {source.citation ? ` / ${source.citation}` : ""}
                                        {source.domain ? ` / ${source.domain}` : ""}
                                      </p>
                                      <p className="legal-text-wrap mt-3 text-sm leading-6 text-muted-foreground">
                                        {source.excerpt}
                                      </p>
                                      {source.url ? (
                                        <a
                                          className="legal-url-wrap mt-3 inline-flex max-w-full text-xs font-semibold uppercase tracking-[0.18em] text-accent"
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
                              </div>
                            ) : null,
                          )}
                        </div>
                      ) : (
                        <p className="mt-3 text-sm leading-6 text-muted-foreground">
                          No source was retrieved. The memo marks this as a research gap.
                        </p>
                      )}
                    </div>

                    <EditableDraftCard
                      onRunUpdated={handleResearchRunUpdated}
                      run={run}
                    />

                    <div className="min-w-0 rounded-2xl border border-line bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Drafting instructions
                      </p>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <p className="legal-text-wrap text-sm leading-6 text-muted-foreground">
                          Draft type:{" "}
                          <span className="text-foreground">
                            {run.draftingInstructions.selectedDraftType ??
                              run.researchMemo.recommendedDraftType}
                          </span>
                        </p>
                        <p className="legal-text-wrap text-sm leading-6 text-muted-foreground">
                          Core issues:{" "}
                          {(run.draftingInstructions.coreIssuesToPlead ?? [])
                            .slice(0, 5)
                            .join(", ") || "Review memo issues"}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Link
                        className={buttonVariants({ size: "sm" })}
                        href={`/research/runs/${run.runId}`}
                      >
                        Open run
                      </Link>
                      <a
                        className={buttonVariants({ size: "sm", variant: "secondary" })}
                        href={getResearchMarkdownUrl(run.runId)}
                        rel="noreferrer"
                        target="_blank"
                      >
                        Open markdown
                      </a>
                      {run.pdfPath ? (
                        <a
                          className={buttonVariants({ size: "sm", variant: "outline" })}
                          href={getResearchPdfUrl(run.runId)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Download PDF
                        </a>
                      ) : null}
                    </div>
                  </Card>
                ))}
              </div>
            ) : null}

            {generatedResearchArtifacts.length ? (
              <div className="mb-5 grid gap-4 xl:grid-cols-2">
                {generatedResearchArtifacts.map((artifact) => (
                  <Card
                    key={artifact.id}
                    className="space-y-4 rounded-[24px] border-line bg-panel-highlight/40"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          {artifact.artifactType}
                        </p>
                        <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                          {artifact.title}
                        </h3>
                      </div>
                      <StatusBadge status={artifact.status} />
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {artifact.content}
                    </p>
                    <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Legal grounding
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground/88">
                        {artifact.groundingStatus}
                      </p>
                      <div className="mt-3">
                        <LegalSourceList
                          compact
                          sources={artifact.legalSources}
                          emptyMessage="No stored legal source was attached to this research artifact."
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : null}

            {researchState.length ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {researchState.map((note) => (
                  <Card
                    key={note.id}
                    className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                  >
                    <div className="space-y-1">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        {note.author} / {note.status}
                      </p>
                      <h3 className="text-lg font-semibold tracking-tight text-foreground">
                        {note.title}
                      </h3>
                    </div>
                    {note.query ? (
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Query
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {note.query}
                        </p>
                      </div>
                    ) : null}
                    <p className="text-sm leading-6 text-muted-foreground">
                      {note.summary}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {note.authorities.map((authority, index) => (
                        <span
                          key={`${note.id}-authority-${index}-${authority}`}
                          className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                        >
                          {authority}
                        </span>
                      ))}
                    </div>
                    <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Next question
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground/88">
                        {note.nextQuestion}
                      </p>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No research entries stored"
                description="Add the first research note for this matter so the chamber retains the legal thread."
                action={
                  <Button
                    onClick={() => {
                      setResearchOpen(true);
                      setResearchError(null);
                    }}
                    variant="secondary"
                  >
                    Add research
                  </Button>
                }
              />
            )}
          </SectionCard>
        ) : null}

        {activeTab === "drafts" ? (
          <SectionCard
            title="Draft workspace"
            description="Draft pleadings and matter notes currently active inside the chamber."
            action={
              <div className="flex flex-wrap gap-2">
                <Button onClick={openDraftAssist} size="sm" variant="outline">
                  Generate draft
                </Button>
                <Button onClick={openCreateDraft} size="sm" variant="secondary">
                  Add draft
                </Button>
              </div>
            }
          >
            {draftAssistOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleDraftAssistSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      AI-assisted draft support
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Generate a first-pass draft skeleton tied to the live case record and linked documents.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setDraftAssistOpen(false);
                      setDraftAssistError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {draftAssistError ? (
                  <InlineFeedback message={draftAssistError} tone="error" />
                ) : null}

                <Field
                  label="Draft assistance type"
                  value={draftAssistForm.draftType}
                  onChange={(value) =>
                    setDraftAssistForm((current) => ({
                      ...current,
                      draftType: value,
                    }))
                  }
                  placeholder="Preliminary objections outline"
                />
                <TextAreaField
                  label="Instructions"
                  value={draftAssistForm.instructions}
                  onChange={(value) =>
                    setDraftAssistForm((current) => ({
                      ...current,
                      instructions: value,
                    }))
                  }
                  placeholder="Optional chamber instruction for emphasis, tone, or use at hearing."
                />

                <div className="flex justify-end">
                  <Button disabled={draftAssistSaving} type="submit">
                    {draftAssistSaving ? "Generating draft..." : "Generate draft assistance"}
                  </Button>
                </div>
              </form>
            ) : null}

            {draftEditor ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleDraftSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      {draftEditor.mode === "edit" ? "Edit draft" : "New draft"}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Store or update a live draft record for this matter.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={closeDraftEditor}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {draftError ? (
                  <InlineFeedback message={draftError} tone="error" />
                ) : null}

                <div className="grid gap-4 md:grid-cols-2">
                  <Field
                    label="Title"
                    value={draftForm.title}
                    onChange={(value) =>
                      setDraftForm((current) => ({ ...current, title: value }))
                    }
                    placeholder="Written statement draft"
                  />
                  <Field
                    label="Draft type"
                    value={draftForm.type}
                    onChange={(value) =>
                      setDraftForm((current) => ({ ...current, type: value }))
                    }
                    placeholder="Written statement"
                  />
                  <SelectField
                    label="Status"
                    value={draftForm.status}
                    options={draftStatuses}
                    onChange={(value) =>
                      setDraftForm((current) => ({ ...current, status: value }))
                    }
                  />
                  <Field
                    label="Owner"
                    value={draftForm.owner}
                    onChange={(value) =>
                      setDraftForm((current) => ({ ...current, owner: value }))
                    }
                    placeholder="Drafting Agent"
                  />
                  <Field
                    label="Version"
                    type="number"
                    value={draftForm.version}
                    onChange={(value) =>
                      setDraftForm((current) => ({ ...current, version: value }))
                    }
                  />
                </div>

                <TextAreaField
                  label="Summary"
                  value={draftForm.summary}
                  onChange={(value) =>
                    setDraftForm((current) => ({ ...current, summary: value }))
                  }
                  placeholder="Short draft summary for the chamber dashboard."
                />
                <TextAreaField
                  label="Content"
                  value={draftForm.content}
                  onChange={(value) =>
                    setDraftForm((current) => ({ ...current, content: value }))
                  }
                  placeholder="Persist the current draft content for the matter."
                />

                <div className="flex justify-end">
                  <Button disabled={draftSaving} type="submit">
                    {draftSaving
                      ? draftEditor.mode === "edit"
                        ? "Saving draft..."
                        : "Adding draft..."
                      : draftEditor.mode === "edit"
                        ? "Save draft"
                        : "Add draft"}
                  </Button>
                </div>
              </form>
            ) : null}

            {draftIntelligence.length ? (
              <div className="mb-5 grid gap-4 xl:grid-cols-2">
                {draftIntelligence.map((artifact) => (
                  <Card
                    key={artifact.id}
                    className="space-y-4 rounded-[24px] border-line bg-panel-highlight/40"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          {artifact.artifactType}
                        </p>
                        <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                          {artifact.title}
                        </h3>
                      </div>
                      <StatusBadge status={artifact.status} />
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {artifact.content}
                    </p>
                    <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Legal grounding
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground/88">
                        {artifact.groundingStatus}
                      </p>
                      <div className="mt-3">
                        <LegalSourceList
                          compact
                          sources={artifact.legalSources}
                          emptyMessage="No stored legal source was attached to this draft artifact."
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : null}

            {draftsState.length ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {draftsState.map((draft) => (
                  <Card
                    key={draft.id}
                    className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          {draft.type}
                        </p>
                        <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                          {draft.title}
                        </h3>
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-foreground"
                          onClick={() => openEditDraft(draft)}
                          type="button"
                        >
                          Edit
                        </button>
                        <StatusBadge status={draft.status} />
                      </div>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {draft.summary}
                    </p>
                    {draft.content ? (
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Content snapshot
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {draft.content}
                        </p>
                      </div>
                    ) : null}
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>
                        {draft.owner} / v{draft.version ?? 1}
                      </span>
                      <span>{formatDate(draft.updatedAt)}</span>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No drafts stored"
                description="Add the first petition, reply, objection, or written statement draft for this matter."
                action={
                  <Button onClick={openCreateDraft} variant="secondary">
                    Add draft
                  </Button>
                }
              />
            )}
          </SectionCard>
        ) : null}

        {activeTab === "agent-output" ? (
          <SectionCard
            title="Agent output"
            description="Coordinated chamber runs, critic-reviewed outputs, and manual agent logs attached to this matter for review and audit."
            action={
              <div className="flex flex-wrap gap-2">
                <Button onClick={openChamberRunForm} size="sm" variant="secondary">
                  Start chamber run
                </Button>
                <Button
                  onClick={() => {
                    setAgentOpen(true);
                    setAgentError(null);
                  }}
                  size="sm"
                  variant="outline"
                >
                  Log agent run
                </Button>
              </div>
            }
          >
            {runFormOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleChamberRunSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      Chamber workflow
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Launch a coordinated matter-aware workflow with memory retrieval, specialist agent routing, and critic review.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setRunFormOpen(false);
                      setRunError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {runError ? <InlineFeedback message={runError} tone="error" /> : null}

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Chamber instruction
                  </span>
                  <Textarea
                    placeholder="Example: Draft preliminary objections in this matter and flag any record gaps."
                    value={runForm.instruction}
                    onChange={(event) =>
                      setRunForm((current) => ({
                        ...current,
                        instruction: event.target.value,
                      }))
                    }
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-subtle">
                    Task type
                  </span>
                  <select
                    className="h-11 w-full rounded-2xl border border-line bg-white/[0.03] px-4 text-sm text-foreground outline-none transition-colors focus:border-accent/50 focus:bg-white/[0.05]"
                    value={runForm.taskType}
                    onChange={(event) =>
                      setRunForm((current) => ({
                        ...current,
                        taskType: (event.target.value as ChamberTaskType | "") ?? "",
                      }))
                    }
                  >
                    <option value="">Auto detect from instruction</option>
                    {chamberTaskTypes.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="flex justify-end">
                  <Button disabled={runSaving} type="submit">
                    {runSaving ? "Running chamber workflow..." : "Start chamber workflow"}
                  </Button>
                </div>
              </form>
            ) : null}

            {selectedRun ? (
              <div className="mb-5">
                <ChamberRunPanel run={selectedRun} />
              </div>
            ) : runDetailLoading ? (
              <div className="mb-5">
                <EmptyState
                  title="Loading chamber run"
                  description="Fetching the selected run trace and critic-reviewed output."
                />
              </div>
            ) : null}

            {runsState.length ? (
              <div className="mb-5 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">
                  Stored chamber runs
                </p>
                {runsState.map((run) => (
                  <button
                      key={run.id}
                      className={`w-full rounded-[24px] border p-4 text-left transition-colors ${
                      selectedRunId === run.id
                        ? "border-accent/40 bg-accent/8"
                        : "border-line bg-white/[0.03] hover:border-accent/25"
                    }`}
                    onClick={() => {
                      setRunDetailLoading(true);
                      setSelectedRunId(run.id);
                      setRunError(null);
                    }}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                          {run.selectedWorkflow}
                        </p>
                        <p className="mt-1 text-sm font-medium text-foreground">
                          {run.userInstruction}
                        </p>
                      </div>
                      <StatusBadge status={run.status} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">
                      {run.finalSummary}
                    </p>
                    <p className="mt-3 text-xs uppercase tracking-[0.16em] text-subtle">
                      {formatDate(run.startedAt)}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="mb-5">
                <EmptyState
                  title="No chamber runs stored"
                  description="Start the first coordinated workflow to build a matter-level run trace."
                  action={
                    <Button onClick={openChamberRunForm} variant="secondary">
                      Start chamber run
                    </Button>
                  }
                />
              </div>
            )}

            {agentOpen ? (
              <form
                className="mb-5 space-y-4 rounded-[24px] border border-line bg-white/[0.03] p-5"
                onSubmit={handleAgentSubmit}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
                      Manual agent log
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Persist a manager, research, drafting, critic, or procedural log entry alongside the generated audit trail.
                    </p>
                  </div>
                  <button
                    className="flex size-9 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
                    onClick={() => {
                      setAgentOpen(false);
                      setAgentError(null);
                    }}
                    type="button"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                {agentError ? (
                  <InlineFeedback message={agentError} tone="error" />
                ) : null}

                <div className="grid gap-4 md:grid-cols-2">
                  <Field
                    label="Agent name"
                    value={agentForm.agentName}
                    onChange={(value) =>
                      setAgentForm((current) => ({ ...current, agentName: value }))
                    }
                    placeholder="Research Agent"
                  />
                  <Field
                    label="Run title"
                    value={agentForm.title}
                    onChange={(value) =>
                      setAgentForm((current) => ({ ...current, title: value }))
                    }
                    placeholder="Maintainability objections reviewed"
                  />
                  <Field
                    label="Task type"
                    value={agentForm.taskType}
                    onChange={(value) =>
                      setAgentForm((current) => ({ ...current, taskType: value }))
                    }
                    placeholder="Authority review"
                  />
                  <SelectField
                    label="Status"
                    value={agentForm.status}
                    options={agentStatuses}
                    onChange={(value) =>
                      setAgentForm((current) => ({ ...current, status: value }))
                    }
                  />
                  <Field
                    label="Confidence score"
                    value={agentForm.confidenceScore}
                    onChange={(value) =>
                      setAgentForm((current) => ({
                        ...current,
                        confidenceScore: value,
                      }))
                    }
                    placeholder="0.82"
                  />
                </div>

                <TextAreaField
                  label="Input summary"
                  value={agentForm.inputSummary}
                  onChange={(value) =>
                    setAgentForm((current) => ({ ...current, inputSummary: value }))
                  }
                  placeholder="What was asked of the agent?"
                />
                <TextAreaField
                  label="Output summary"
                  value={agentForm.outputSummary}
                  onChange={(value) =>
                    setAgentForm((current) => ({ ...current, outputSummary: value }))
                  }
                  placeholder="Summarize what the agent produced."
                />
                <Field
                  label="Citations"
                  value={agentForm.citations}
                  onChange={(value) =>
                    setAgentForm((current) => ({ ...current, citations: value }))
                  }
                  placeholder="PLD 2014 SC 123, Civil Procedure Code"
                />
                <TextAreaField
                  label="Next action"
                  value={agentForm.nextAction}
                  onChange={(value) =>
                    setAgentForm((current) => ({ ...current, nextAction: value }))
                  }
                  placeholder="What should counsel or the next agent do now?"
                />

                <div className="flex justify-end">
                  <Button disabled={agentSaving} type="submit">
                    {agentSaving ? "Saving log..." : "Save agent log"}
                  </Button>
                </div>
              </form>
            ) : null}

            {agentOutputsState.length ? (
              <div className="space-y-4">
                {agentOutputsState.map((output) => (
                  <Card
                    key={output.id}
                    className="space-y-4 rounded-[24px] border-line bg-white/[0.03]"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="space-y-1">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          {output.agentId}
                          {output.taskType ? ` / ${output.taskType}` : ""}
                        </p>
                        <h3 className="text-lg font-semibold tracking-tight text-foreground">
                          {output.title}
                        </h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <StatusBadge status={output.status} />
                      </div>
                    </div>
                    {output.inputSummary ? (
                      <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                        <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                          Input summary
                        </p>
                        <p className="mt-2 text-sm leading-6 text-foreground/88">
                          {output.inputSummary}
                        </p>
                      </div>
                    ) : null}
                    <p className="text-sm leading-6 text-muted-foreground">
                      {output.summary}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {output.citations.map((citation) => (
                        <span
                          key={citation}
                          className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                        >
                          {citation}
                        </span>
                      ))}
                    </div>
                    <div className="rounded-2xl border border-line bg-panel-highlight p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                        Next action
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground/88">
                        {output.nextAction}
                      </p>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No agent logs recorded"
                description="Log the first manual agent run so this matter starts building an audit trail."
                action={
                  <Button
                    onClick={() => {
                      setAgentOpen(true);
                      setAgentError(null);
                    }}
                    variant="secondary"
                  >
                    Log agent run
                  </Button>
                }
              />
            )}
          </SectionCard>
        ) : null}
      </div>

      {activeTab === "research" ? null : (
        <RightPanel
          title="Matter intelligence"
          description="Contextual risks, reminders, and the latest chamber reasoning for this file."
          sections={intelligenceSections}
        />
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-line bg-white/[0.03] p-4">
      <p className="text-xs uppercase tracking-[0.18em] text-subtle">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
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
