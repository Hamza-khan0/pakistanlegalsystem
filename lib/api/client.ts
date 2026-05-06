import type {
  ActivityItem,
  AgentActivity,
  AgentOutput,
  ChamberRun,
  ChamberRunStep,
  ChamberRunSummary,
  CaseDetailData,
  CasePrediction,
  CaseDocument,
  CrawlJob,
  CrawledDocument,
  CrawlSource,
  CorpusBuildResult,
  CorpusEntry,
  CorpusExportResult,
  DatasetReadiness,
  EvaluationReport,
  IntelligenceArtifact,
  GroundingSource,
  CaseMatter,
  ChamberTaskType,
  DashboardSummaryData,
  Deadline,
  DraftArtifact,
  MemorySource,
  NoteEntry,
  NotificationItem,
  ResearchNote,
  ResearchHealth,
  ResearchRunSummary,
  ResearchWorkflowRequest,
  ResearchWorkflowResponse,
  TimelineEntry,
  MlDataset,
  MlLeaderboardEntry,
  MlModel,
  MlModelDiagnostics,
  MlModelFamily,
  MlTaskLeaderboard,
  MlTaskName,
  EmbeddingIndexMetadata,
  PredictionExplanation,
  CalibrationRecord,
  CaseQualitySummary,
  ChamberRunQuality,
  RetrievalBenchmarkRun,
  RetrievalLeaderboard,
  RetrievalSearchResult,
  RetrievalMode,
  RunGroundingDiagnostics,
  Tier1DatasetBuildResult,
  Tier1Document,
  Tier1ExportResult,
  Tier1ImportResult,
  Tier1Label,
  Tier1Readiness,
  Tier1Report,
} from "@/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function getApiBaseUrl() {
  return (
    process.env.INTERNAL_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    DEFAULT_API_BASE_URL
  ).replace(/\/$/, "");
}

function buildApiUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function readApiErrorMessage(payload: unknown, fallback: string) {
  if (typeof payload !== "object" || payload === null) {
    return fallback;
  }

  const record = payload as {
    detail?: string;
    errors?: Array<{ msg?: string; loc?: Array<string | number> }>;
  };

  if (typeof record.detail === "string" && record.detail.trim()) {
    if (record.errors?.length) {
      const [firstError] = record.errors;
      const field =
        firstError.loc?.length && typeof firstError.loc[firstError.loc.length - 1] === "string"
          ? String(firstError.loc[firstError.loc.length - 1])
          : null;
      if (firstError.msg) {
        return field ? `${field}: ${firstError.msg}` : firstError.msg;
      }
    }
    return record.detail;
  }

  if (record.errors?.length) {
    const [firstError] = record.errors;
    if (firstError.msg) {
      return firstError.msg;
    }
  }

  return fallback;
}

export class ApiClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function apiRequest<T>(
  path: string,
  init?: RequestInit & { expectJson?: boolean },
): Promise<T> {
  const { expectJson = true, headers, body, ...requestInit } = init ?? {};
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  const response = await fetch(buildApiUrl(path), {
    ...requestInit,
    body,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const payload = (await response.json()) as unknown;
      message = readApiErrorMessage(payload, message);
    } catch {
      message = response.statusText || message;
    }
    throw new ApiClientError(message, response.status);
  }

  if (!expectJson || response.status === 204) {
    return undefined as T;
  }

  const contentLength = response.headers.get("content-length");
  if (contentLength === "0") {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function apiJson<TResponse, TPayload = undefined>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  payload?: TPayload,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    method,
    body: payload === undefined ? undefined : JSON.stringify(payload),
    expectJson: method !== "DELETE",
  });
}

async function apiFormData<TResponse>(
  path: string,
  formData: FormData,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    method: "POST",
    body: formData,
  });
}

async function apiText(path: string): Promise<string> {
  const response = await fetch(buildApiUrl(path), {
    cache: "no-store",
    headers: { Accept: "text/plain" },
  });
  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const payload = (await response.json()) as unknown;
      message = readApiErrorMessage(payload, message);
    } catch {
      message = response.statusText || message;
    }
    throw new ApiClientError(message, response.status);
  }
  return response.text();
}

interface ApiCase {
  id: string;
  title: string;
  caseNumber: string;
  forum: string;
  matterType: string;
  status: string;
  priority: string;
  client: string;
  opposingParty: string;
  summary: string;
  issues: string[];
  reliefSought: string[];
  nextHearingDate: string | null;
  assignedCounsel: string[];
  stage: string;
  riskFlags: string[];
  importantNotes: string[];
  factsBackground: Array<{ label: string; text: string }>;
  linkedStatutes: string[];
  precedents: string[];
  proceduralAlerts: string[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

interface ApiDocument {
  id: string;
  caseId: string;
  name: string;
  type: string;
  status: string;
  category: string;
  fileName: string;
  filePath: string;
  fileUrl: string;
  mimeType: string;
  tags: string[];
  uploadDate: string;
  extractionStatus: string;
  intelligenceStatus: string;
  ocrStatus: string;
  parsingStatus: string;
  previewText: string;
  extractedText: string;
  extractionError: string;
  processedAt: string | null;
  summary: string;
  filedBy: string;
  pages: number;
  metadataJson: Record<string, unknown>;
  caseTitle?: string | null;
  caseNumber?: string | null;
  caseForum?: string | null;
  casePriority?: string | null;
}

interface ApiTimelineEvent {
  id: string;
  caseId: string;
  title: string;
  type: string;
  description: string;
  actor: string;
  date: string;
  createdAt: string;
}

interface ApiNote {
  id: string;
  caseId: string;
  title: string;
  content: string;
  noteType: string;
  author: string;
  createdAt: string;
  updatedAt: string;
}

interface ApiResearchEntry {
  id: string;
  caseId: string;
  title: string;
  query: string;
  summary: string;
  citations: string[];
  sourceType: string;
  status: string;
  author: string;
  nextQuestion: string;
  createdAt: string;
  updatedAt: string;
}

interface ApiDraft {
  id: string;
  caseId: string;
  title: string;
  type: string;
  status: string;
  content: string;
  version: number;
  owner: string;
  summary: string;
  createdAt: string;
  updatedAt: string;
}

interface ApiAgentOutput {
  id: string;
  caseId: string;
  agentName: string;
  title: string;
  taskType: string;
  inputSummary: string;
  outputSummary: string;
  status: string;
  confidenceScore?: number | null;
  confidence: string;
  citations: string[];
  nextAction: string;
  startedAt: string;
  completedAt?: string | null;
  metadataJson: Record<string, unknown>;
}

interface ApiMemorySource {
  sourceId: string;
  sourceType: string;
  title: string;
  detail: string;
  excerpt: string;
}

interface ApiGroundingSource {
  sourceId: string;
  chunkId: string | null;
  title: string;
  shortTitle: string;
  citationLabel: string;
  sourceType: string;
  category: string;
  actName: string;
  sectionLabel: string;
  language: string;
  sourceOrigin: string;
  sourceUrl: string;
  excerpt: string;
  relevanceScore: number | null;
  lexicalScore?: number | null;
  semanticScore?: number | null;
  rerankScore?: number | null;
  retrievalMode?: string;
  explanation?: string;
  usageType: string;
}

interface ApiCrawlSource {
  id: string;
  name: string;
  sourceType: string;
  baseUrl: string;
  allowedDomains: string[];
  crawlMode: string;
  languageHint: string;
  category: string;
  isActive: boolean;
  configJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiCrawlJob {
  id: string;
  sourceId: string;
  sourceName: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  pagesFetched: number;
  documentsDiscovered: number;
  documentsSaved: number;
  errorsCount: number;
  metadataJson: Record<string, unknown>;
}

interface ApiCrawledDocument {
  id: string;
  sourceId: string;
  sourceName: string;
  legalSourceId: string | null;
  sourceUrl: string;
  title: string;
  documentType: string;
  language: string;
  jurisdiction: string;
  rawHtmlPath: string;
  rawHtmlUrl: string;
  downloadedFilePath: string;
  downloadedFileUrl: string;
  mimeType: string;
  crawlStatus: string;
  processingStatus: string;
  duplicateHash: string;
  extractedText: string;
  extractedTextPreview: string;
  normalizedText: string;
  ocrEngine: string;
  ocrStatus: string;
  ocrConfidenceSummary: number | null;
  languageDetected: string;
  pageCount: number;
  errorsJson: Record<string, unknown>;
  processedAt: string | null;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiCorpusEntry {
  id: string;
  sourceKind: string;
  crawledDocumentId: string | null;
  legalSourceId: string | null;
  title: string;
  language: string;
  normalizedText: string;
  chunkCount: number;
  readyForRetrieval: boolean;
  readyForTraining: boolean;
  datasetSplit: string;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiCorpusBuildResult {
  legalSourcesUpserted: number;
  corpusEntriesUpserted: number;
  crawledDocumentsPromoted: number;
}

interface ApiCorpusExportResult {
  outputDir: string;
  retrievalRecords: number;
  classificationRecords: number;
  bilingualRecords: number;
  files: string[];
}

interface ApiMlDataset {
  id: string;
  taskName: string;
  name: string;
  version: string;
  status: string;
  recordCount: number;
  labelStrategy: string;
  splitStrategy: string;
  dataPath: string;
  reportPath: string;
  reportJson: Record<string, unknown>;
  notes: string;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiDatasetReadiness {
  datasetId: string;
  taskName: string;
  datasetName: string;
  datasetVersion: string;
  status: string;
  score: number;
  totalExamples: number;
  uniqueCases: number;
  classDistribution: Record<string, number>;
  classImbalanceRatio: number;
  splitCounts: Record<string, number>;
  labelSourceDistribution: Record<string, number>;
  languageDistribution: Record<string, number>;
  sourceViewDistribution: Record<string, number>;
  missingTextExamples: number;
  nearEmptyExamples: number;
  duplicateExamples: number;
  weakLabelPercentage: number;
  lowOcrConfidencePercentage: number;
  leakageCaseCount: number;
  leakageCaseIds: string[];
  warnings: string[];
  recommendations: string[];
}

interface ApiMlModel {
  id: string;
  datasetId: string;
  taskName: string;
  modelFamily: string;
  name: string;
  status: string;
  artifactPath: string;
  metricsPath: string;
  metricsJson: Record<string, unknown>;
  configJson: Record<string, unknown>;
  labelSchema: string[];
  trainingSummary: string;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiMlLeaderboardEntry {
  modelId: string;
  name: string;
  modelFamily: string;
  primaryMetric: number;
  metricsJson: Record<string, unknown>;
  createdAt: string;
}

interface ApiMlTaskLeaderboard {
  taskName: string;
  entries: ApiMlLeaderboardEntry[];
}

interface ApiMlModelDiagnostics {
  modelId: string;
  taskName: string;
  modelFamily: string;
  modelName: string;
  diagnostics: Record<string, unknown>;
}

interface ApiCasePrediction {
  id: string;
  caseId: string;
  modelId: string;
  taskName: string;
  predictedLabel: string;
  confidence: number;
  probabilitiesJson: Record<string, number>;
  inputSummary: string;
  warningText: string;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  modelName: string;
  modelFamily: string;
  datasetId: string;
}

interface ApiCalibrationRecord {
  modelId: string;
  taskName: string;
  calibrationMethod: string;
  sampleCount: number;
  hasCalibratedScores: boolean;
  supportedMethods: string[];
  metricsJson: Record<string, unknown>;
  reliabilityJson: Record<string, unknown>;
  notes: string;
  createdAt: string;
}

interface ApiPredictionExplanation {
  predictionId: string;
  taskName: string;
  predictedLabel: string;
  confidence: number;
  modelFamily: string;
  modelName: string;
  explanationNote: string;
  topProbabilities: Array<{ label: string; score: number }>;
  structuredSignals: Record<string, unknown>;
  diagnostics: Record<string, unknown>;
}

interface ApiChamberRunStep {
  id: string;
  runId: string;
  stepOrder: number;
  agentName: string;
  taskLabel: string;
  inputSummary: string;
  outputSummary: string;
  fullOutput: string;
  structuredJson: Record<string, unknown>;
  status: string;
  confidenceScore: number | null;
  sourceArtifactIds: string[];
  metadataJson: Record<string, unknown>;
  createdAt: string;
  completedAt: string | null;
}

interface ApiChamberRunSummary {
  id: string;
  caseId: string;
  taskType: string;
  userInstruction: string;
  selectedWorkflow: string;
  status: string;
  finalSummary: string;
  confidenceScore: number | null;
  agentNames: string[];
  memorySources: ApiMemorySource[];
  criticSummary: string;
  finalArtifactId: string | null;
  linkedDraftId: string | null;
  linkedResearchEntryId: string | null;
  groundingStatus: string;
  retrievalMode: string;
  retrievalDiagnostics: Record<string, unknown>;
  legalRetrievalQuery: string;
  legalSourceCount: number;
  legalSources: ApiGroundingSource[];
  startedAt: string;
  completedAt: string | null;
}

interface ApiChamberRun extends ApiChamberRunSummary {
  finalOutput: string;
  steps: ApiChamberRunStep[];
  metadataJson: Record<string, unknown>;
}

interface ApiEmbeddingIndexMetadata {
  id: string;
  name: string;
  retrievalMode: string;
  modelName: string;
  status: string;
  corpusVersion: string;
  indexPath: string;
  vectorDimension: number;
  sourceCount: number;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface ApiRetrievalSearchResult {
  query: string;
  mode: string;
  status: string;
  summary: string;
  diagnostics: Record<string, unknown>;
  sources: ApiGroundingSource[];
}

interface ApiRetrievalLeaderboardEntry {
  mode: string;
  query: string;
  topLabels: string[];
  sourceTypeMix: Record<string, number>;
  averageScore: number;
  diagnostics: Record<string, unknown>;
}

interface ApiRetrievalLeaderboard {
  generatedAt: string;
  entries: ApiRetrievalLeaderboardEntry[];
}

interface ApiRetrievalBenchmarkResult {
  query: string;
  taskType: string;
  mode: string;
  topK: number;
  expectedLabels: string[];
  metricsJson: Record<string, unknown>;
  resultsJson: Array<Record<string, unknown>>;
  diagnostics: Record<string, unknown>;
}

interface ApiRetrievalBenchmarkRun {
  id: string;
  name: string;
  retrievalModesCompared: string[];
  queryCount: number;
  metricsJson: Record<string, unknown>;
  createdAt: string;
  results: ApiRetrievalBenchmarkResult[];
}

interface ApiRunGroundingDiagnostics {
  runId: string;
  retrievalMode: string;
  groundingStatus: string;
  diagnostics: Record<string, unknown>;
  sources: ApiGroundingSource[];
}

interface ApiChamberRunQuality {
  runId: string;
  caseId: string;
  status: string;
  retrievalMode: string;
  sourceCountRetrieved: number;
  sourceCountReliedOn: number;
  groundingStrength: string;
  criticFlags: string[];
  unsupportedClaimWarnings: string[];
  proceduralDependencies: string[];
  memoryUsageCount: number;
  finalConfidenceScore: number | null;
  recommendations: string[];
}

interface ApiCaseQualitySummary {
  caseId: string;
  recentRunCount: number;
  averageRunConfidence: number | null;
  latestRunQuality: ApiChamberRunQuality | null;
  groundedRunCount: number;
  criticalWarningCount: number;
  qualityWarnings: string[];
}

interface ApiEvaluationReport {
  id: string;
  reportType: string;
  title: string;
  taskName: string | null;
  datasetId: string | null;
  modelId: string | null;
  payloadJson: Record<string, unknown>;
  markdownPath: string | null;
  createdAt: string;
}

interface ApiTier1ImportResult {
  status: string;
  message: string;
  sourceType: string;
  sourceName: string;
  importedCount: number;
  updatedCount: number;
  skippedCount: number;
  labelCount: number;
  warnings: string[];
  metadataJson: Record<string, unknown>;
}

interface ApiTier1Document {
  id: string;
  sourceType: string;
  sourceName: string;
  externalId: string;
  filePath: string;
  title: string;
  rawText: string;
  normalizedText: string;
  language: string;
  documentType: string;
  court: string;
  date: string;
  citation: string;
  caseNumber: string;
  parties: string;
  metadataJson: Record<string, unknown>;
  importStatus: string;
  createdAt: string;
  updatedAt: string;
}

interface ApiTier1Label {
  id: string;
  documentId: string;
  documentTitle: string;
  taskName: string;
  label: string;
  labelSource: string;
  confidenceScore: number;
  evidenceText: string;
  ruleName: string;
  needsReview: boolean;
  reviewed: boolean;
  reviewerNote: string;
  createdAt: string;
  updatedAt: string;
}

interface ApiTier1Readiness {
  taskName: string;
  status: string;
  totalLabels: number;
  reviewedLabels: number;
  weakLabels: number;
  usableLabels: number;
  classDistribution: Record<string, number>;
  splitCounts: Record<string, number>;
  warnings: string[];
  recommendations: string[];
}

interface ApiTier1DatasetBuildResult {
  status: string;
  message: string;
  datasets: Array<Record<string, unknown>>;
  warnings: string[];
}

interface ApiTier1ExportResult {
  status: string;
  message: string;
  exportDir: string;
  zipPath: string;
  datasetCounts: Record<string, Record<string, number>>;
  warnings: string[];
}

interface ApiTier1Report {
  generatedAt: string;
  documentCount: number;
  labelCount: number;
  sourceTypeCounts: Record<string, number>;
  languageCounts: Record<string, number>;
  reviewCounts: Record<string, number>;
  readiness: ApiTier1Readiness[];
}

interface ApiAgentActivity {
  stepId: string;
  runId: string;
  caseId: string;
  caseTitle: string;
  agentName: string;
  taskLabel: string;
  status: string;
  outputSummary: string;
  confidenceScore: number | null;
  completedAt: string | null;
}

interface ApiIntelligenceArtifact {
  id: string;
  caseId: string;
  documentId?: string | null;
  artifactType: string;
  title: string;
  content: string;
  structuredJson: Record<string, unknown>;
  source: string;
  status: string;
  groundingStatus: string;
  legalSources: ApiGroundingSource[];
  createdAt: string;
  updatedAt: string;
}

interface ApiCaseDetail extends ApiCase {
  documents: ApiDocument[];
  timeline: ApiTimelineEvent[];
  notes: ApiNote[];
  research: ApiResearchEntry[];
  drafts: ApiDraft[];
  agentOutputs: ApiAgentOutput[];
  intelligence: ApiIntelligenceArtifact[];
  runs: ApiChamberRunSummary[];
  legalBasis: ApiGroundingSource[];
  predictions?: ApiCasePrediction[];
}

interface ApiActivity {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  category: string;
}

interface ApiDeadline {
  id: string;
  caseId: string;
  title: string;
  dueDate: string;
  owner: string;
  severity: string;
  note: string;
}

interface ApiNotification {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  tone: "info" | "warning" | "success";
}

interface ApiDashboardSummary {
  activeCaseCount: number;
  urgentDeadlinesCount: number;
  pendingFilingsCount: number;
  uploadedDocumentsCount: number;
  recentActivity: ApiActivity[];
  upcomingHearings: ApiDeadline[];
  urgentDeadlines: ApiDeadline[];
  notifications: ApiNotification[];
  recentCases: ApiCase[];
}

interface ApiGeneratedCaseArtifacts {
  artifacts: ApiIntelligenceArtifact[];
  agentOutput: ApiAgentOutput;
}

interface ApiGeneratedDraft {
  draft: ApiDraft;
  artifact: ApiIntelligenceArtifact;
  agentOutput: ApiAgentOutput;
}

interface ApiGeneratedResearch {
  researchEntry: ApiResearchEntry;
  artifact: ApiIntelligenceArtifact;
  agentOutput: ApiAgentOutput;
}

export interface CaseMutationInput {
  title: string;
  caseNumber: string;
  forum: string;
  matterType: string;
  status: string;
  priority: string;
  client: string;
  opposingParty: string;
  summary: string;
  nextHearingDate: string | null;
  stage: string;
  assignedCounsel: string[];
  issues?: string[];
  reliefSought?: string[];
  riskFlags?: string[];
  tags?: string[];
  importantNotes?: string[];
}

export interface NoteMutationInput {
  title: string;
  content: string;
  noteType: string;
  author: string;
}

export interface TimelineMutationInput {
  title: string;
  type: string;
  description: string;
  actor: string;
  date: string;
}

export interface DraftMutationInput {
  title: string;
  type: string;
  status: string;
  content: string;
  version: number;
  owner: string;
  summary: string;
}

export interface ResearchMutationInput {
  title: string;
  query: string;
  summary: string;
  citations: string[];
  sourceType: string;
  status: string;
  author: string;
  nextQuestion: string;
}

export interface AgentLogMutationInput {
  agentName: string;
  title: string;
  taskType: string;
  inputSummary: string;
  outputSummary: string;
  status: string;
  confidenceScore: number | null;
  citations: string[];
  nextAction: string;
}

export interface DocumentUploadInput {
  caseId: string;
  name: string;
  type: string;
  status: string;
  category: string;
  tags: string[];
  summary: string;
  filedBy: string;
  previewText: string;
  pages: number;
  file: File;
}

export interface IntelligenceGenerationInput {
  documentIds?: string[];
  instructions?: string;
}

export interface DraftGenerationInput extends IntelligenceGenerationInput {
  draftType: string;
}

export interface ResearchGenerationInput extends IntelligenceGenerationInput {
  issue?: string;
}

export interface ChamberRunCreateInput {
  instruction: string;
  taskType?: ChamberTaskType;
  selectedWorkflow?: string;
}

export interface MlTrainInput {
  datasetId: string;
  modelFamily: MlModelFamily;
  modelName?: string;
  hyperparameters?: Record<string, unknown>;
}

export interface MlPredictInput {
  caseId: string;
  taskName?: MlTaskName;
  modelId?: string;
}

export interface RetrievalSearchInput {
  query: string;
  taskType?: ChamberTaskType;
  caseId?: string;
  language?: string;
  limit?: number;
}

function mapCase(apiCase: ApiCase): CaseMatter {
  return {
    id: apiCase.id,
    title: apiCase.title,
    caseNumber: apiCase.caseNumber,
    forum: apiCase.forum,
    matterType: apiCase.matterType,
    status: apiCase.status as CaseMatter["status"],
    priority: apiCase.priority as CaseMatter["priority"],
    client: apiCase.client,
    opposingParty: apiCase.opposingParty,
    summary: apiCase.summary,
    issues: apiCase.issues,
    reliefSought: apiCase.reliefSought,
    nextHearingDate: apiCase.nextHearingDate ?? "",
    assignedCounsel: apiCase.assignedCounsel,
    stage: apiCase.stage,
    teamAgents: [],
    importantNotes: apiCase.importantNotes,
    factsBackground: apiCase.factsBackground,
    linkedStatutes: apiCase.linkedStatutes,
    precedents: apiCase.precedents,
    linkedDocumentIds: [],
    timelineIds: [],
    researchNoteIds: [],
    draftArtifacts: [],
    riskFlags: apiCase.riskFlags,
    proceduralAlerts: apiCase.proceduralAlerts,
    tags: apiCase.tags,
    createdAt: apiCase.createdAt,
    updatedAt: apiCase.updatedAt,
  };
}

function mapDocument(apiDocument: ApiDocument): CaseDocument {
  const metadata = apiDocument.metadataJson ?? {};
  const pageExtractions = Array.isArray(metadata.pageExtractions)
    ? metadata.pageExtractions
        .map((page) => {
          if (!page || typeof page !== "object") {
            return null;
          }
          const record = page as Record<string, unknown>;
          return {
            pageNumber: Number(record.pageNumber ?? 0),
            method: String(record.method ?? ""),
            confidence:
              typeof record.confidence === "number" ? record.confidence : null,
            textPreview: String(record.textPreview ?? ""),
          };
        })
        .filter(
          (
            page,
          ): page is {
            pageNumber: number;
            method: string;
            confidence: number | null;
            textPreview: string;
          } => Boolean(page && page.method),
        )
    : [];

  return {
    id: apiDocument.id,
    caseId: apiDocument.caseId,
    name: apiDocument.name,
    type: apiDocument.type as CaseDocument["type"],
    category: apiDocument.category,
    uploadDate: apiDocument.uploadDate,
    status: apiDocument.status as CaseDocument["status"],
    extractionStatus: apiDocument.extractionStatus as CaseDocument["extractionStatus"],
    intelligenceStatus:
      apiDocument.intelligenceStatus as CaseDocument["intelligenceStatus"],
    tags: apiDocument.tags,
    pages: apiDocument.pages,
    filedBy: apiDocument.filedBy,
    summary: apiDocument.summary,
    previewText: apiDocument.previewText,
    extractedText: apiDocument.extractedText,
    extractionError: apiDocument.extractionError,
    processedAt: apiDocument.processedAt,
    fileName: apiDocument.fileName,
    filePath: apiDocument.filePath,
      fileUrl: buildApiUrl(apiDocument.fileUrl),
      mimeType: apiDocument.mimeType,
      ocrStatus: apiDocument.ocrStatus,
      ocrEngine:
        typeof metadata.ocrEngine === "string" ? metadata.ocrEngine : undefined,
      ocrOutcome:
        typeof metadata.ocrOutcome === "string" ? metadata.ocrOutcome : undefined,
      ocrConfidence:
        typeof metadata.ocrConfidence === "number"
          ? metadata.ocrConfidence
          : null,
      detectedLanguage:
        typeof metadata.detectedLanguage === "string"
          ? metadata.detectedLanguage
          : undefined,
      pageExtractions,
      parsingStatus: apiDocument.parsingStatus,
      metadataJson: apiDocument.metadataJson,
    caseTitle: apiDocument.caseTitle ?? undefined,
    caseNumber: apiDocument.caseNumber ?? undefined,
    caseForum: apiDocument.caseForum ?? undefined,
    casePriority: (apiDocument.casePriority as CaseDocument["casePriority"]) ?? undefined,
  };
}

function mapIntelligenceArtifact(
  artifact: ApiIntelligenceArtifact,
): IntelligenceArtifact {
  return {
    id: artifact.id,
    caseId: artifact.caseId,
    documentId: artifact.documentId ?? null,
    artifactType: artifact.artifactType as IntelligenceArtifact["artifactType"],
    title: artifact.title,
    content: artifact.content,
    structuredJson: artifact.structuredJson,
    source: artifact.source,
    status: artifact.status as IntelligenceArtifact["status"],
    groundingStatus: artifact.groundingStatus,
    legalSources: artifact.legalSources.map(mapGroundingSource),
    createdAt: artifact.createdAt,
    updatedAt: artifact.updatedAt,
  };
}

function mapGroundingSource(source: ApiGroundingSource): GroundingSource {
  return {
    sourceId: source.sourceId,
    chunkId: source.chunkId,
    title: source.title,
    shortTitle: source.shortTitle,
    citationLabel: source.citationLabel,
    sourceType: source.sourceType,
    category: source.category,
    actName: source.actName,
    sectionLabel: source.sectionLabel,
    language: source.language,
    sourceOrigin: source.sourceOrigin,
    sourceUrl: source.sourceUrl,
    excerpt: source.excerpt,
    relevanceScore: source.relevanceScore ?? null,
    lexicalScore: source.lexicalScore ?? null,
    semanticScore: source.semanticScore ?? null,
    rerankScore: source.rerankScore ?? null,
    retrievalMode: source.retrievalMode ?? "Lexical",
    explanation: source.explanation ?? "",
    usageType: source.usageType as GroundingSource["usageType"],
  };
}

function mapCrawlSource(source: ApiCrawlSource): CrawlSource {
  return {
    id: source.id,
    name: source.name,
    sourceType: source.sourceType as CrawlSource["sourceType"],
    baseUrl: source.baseUrl,
    allowedDomains: source.allowedDomains,
    crawlMode: source.crawlMode as CrawlSource["crawlMode"],
    languageHint: source.languageHint,
    category: source.category,
    isActive: source.isActive,
    configJson: source.configJson,
    createdAt: source.createdAt,
    updatedAt: source.updatedAt,
  };
}

function mapCrawlJob(job: ApiCrawlJob): CrawlJob {
  return {
    id: job.id,
    sourceId: job.sourceId,
    sourceName: job.sourceName,
    status: job.status as CrawlJob["status"],
    startedAt: job.startedAt,
    completedAt: job.completedAt,
    pagesFetched: job.pagesFetched,
    documentsDiscovered: job.documentsDiscovered,
    documentsSaved: job.documentsSaved,
    errorsCount: job.errorsCount,
    metadataJson: job.metadataJson,
  };
}

function mapCrawledDocument(document: ApiCrawledDocument): CrawledDocument {
  return {
    id: document.id,
    sourceId: document.sourceId,
    sourceName: document.sourceName,
    legalSourceId: document.legalSourceId,
    sourceUrl: document.sourceUrl,
    title: document.title,
    documentType: document.documentType,
    language: document.language,
    jurisdiction: document.jurisdiction,
    rawHtmlPath: document.rawHtmlPath,
    rawHtmlUrl: document.rawHtmlUrl ? buildApiUrl(document.rawHtmlUrl) : "",
    downloadedFilePath: document.downloadedFilePath,
    downloadedFileUrl: document.downloadedFileUrl
      ? buildApiUrl(document.downloadedFileUrl)
      : "",
    mimeType: document.mimeType,
    crawlStatus: document.crawlStatus as CrawledDocument["crawlStatus"],
    processingStatus:
      document.processingStatus as CrawledDocument["processingStatus"],
    duplicateHash: document.duplicateHash,
    extractedText: document.extractedText,
    extractedTextPreview: document.extractedTextPreview,
    normalizedText: document.normalizedText,
    ocrEngine: document.ocrEngine,
    ocrStatus: document.ocrStatus,
    ocrConfidenceSummary: document.ocrConfidenceSummary,
    languageDetected: document.languageDetected,
    pageCount: document.pageCount,
    errorsJson: document.errorsJson,
    processedAt: document.processedAt,
    metadataJson: document.metadataJson,
    createdAt: document.createdAt,
    updatedAt: document.updatedAt,
  };
}

function mapCorpusEntry(entry: ApiCorpusEntry): CorpusEntry {
  return {
    id: entry.id,
    sourceKind: entry.sourceKind as CorpusEntry["sourceKind"],
    crawledDocumentId: entry.crawledDocumentId,
    legalSourceId: entry.legalSourceId,
    title: entry.title,
    language: entry.language,
    normalizedText: entry.normalizedText,
    chunkCount: entry.chunkCount,
    readyForRetrieval: entry.readyForRetrieval,
    readyForTraining: entry.readyForTraining,
    datasetSplit: entry.datasetSplit as CorpusEntry["datasetSplit"],
    metadataJson: entry.metadataJson,
    createdAt: entry.createdAt,
    updatedAt: entry.updatedAt,
  };
}

function mapMlDataset(dataset: ApiMlDataset): MlDataset {
  return {
    id: dataset.id,
    taskName: dataset.taskName as MlDataset["taskName"],
    name: dataset.name,
    version: dataset.version,
    status: dataset.status as MlDataset["status"],
    recordCount: dataset.recordCount,
    labelStrategy: dataset.labelStrategy,
    splitStrategy: dataset.splitStrategy,
    dataPath: dataset.dataPath,
    reportPath: dataset.reportPath,
    reportJson: dataset.reportJson,
    notes: dataset.notes,
    metadataJson: dataset.metadataJson,
    createdAt: dataset.createdAt,
    updatedAt: dataset.updatedAt,
  };
}

function mapDatasetReadiness(item: ApiDatasetReadiness): DatasetReadiness {
  return {
    datasetId: item.datasetId,
    taskName: item.taskName,
    datasetName: item.datasetName,
    datasetVersion: item.datasetVersion,
    status: item.status as DatasetReadiness["status"],
    score: item.score,
    totalExamples: item.totalExamples,
    uniqueCases: item.uniqueCases,
    classDistribution: item.classDistribution,
    classImbalanceRatio: item.classImbalanceRatio,
    splitCounts: item.splitCounts,
    labelSourceDistribution: item.labelSourceDistribution,
    languageDistribution: item.languageDistribution,
    sourceViewDistribution: item.sourceViewDistribution,
    missingTextExamples: item.missingTextExamples,
    nearEmptyExamples: item.nearEmptyExamples,
    duplicateExamples: item.duplicateExamples,
    weakLabelPercentage: item.weakLabelPercentage,
    lowOcrConfidencePercentage: item.lowOcrConfidencePercentage,
    leakageCaseCount: item.leakageCaseCount,
    leakageCaseIds: item.leakageCaseIds,
    warnings: item.warnings,
    recommendations: item.recommendations,
  };
}

function mapMlModel(model: ApiMlModel): MlModel {
  return {
    id: model.id,
    datasetId: model.datasetId,
    taskName: model.taskName as MlModel["taskName"],
    modelFamily: model.modelFamily as MlModel["modelFamily"],
    name: model.name,
    status: model.status as MlModel["status"],
    artifactPath: model.artifactPath,
    metricsPath: model.metricsPath,
    metricsJson: model.metricsJson,
    configJson: model.configJson,
    labelSchema: model.labelSchema,
    trainingSummary: model.trainingSummary,
    metadataJson: model.metadataJson,
    createdAt: model.createdAt,
    updatedAt: model.updatedAt,
  };
}

function mapMlModelDiagnostics(model: ApiMlModelDiagnostics): MlModelDiagnostics {
  return {
    modelId: model.modelId,
    taskName: model.taskName as MlTaskName,
    modelFamily: model.modelFamily as MlModelFamily,
    modelName: model.modelName,
    diagnostics: model.diagnostics,
  };
}

function mapMlLeaderboardEntry(entry: ApiMlLeaderboardEntry): MlLeaderboardEntry {
  return {
    modelId: entry.modelId,
    name: entry.name,
    modelFamily: entry.modelFamily as MlLeaderboardEntry["modelFamily"],
    primaryMetric: entry.primaryMetric,
    metricsJson: entry.metricsJson,
    createdAt: entry.createdAt,
  };
}

function mapMlTaskLeaderboard(leaderboard: ApiMlTaskLeaderboard): MlTaskLeaderboard {
  return {
    taskName: leaderboard.taskName as MlTaskLeaderboard["taskName"],
    entries: leaderboard.entries.map(mapMlLeaderboardEntry),
  };
}

function mapCasePrediction(prediction: ApiCasePrediction): CasePrediction {
  return {
    id: prediction.id,
    caseId: prediction.caseId,
    modelId: prediction.modelId,
    taskName: prediction.taskName as CasePrediction["taskName"],
    predictedLabel: prediction.predictedLabel,
    confidence: prediction.confidence,
    probabilitiesJson: prediction.probabilitiesJson,
    inputSummary: prediction.inputSummary,
    warningText: prediction.warningText,
    metadataJson: prediction.metadataJson,
    createdAt: prediction.createdAt,
    modelName: prediction.modelName,
    modelFamily: prediction.modelFamily as CasePrediction["modelFamily"],
    datasetId: prediction.datasetId,
  };
}

function mapPredictionExplanation(item: ApiPredictionExplanation): PredictionExplanation {
  return {
    predictionId: item.predictionId,
    taskName: item.taskName as MlTaskName,
    predictedLabel: item.predictedLabel,
    confidence: item.confidence,
    modelFamily: item.modelFamily,
    modelName: item.modelName,
    explanationNote: item.explanationNote,
    topProbabilities: item.topProbabilities,
    structuredSignals: item.structuredSignals,
    diagnostics: item.diagnostics,
  };
}

function mapCalibrationRecord(item: ApiCalibrationRecord): CalibrationRecord {
  return {
    modelId: item.modelId,
    taskName: item.taskName,
    calibrationMethod: item.calibrationMethod,
    sampleCount: item.sampleCount,
    hasCalibratedScores: item.hasCalibratedScores,
    supportedMethods: item.supportedMethods,
    metricsJson: item.metricsJson,
    reliabilityJson: item.reliabilityJson,
    notes: item.notes,
    createdAt: item.createdAt,
  };
}

function mapTimeline(entry: ApiTimelineEvent): TimelineEntry {
  return {
    id: entry.id,
    caseId: entry.caseId,
    date: entry.date,
    title: entry.title,
    description: entry.description,
    actor: entry.actor,
    type: entry.type as TimelineEntry["type"],
  };
}

function mapNote(note: ApiNote): NoteEntry {
  return {
    id: note.id,
    caseId: note.caseId,
    title: note.title,
    content: note.content,
    noteType: note.noteType,
    author: note.author,
    createdAt: note.createdAt,
    updatedAt: note.updatedAt,
  };
}

function mapResearch(entry: ApiResearchEntry): ResearchNote {
  return {
    id: entry.id,
    caseId: entry.caseId,
    title: entry.title,
    status: entry.status as ResearchNote["status"],
    author: entry.author,
    updatedAt: entry.updatedAt,
    query: entry.query,
    sourceType: entry.sourceType,
    authorities: entry.citations,
    summary: entry.summary,
    nextQuestion: entry.nextQuestion,
  };
}

function mapDraft(draft: ApiDraft): DraftArtifact {
  return {
    id: draft.id,
    title: draft.title,
    type: draft.type,
    status: draft.status as DraftArtifact["status"],
    updatedAt: draft.updatedAt,
    createdAt: draft.createdAt,
    owner: draft.owner,
    summary: draft.summary,
    content: draft.content,
    version: draft.version,
  };
}

function mapAgentOutput(output: ApiAgentOutput): AgentOutput {
  return {
    id: output.id,
    caseId: output.caseId,
    agentId: output.agentName,
    title: output.title || `${output.agentName} / ${output.taskType}`,
    generatedAt: output.completedAt ?? output.startedAt,
    confidence: output.confidence,
    rawStatus: output.status,
    taskType: output.taskType,
    inputSummary: output.inputSummary,
    confidenceScore: output.confidenceScore ?? null,
    status: output.status === "Completed" ? "Published" : "Needs Review",
    summary: output.outputSummary,
    citations: output.citations,
    nextAction: output.nextAction,
  };
}

function mapMemorySource(source: ApiMemorySource): MemorySource {
  return {
    sourceId: source.sourceId,
    sourceType: source.sourceType,
    title: source.title,
    detail: source.detail,
    excerpt: source.excerpt,
  };
}

function mapChamberRunStep(step: ApiChamberRunStep): ChamberRunStep {
  return {
    id: step.id,
    runId: step.runId,
    stepOrder: step.stepOrder,
    agentName: step.agentName,
    taskLabel: step.taskLabel,
    inputSummary: step.inputSummary,
    outputSummary: step.outputSummary,
    fullOutput: step.fullOutput,
    structuredJson: step.structuredJson,
    status: step.status as ChamberRunStep["status"],
    confidenceScore: step.confidenceScore ?? null,
    sourceArtifactIds: step.sourceArtifactIds,
    metadataJson: step.metadataJson,
    createdAt: step.createdAt,
    completedAt: step.completedAt,
  };
}

function mapChamberRunSummary(run: ApiChamberRunSummary): ChamberRunSummary {
  return {
    id: run.id,
    caseId: run.caseId,
    taskType: run.taskType as ChamberRunSummary["taskType"],
    userInstruction: run.userInstruction,
    selectedWorkflow: run.selectedWorkflow,
    status: run.status as ChamberRunSummary["status"],
    finalSummary: run.finalSummary,
    confidenceScore: run.confidenceScore ?? null,
    agentNames: run.agentNames,
    memorySources: run.memorySources.map(mapMemorySource),
    criticSummary: run.criticSummary,
    finalArtifactId: run.finalArtifactId,
    linkedDraftId: run.linkedDraftId,
    linkedResearchEntryId: run.linkedResearchEntryId,
    groundingStatus: run.groundingStatus,
    retrievalMode: run.retrievalMode,
    retrievalDiagnostics: run.retrievalDiagnostics ?? {},
    legalRetrievalQuery: run.legalRetrievalQuery,
    legalSourceCount: run.legalSourceCount,
    legalSources: run.legalSources.map(mapGroundingSource),
    startedAt: run.startedAt,
    completedAt: run.completedAt,
  };
}

function mapEmbeddingIndex(item: ApiEmbeddingIndexMetadata): EmbeddingIndexMetadata {
  return {
    id: item.id,
    name: item.name,
    retrievalMode: item.retrievalMode as RetrievalMode,
    modelName: item.modelName,
    status: item.status as EmbeddingIndexMetadata["status"],
    corpusVersion: item.corpusVersion,
    indexPath: item.indexPath,
    vectorDimension: item.vectorDimension,
    sourceCount: item.sourceCount,
    metadataJson: item.metadataJson,
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
  };
}

function mapRetrievalSearchResult(item: ApiRetrievalSearchResult): RetrievalSearchResult {
  return {
    query: item.query,
    mode: item.mode as RetrievalMode,
    status: item.status,
    summary: item.summary,
    diagnostics: item.diagnostics,
    sources: item.sources.map(mapGroundingSource),
  };
}

function mapRetrievalLeaderboard(item: ApiRetrievalLeaderboard): RetrievalLeaderboard {
  return {
    generatedAt: item.generatedAt,
    entries: item.entries.map((entry) => ({
      mode: entry.mode,
      query: entry.query,
      topLabels: entry.topLabels,
      sourceTypeMix: entry.sourceTypeMix,
      averageScore: entry.averageScore,
      diagnostics: entry.diagnostics,
    })),
  };
}

function mapRetrievalBenchmarkRun(item: ApiRetrievalBenchmarkRun): RetrievalBenchmarkRun {
  return {
    id: item.id,
    name: item.name,
    retrievalModesCompared: item.retrievalModesCompared,
    queryCount: item.queryCount,
    metricsJson: item.metricsJson,
    createdAt: item.createdAt,
    results: item.results.map((result) => ({
      query: result.query,
      taskType: result.taskType,
      mode: result.mode,
      topK: result.topK,
      expectedLabels: result.expectedLabels,
      metricsJson: result.metricsJson,
      resultsJson: result.resultsJson,
      diagnostics: result.diagnostics,
    })),
  };
}

function mapRunGroundingDiagnostics(item: ApiRunGroundingDiagnostics): RunGroundingDiagnostics {
  return {
    runId: item.runId,
    retrievalMode: item.retrievalMode,
    groundingStatus: item.groundingStatus,
    diagnostics: item.diagnostics,
    sources: item.sources.map(mapGroundingSource),
  };
}

function mapChamberRunQuality(item: ApiChamberRunQuality): ChamberRunQuality {
  return {
    runId: item.runId,
    caseId: item.caseId,
    status: item.status,
    retrievalMode: item.retrievalMode,
    sourceCountRetrieved: item.sourceCountRetrieved,
    sourceCountReliedOn: item.sourceCountReliedOn,
    groundingStrength: item.groundingStrength,
    criticFlags: item.criticFlags,
    unsupportedClaimWarnings: item.unsupportedClaimWarnings,
    proceduralDependencies: item.proceduralDependencies,
    memoryUsageCount: item.memoryUsageCount,
    finalConfidenceScore: item.finalConfidenceScore,
    recommendations: item.recommendations,
  };
}

function mapCaseQualitySummary(item: ApiCaseQualitySummary): CaseQualitySummary {
  return {
    caseId: item.caseId,
    recentRunCount: item.recentRunCount,
    averageRunConfidence: item.averageRunConfidence,
    latestRunQuality: item.latestRunQuality
      ? mapChamberRunQuality(item.latestRunQuality)
      : null,
    groundedRunCount: item.groundedRunCount,
    criticalWarningCount: item.criticalWarningCount,
    qualityWarnings: item.qualityWarnings,
  };
}

function mapEvaluationReport(item: ApiEvaluationReport): EvaluationReport {
  return {
    id: item.id,
    reportType: item.reportType,
    title: item.title,
    taskName: item.taskName,
    datasetId: item.datasetId,
    modelId: item.modelId,
    payloadJson: item.payloadJson,
    markdownPath: item.markdownPath,
    createdAt: item.createdAt,
  };
}

function mapTier1ImportResult(item: ApiTier1ImportResult): Tier1ImportResult {
  return item;
}

function mapTier1Document(item: ApiTier1Document): Tier1Document {
  return item;
}

function mapTier1Label(item: ApiTier1Label): Tier1Label {
  return {
    ...item,
    taskName: item.taskName as MlTaskName,
  };
}

function mapTier1Readiness(item: ApiTier1Readiness): Tier1Readiness {
  return {
    ...item,
    taskName: item.taskName as MlTaskName,
  };
}

function mapTier1DatasetBuildResult(item: ApiTier1DatasetBuildResult): Tier1DatasetBuildResult {
  return item;
}

function mapTier1ExportResult(item: ApiTier1ExportResult): Tier1ExportResult {
  return item;
}

function mapTier1Report(item: ApiTier1Report): Tier1Report {
  return {
    ...item,
    readiness: item.readiness.map(mapTier1Readiness),
  };
}

function mapChamberRun(run: ApiChamberRun): ChamberRun {
  return {
    ...mapChamberRunSummary(run),
    finalOutput: run.finalOutput,
    steps: run.steps.map(mapChamberRunStep),
    metadataJson: run.metadataJson,
  };
}

function mapAgentActivity(item: ApiAgentActivity): AgentActivity {
  return {
    stepId: item.stepId,
    runId: item.runId,
    caseId: item.caseId,
    caseTitle: item.caseTitle,
    agentName: item.agentName,
    taskLabel: item.taskLabel,
    status: item.status as AgentActivity["status"],
    outputSummary: item.outputSummary,
    confidenceScore: item.confidenceScore ?? null,
    completedAt: item.completedAt,
  };
}

function mapActivity(item: ApiActivity): ActivityItem {
  return {
    id: item.id,
    title: item.title,
    detail: item.detail,
    timestamp: item.timestamp,
    category: item.category as ActivityItem["category"],
  };
}

function mapDeadline(item: ApiDeadline): Deadline {
  return {
    id: item.id,
    caseId: item.caseId,
    title: item.title,
    dueDate: item.dueDate,
    owner: item.owner,
    severity: item.severity as Deadline["severity"],
    note: item.note,
  };
}

function mapNotification(item: ApiNotification): NotificationItem {
  return {
    id: item.id,
    title: item.title,
    detail: item.detail,
    timestamp: item.timestamp,
    tone: item.tone,
  };
}

function buildCasePayload(input: CaseMutationInput) {
  return {
    title: input.title,
    caseNumber: input.caseNumber,
    forum: input.forum,
    matterType: input.matterType,
    status: input.status,
    priority: input.priority,
    client: input.client,
    opposingParty: input.opposingParty,
    summary: input.summary,
    issues: input.issues ?? [],
    reliefSought: input.reliefSought ?? [],
    nextHearingDate: input.nextHearingDate || null,
    assignedCounsel: input.assignedCounsel,
    stage: input.stage,
    riskFlags: input.riskFlags ?? [],
    importantNotes: input.importantNotes ?? [],
    factsBackground: [],
    linkedStatutes: [],
    precedents: [],
    proceduralAlerts: [],
    tags: input.tags ?? [],
  };
}

export async function getDashboardSummary(): Promise<DashboardSummaryData> {
  const payload = await apiRequest<ApiDashboardSummary>("/api/dashboard/summary");
  return {
    activeCaseCount: payload.activeCaseCount,
    urgentDeadlinesCount: payload.urgentDeadlinesCount,
    pendingFilingsCount: payload.pendingFilingsCount,
    uploadedDocumentsCount: payload.uploadedDocumentsCount,
    recentActivity: payload.recentActivity.map(mapActivity),
    upcomingHearings: payload.upcomingHearings.map(mapDeadline),
    urgentDeadlines: payload.urgentDeadlines.map(mapDeadline),
    notifications: payload.notifications.map(mapNotification),
    recentCases: payload.recentCases.map(mapCase),
  };
}

export async function getCases(): Promise<CaseMatter[]> {
  const payload = await apiRequest<ApiCase[]>("/api/cases");
  return payload.map(mapCase);
}

export async function createCase(input: CaseMutationInput): Promise<CaseMatter> {
  const payload = await apiJson<ApiCase, ReturnType<typeof buildCasePayload>>(
    "/api/cases",
    "POST",
    buildCasePayload(input),
  );
  return mapCase(payload);
}

export async function updateCase(
  caseId: string,
  input: CaseMutationInput,
): Promise<CaseMatter> {
  const payload = await apiJson<ApiCase, ReturnType<typeof buildCasePayload>>(
    `/api/cases/${caseId}`,
    "PATCH",
    buildCasePayload(input),
  );
  return mapCase(payload);
}

export async function archiveCase(caseId: string): Promise<void> {
  await apiJson<void>(`/api/cases/${caseId}`, "DELETE");
}

export async function getCaseDetail(caseId: string): Promise<CaseDetailData> {
  const payload = await apiRequest<ApiCaseDetail>(`/api/cases/${caseId}`);
  const drafts = payload.drafts.map(mapDraft);
  const agentOutputs = payload.agentOutputs.map(mapAgentOutput);
  const caseItem = mapCase(payload);

  caseItem.draftArtifacts = drafts;
  caseItem.teamAgents = Array.from(
    new Set(agentOutputs.map((item) => item.agentId)),
  );

  return {
    caseItem,
    documents: payload.documents.map(mapDocument),
    timeline: payload.timeline.map(mapTimeline),
    notes: payload.notes.map(mapNote),
    research: payload.research.map(mapResearch),
    drafts,
    agentOutputs,
    intelligence: payload.intelligence.map(mapIntelligenceArtifact),
    runs: payload.runs.map(mapChamberRunSummary),
    legalBasis: payload.legalBasis.map(mapGroundingSource),
    predictions: (payload.predictions ?? []).map(mapCasePrediction),
  };
}

export async function createNote(
  caseId: string,
  input: NoteMutationInput,
): Promise<NoteEntry> {
  const payload = await apiJson<ApiNote, NoteMutationInput>(
    `/api/cases/${caseId}/notes`,
    "POST",
    input,
  );
  return mapNote(payload);
}

export async function updateNote(
  noteId: string,
  input: Partial<NoteMutationInput>,
): Promise<NoteEntry> {
  const payload = await apiJson<ApiNote, Partial<NoteMutationInput>>(
    `/api/notes/${noteId}`,
    "PATCH",
    input,
  );
  return mapNote(payload);
}

export async function createTimelineEvent(
  caseId: string,
  input: TimelineMutationInput,
): Promise<TimelineEntry> {
  const payload = await apiJson<ApiTimelineEvent, TimelineMutationInput>(
    `/api/cases/${caseId}/timeline`,
    "POST",
    input,
  );
  return mapTimeline(payload);
}

export async function createResearchEntry(
  caseId: string,
  input: ResearchMutationInput,
): Promise<ResearchNote> {
  const payload = await apiJson<ApiResearchEntry, ResearchMutationInput>(
    `/api/cases/${caseId}/research`,
    "POST",
    input,
  );
  return mapResearch(payload);
}

export async function getResearchHealth(): Promise<ResearchHealth> {
  return apiRequest<ResearchHealth>("/api/research/health");
}

export async function runResearchWorkflow(
  input: ResearchWorkflowRequest,
): Promise<ResearchWorkflowResponse> {
  return apiJson<ResearchWorkflowResponse, ResearchWorkflowRequest>(
    "/api/research/runs",
    "POST",
    input,
  );
}

export async function getResearchRun(
  runId: string,
): Promise<ResearchWorkflowResponse> {
  return apiRequest<ResearchWorkflowResponse>(`/api/research/runs/${runId}`);
}

export async function listCaseResearchRuns(
  caseId: string,
): Promise<ResearchRunSummary[]> {
  return apiRequest<ResearchRunSummary[]>(`/api/research/cases/${caseId}/runs`);
}

export async function getResearchMarkdown(runId: string): Promise<string> {
  return apiText(`/api/research/runs/${runId}/markdown`);
}

export function getResearchMarkdownUrl(runId: string) {
  return buildApiUrl(`/api/research/runs/${runId}/markdown`);
}

export function getResearchPdfUrl(runId: string) {
  return buildApiUrl(`/api/research/runs/${runId}/pdf`);
}

export async function createDraft(
  caseId: string,
  input: DraftMutationInput,
): Promise<DraftArtifact> {
  const payload = await apiJson<ApiDraft, DraftMutationInput>(
    `/api/cases/${caseId}/drafts`,
    "POST",
    input,
  );
  return mapDraft(payload);
}

export async function updateDraft(
  draftId: string,
  input: Partial<DraftMutationInput>,
): Promise<DraftArtifact> {
  const payload = await apiJson<ApiDraft, Partial<DraftMutationInput>>(
    `/api/drafts/${draftId}`,
    "PATCH",
    input,
  );
  return mapDraft(payload);
}

export async function createAgentLog(
  caseId: string,
  input: AgentLogMutationInput,
): Promise<AgentOutput> {
  const payload = await apiJson<
    ApiAgentOutput,
    Omit<AgentLogMutationInput, "confidenceScore"> & {
      confidenceScore?: number | null;
      startedAt?: string;
      completedAt?: string | null;
    }
  >(`/api/cases/${caseId}/agent-logs`, "POST", {
    ...input,
    confidenceScore: input.confidenceScore,
    startedAt: new Date().toISOString(),
    completedAt:
      input.status === "Completed" || input.status === "Needs Review"
        ? new Date().toISOString()
        : null,
  });
  return mapAgentOutput(payload);
}

export async function getDocuments(): Promise<CaseDocument[]> {
  const payload = await apiRequest<ApiDocument[]>("/api/documents");
  return payload.map(mapDocument);
}

export async function uploadDocument(
  input: DocumentUploadInput,
): Promise<CaseDocument> {
  const formData = new FormData();
  formData.append("caseId", input.caseId);
  formData.append("name", input.name);
  formData.append("type", input.type);
  formData.append("status", input.status);
  formData.append("category", input.category);
  formData.append("tags", input.tags.join(", "));
  formData.append("extractionStatus", "Ready for Indexing");
  formData.append("ocrStatus", "Not Started");
  formData.append("parsingStatus", "Not Started");
  formData.append("previewText", input.previewText);
  formData.append("summary", input.summary);
  formData.append("filedBy", input.filedBy);
  formData.append("pages", String(input.pages));
  formData.append("file", input.file);

  const payload = await apiFormData<ApiDocument>("/api/documents/upload", formData);
  return mapDocument(payload);
}

export async function processDocument(documentId: string): Promise<CaseDocument> {
  const payload = await apiJson<ApiDocument, undefined>(
    `/api/documents/${documentId}/process`,
    "POST",
  );
  return mapDocument(payload);
}

export async function getDocumentExtraction(
  documentId: string,
): Promise<CaseDocument> {
  const payload = await apiRequest<ApiDocument>(
    `/api/documents/${documentId}/extraction`,
  );
  return mapDocument(payload);
}

export async function getCrawlSources(): Promise<CrawlSource[]> {
  const payload = await apiRequest<ApiCrawlSource[]>("/api/crawl/sources");
  return payload.map(mapCrawlSource);
}

export async function getCrawlJobs(): Promise<CrawlJob[]> {
  const payload = await apiRequest<ApiCrawlJob[]>("/api/crawl/jobs");
  return payload.map(mapCrawlJob);
}

export async function runCrawl(sourceId: string): Promise<CrawlJob> {
  const payload = await apiJson<ApiCrawlJob, { sourceId: string }>(
    "/api/crawl/run",
    "POST",
    { sourceId },
  );
  return mapCrawlJob(payload);
}

export async function getCrawledDocuments(): Promise<CrawledDocument[]> {
  const payload = await apiRequest<ApiCrawledDocument[]>("/api/crawled-documents");
  return payload.map(mapCrawledDocument);
}

export async function processCrawledDocument(
  documentId: string,
): Promise<CrawledDocument> {
  const payload = await apiJson<ApiCrawledDocument, undefined>(
    `/api/crawled-documents/${documentId}/process`,
    "POST",
  );
  return mapCrawledDocument(payload);
}

export async function forceOcrCrawledDocument(
  documentId: string,
): Promise<CrawledDocument> {
  const payload = await apiJson<ApiCrawledDocument, undefined>(
    `/api/crawled-documents/${documentId}/ocr`,
    "POST",
  );
  return mapCrawledDocument(payload);
}

export async function getCorpusEntries(): Promise<CorpusEntry[]> {
  const payload = await apiRequest<ApiCorpusEntry[]>("/api/corpus/entries");
  return payload.map(mapCorpusEntry);
}

export async function buildCorpus(): Promise<CorpusBuildResult> {
  const payload = await apiJson<ApiCorpusBuildResult, undefined>(
    "/api/corpus/build",
    "POST",
  );
  return payload;
}

export async function exportCorpus(): Promise<CorpusExportResult> {
  const payload = await apiJson<ApiCorpusExportResult, undefined>(
    "/api/corpus/export",
    "POST",
  );
  return payload;
}

export async function buildRetrievalIndex(modelName?: string): Promise<EmbeddingIndexMetadata> {
  const payload = await apiJson<ApiEmbeddingIndexMetadata, { modelName?: string }>(
    "/api/retrieval/index/build",
    "POST",
    modelName ? { modelName } : {},
  );
  return mapEmbeddingIndex(payload);
}

export async function getRetrievalIndexStatus(): Promise<EmbeddingIndexMetadata | null> {
  const payload = await apiRequest<ApiEmbeddingIndexMetadata | null>("/api/retrieval/index/status");
  return payload ? mapEmbeddingIndex(payload) : null;
}

export async function semanticRetrievalSearch(
  input: RetrievalSearchInput,
): Promise<RetrievalSearchResult> {
  const payload = await apiJson<ApiRetrievalSearchResult, RetrievalSearchInput>(
    "/api/retrieval/search",
    "POST",
    input,
  );
  return mapRetrievalSearchResult(payload);
}

export async function hybridRetrievalSearch(
  input: RetrievalSearchInput,
): Promise<RetrievalSearchResult> {
  const payload = await apiJson<ApiRetrievalSearchResult, RetrievalSearchInput>(
    "/api/retrieval/hybrid-search",
    "POST",
    input,
  );
  return mapRetrievalSearchResult(payload);
}

export async function getRetrievalLeaderboard(): Promise<RetrievalLeaderboard> {
  const payload = await apiRequest<ApiRetrievalLeaderboard>("/api/retrieval/leaderboard");
  return mapRetrievalLeaderboard(payload);
}

export async function evaluateRetrieval(): Promise<RetrievalLeaderboard> {
  const payload = await apiJson<ApiRetrievalLeaderboard, undefined>(
    "/api/retrieval/evaluate",
    "POST",
  );
  return mapRetrievalLeaderboard(payload);
}

export async function runRetrievalBenchmark(input?: {
  name?: string;
  topK?: number;
}): Promise<RetrievalBenchmarkRun> {
  const payload = await apiJson<ApiRetrievalBenchmarkRun, { name?: string; topK?: number }>(
    "/api/retrieval/benchmarks/run",
    "POST",
    input ?? {},
  );
  return mapRetrievalBenchmarkRun(payload);
}

export async function getRetrievalBenchmarks(): Promise<RetrievalBenchmarkRun[]> {
  const payload = await apiRequest<ApiRetrievalBenchmarkRun[]>("/api/retrieval/benchmarks");
  return payload.map(mapRetrievalBenchmarkRun);
}

export async function getRetrievalBenchmark(benchmarkId: string): Promise<RetrievalBenchmarkRun> {
  const payload = await apiRequest<ApiRetrievalBenchmarkRun>(
    `/api/retrieval/benchmarks/${benchmarkId}`,
  );
  return mapRetrievalBenchmarkRun(payload);
}

export async function getMlDatasets(): Promise<MlDataset[]> {
  const payload = await apiRequest<ApiMlDataset[]>("/api/ml/datasets");
  return payload.map(mapMlDataset);
}

export async function getDatasetReadiness(): Promise<DatasetReadiness[]> {
  const payload = await apiRequest<ApiDatasetReadiness[]>("/api/evaluation/datasets/readiness");
  return payload.map(mapDatasetReadiness);
}

export async function getDatasetReadinessByDataset(datasetId: string): Promise<DatasetReadiness> {
  const payload = await apiRequest<ApiDatasetReadiness>(
    `/api/evaluation/datasets/${datasetId}/readiness`,
  );
  return mapDatasetReadiness(payload);
}

export async function buildMlDatasets(taskName?: MlTaskName): Promise<MlDataset[]> {
  const payload = await apiJson<ApiMlDataset[], { taskName?: MlTaskName; rebuild: boolean }>(
    "/api/ml/datasets/build",
    "POST",
    {
      taskName,
      rebuild: true,
    },
  );
  return payload.map(mapMlDataset);
}

export async function getMlModels(): Promise<MlModel[]> {
  const payload = await apiRequest<ApiMlModel[]>("/api/ml/models");
  return payload.map(mapMlModel);
}

export async function trainMlModel(input: MlTrainInput): Promise<MlModel> {
  const payload = await apiJson<ApiMlModel, MlTrainInput>("/api/ml/train", "POST", input);
  return mapMlModel(payload);
}

export async function getModelDiagnostics(modelId: string): Promise<MlModelDiagnostics> {
  const payload = await apiRequest<ApiMlModelDiagnostics>(`/api/ml/models/${modelId}/diagnostics`);
  return mapMlModelDiagnostics(payload);
}

export async function getModelCalibration(modelId: string): Promise<CalibrationRecord> {
  const payload = await apiRequest<ApiCalibrationRecord>(`/api/ml/models/${modelId}/calibration`);
  return mapCalibrationRecord(payload);
}

export async function buildModelCalibration(modelId: string): Promise<CalibrationRecord> {
  const payload = await apiJson<ApiCalibrationRecord, undefined>(
    `/api/ml/models/${modelId}/calibration/build`,
    "POST",
  );
  return mapCalibrationRecord(payload);
}

export async function getTaskLeaderboard(taskName: MlTaskName): Promise<MlTaskLeaderboard> {
  const payload = await apiRequest<ApiMlTaskLeaderboard>(`/api/ml/tasks/${taskName}/leaderboard`);
  return mapMlTaskLeaderboard(payload);
}

export async function predictCase(input: MlPredictInput): Promise<CasePrediction[]> {
  const payload = await apiJson<ApiCasePrediction[], MlPredictInput>(
    `/api/cases/${input.caseId}/predict`,
    "POST",
    input,
  );
  return payload.map(mapCasePrediction);
}

export async function getCasePredictions(caseId: string): Promise<CasePrediction[]> {
  const payload = await apiRequest<ApiCasePrediction[]>(`/api/cases/${caseId}/predictions`);
  return payload.map(mapCasePrediction);
}

export async function getCasePredictionExplanations(
  caseId: string,
): Promise<PredictionExplanation[]> {
  const payload = await apiRequest<ApiPredictionExplanation[]>(
    `/api/cases/${caseId}/predictions/explain`,
  );
  return payload.map(mapPredictionExplanation);
}

export async function getCaseIntelligence(
  caseId: string,
): Promise<IntelligenceArtifact[]> {
  const payload = await apiRequest<ApiIntelligenceArtifact[]>(
    `/api/cases/${caseId}/intelligence`,
  );
  return payload.map(mapIntelligenceArtifact);
}

export async function generateCaseSummary(
  caseId: string,
  input: IntelligenceGenerationInput = {},
): Promise<{ artifacts: IntelligenceArtifact[]; agentOutput: AgentOutput }> {
  const payload = await apiJson<ApiGeneratedCaseArtifacts, IntelligenceGenerationInput>(
    `/api/cases/${caseId}/generate-summary`,
    "POST",
    input,
  );
  return {
    artifacts: payload.artifacts.map(mapIntelligenceArtifact),
    agentOutput: mapAgentOutput(payload.agentOutput),
  };
}

export async function generateCaseIssues(
  caseId: string,
  input: IntelligenceGenerationInput = {},
): Promise<{ artifacts: IntelligenceArtifact[]; agentOutput: AgentOutput }> {
  const payload = await apiJson<ApiGeneratedCaseArtifacts, IntelligenceGenerationInput>(
    `/api/cases/${caseId}/generate-issues`,
    "POST",
    input,
  );
  return {
    artifacts: payload.artifacts.map(mapIntelligenceArtifact),
    agentOutput: mapAgentOutput(payload.agentOutput),
  };
}

export async function generateDraftAssistance(
  caseId: string,
  input: DraftGenerationInput,
): Promise<{
  draft: DraftArtifact;
  artifact: IntelligenceArtifact;
  agentOutput: AgentOutput;
}> {
  const payload = await apiJson<ApiGeneratedDraft, DraftGenerationInput>(
    `/api/cases/${caseId}/generate-draft`,
    "POST",
    input,
  );
  return {
    draft: mapDraft(payload.draft),
    artifact: mapIntelligenceArtifact(payload.artifact),
    agentOutput: mapAgentOutput(payload.agentOutput),
  };
}

export async function generateResearchNote(
  caseId: string,
  input: ResearchGenerationInput = {},
): Promise<{
  research: ResearchNote;
  artifact: IntelligenceArtifact;
  agentOutput: AgentOutput;
}> {
  const payload = await apiJson<ApiGeneratedResearch, ResearchGenerationInput>(
    `/api/cases/${caseId}/generate-research`,
    "POST",
    input,
  );
  return {
    research: mapResearch(payload.researchEntry),
    artifact: mapIntelligenceArtifact(payload.artifact),
    agentOutput: mapAgentOutput(payload.agentOutput),
  };
}

export async function createCaseRun(
  caseId: string,
  input: ChamberRunCreateInput,
): Promise<ChamberRun> {
  const payload = await apiJson<ApiChamberRun, ChamberRunCreateInput>(
    `/api/cases/${caseId}/runs`,
    "POST",
    input,
  );
  return mapChamberRun(payload);
}

export async function getCaseRuns(caseId: string): Promise<ChamberRunSummary[]> {
  const payload = await apiRequest<ApiChamberRunSummary[]>(`/api/cases/${caseId}/runs`);
  return payload.map(mapChamberRunSummary);
}

export async function getRun(runId: string): Promise<ChamberRun> {
  const payload = await apiRequest<ApiChamberRun>(`/api/runs/${runId}`);
  return mapChamberRun(payload);
}

export async function getRunGroundingDiagnostics(
  runId: string,
): Promise<RunGroundingDiagnostics> {
  const payload = await apiRequest<ApiRunGroundingDiagnostics>(
    `/api/runs/${runId}/grounding/diagnostics`,
  );
  return mapRunGroundingDiagnostics(payload);
}

export async function getRunQuality(runId: string): Promise<ChamberRunQuality> {
  const payload = await apiRequest<ApiChamberRunQuality>(`/api/runs/${runId}/quality`);
  return mapChamberRunQuality(payload);
}

export async function getCaseQualitySummary(caseId: string): Promise<CaseQualitySummary> {
  const payload = await apiRequest<ApiCaseQualitySummary>(`/api/cases/${caseId}/quality-summary`);
  return mapCaseQualitySummary(payload);
}

export async function getRunSteps(runId: string): Promise<ChamberRunStep[]> {
  const payload = await apiRequest<ApiChamberRunStep[]>(`/api/runs/${runId}/steps`);
  return payload.map(mapChamberRunStep);
}

export async function getAgentActivity(caseId?: string): Promise<AgentActivity[]> {
  const search = caseId ? `?caseId=${encodeURIComponent(caseId)}` : "";
  const payload = await apiRequest<ApiAgentActivity[]>(`/api/agents/activity${search}`);
  return payload.map(mapAgentActivity);
}

export async function buildEvaluationReport(title?: string): Promise<EvaluationReport> {
  const payload = await apiJson<ApiEvaluationReport, { title?: string }>(
    "/api/evaluation/reports/build",
    "POST",
    title ? { title } : {},
  );
  return mapEvaluationReport(payload);
}

export async function getEvaluationReports(): Promise<EvaluationReport[]> {
  const payload = await apiRequest<ApiEvaluationReport[]>("/api/evaluation/reports");
  return payload.map(mapEvaluationReport);
}

export async function getEvaluationReport(reportId: string): Promise<EvaluationReport> {
  const payload = await apiRequest<ApiEvaluationReport>(`/api/evaluation/reports/${reportId}`);
  return mapEvaluationReport(payload);
}

export async function importTier1Local(): Promise<Tier1ImportResult> {
  const payload = await apiJson<ApiTier1ImportResult, undefined>("/api/tier1/import/local", "POST");
  return mapTier1ImportResult(payload);
}

export async function importTier1Kaggle(): Promise<Tier1ImportResult> {
  const payload = await apiJson<ApiTier1ImportResult, undefined>("/api/tier1/import/kaggle", "POST");
  return mapTier1ImportResult(payload);
}

export async function importTier1HuggingFace(): Promise<Tier1ImportResult> {
  const payload = await apiJson<ApiTier1ImportResult, undefined>("/api/tier1/import/huggingface", "POST");
  return mapTier1ImportResult(payload);
}

export async function getTier1Documents(): Promise<Tier1Document[]> {
  const payload = await apiRequest<ApiTier1Document[]>("/api/tier1/documents");
  return payload.map(mapTier1Document);
}

export async function getTier1Labels(taskName?: MlTaskName): Promise<Tier1Label[]> {
  const query = taskName ? `?taskName=${encodeURIComponent(taskName)}` : "";
  const payload = await apiRequest<ApiTier1Label[]>(`/api/tier1/labels${query}`);
  return payload.map(mapTier1Label);
}

export async function getTier1AuditLabels(taskName?: MlTaskName): Promise<Tier1Label[]> {
  const query = taskName ? `?taskName=${encodeURIComponent(taskName)}` : "";
  const payload = await apiRequest<ApiTier1Label[]>(`/api/tier1/labels/audit${query}`);
  return payload.map(mapTier1Label);
}

export async function updateTier1Label(
  labelId: string,
  input: { label?: string; reviewed?: boolean; needsReview?: boolean; reviewerNote?: string },
): Promise<Tier1Label> {
  const payload = await apiJson<ApiTier1Label, typeof input>(
    `/api/tier1/labels/${labelId}`,
    "PATCH",
    input,
  );
  return mapTier1Label(payload);
}

export async function buildTier1Datasets(): Promise<Tier1DatasetBuildResult> {
  const payload = await apiJson<ApiTier1DatasetBuildResult, undefined>("/api/tier1/datasets/build", "POST");
  return mapTier1DatasetBuildResult(payload);
}

export async function getTier1Readiness(): Promise<Tier1Readiness[]> {
  const payload = await apiRequest<ApiTier1Readiness[]>("/api/tier1/datasets/readiness");
  return payload.map(mapTier1Readiness);
}

export async function exportTier1TrainingBundle(): Promise<Tier1ExportResult> {
  const payload = await apiJson<ApiTier1ExportResult, undefined>("/api/tier1/export/training-bundle", "POST");
  return mapTier1ExportResult(payload);
}

export async function getTier1Report(): Promise<Tier1Report> {
  const payload = await apiRequest<ApiTier1Report>("/api/tier1/reports");
  return mapTier1Report(payload);
}

export { buildApiUrl, getApiBaseUrl };
