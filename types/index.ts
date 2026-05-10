export type PriorityLevel = "Critical" | "High" | "Medium" | "Low";

export type CaseStatus =
  | "Active"
  | "Hearing Due"
  | "Awaiting Filing"
  | "Research"
  | "Drafting"
  | "Closed";

export type DocumentType =
  | "Plaint"
  | "Written Statement"
  | "Affidavit"
  | "Rejoinder"
  | "Application"
  | "Annexure"
  | "Order Sheet"
  | "Judgment"
  | "Vakalatnama"
  | "Brief";

export type DocumentStatus =
  | "Filed"
  | "Draft"
  | "Under Review"
  | "Pending Signature"
  | "Reference";

export type ExtractionStatus =
  | "Parsed"
  | "OCR Running"
  | "Manual Review"
  | "Ready for Indexing";

export type IntelligenceStatus =
  | "Not Processed"
  | "Processing"
  | "Processed"
  | "Generated"
  | "Stale"
  | "Needs Review"
  | "Failed";

export type IntelligenceArtifactType =
  | "Factual Summary"
  | "Procedural Summary"
  | "Issue Spotting"
  | "Risk Assessment"
  | "Draft Outline"
  | "Preliminary Objections"
  | "Petition Skeleton"
  | "Reply Skeleton"
  | "Hearing Note"
  | "Case Memo"
  | "Strategy Note"
  | "Research Note";

export type AgentStatus = "Ready" | "Running" | "Queued" | "Reviewing";
export type ChamberTaskType =
  | "summary"
  | "issue_spotting"
  | "preliminary_objections"
  | "hearing_notes"
  | "draft_outline"
  | "draft_review"
  | "research_memo"
  | "procedural_check";

export type ChamberRunStatus =
  | "Queued"
  | "Planning"
  | "Running"
  | "Critic Review"
  | "Completed"
  | "Failed";

export type ChamberRunStepStatus =
  | "Pending"
  | "Running"
  | "Completed"
  | "Failed";

export type GroundingUsageType =
  | "Retrieved"
  | "Cited"
  | "Relied On"
  | "Suggested";

export type CrawlSourceType = "HTML" | "PDF" | "Mixed";
export type CrawlMode = "Index" | "Paginated Index" | "Detail Pages" | "Direct Documents";
export type CrawlJobStatus = "Queued" | "Running" | "Completed" | "Failed";
export type CrawlProcessingStatus =
  | "Pending"
  | "Text Extracted"
  | "OCR Required"
  | "OCR Completed"
  | "Partially Extracted"
  | "Failed";
export type CrawlDocumentStatus =
  | "Discovered"
  | "Fetched"
  | "Downloaded"
  | "Duplicate"
  | "Failed";
export type CorpusSourceKind = "Seeded Legal Source" | "Crawled Document";
export type DatasetSplit = "train" | "validation" | "test";
export type MlTaskName =
  | "case_outcome"
  | "maintainability"
  | "risk_scoring"
  | "case_type"
  | "legal_issue_classifier";
export type MlDatasetStatus = "Ready" | "Failed";
export type MlModelFamily = "Baseline" | "Transformer" | "Hybrid MLP";
export type MlModelStatus = "Training" | "Ready" | "Failed";
export type RetrievalMode = "Lexical" | "Semantic" | "Hybrid";
export type EmbeddingIndexStatus = "Building" | "Ready" | "Failed";
export type DatasetReadinessStatus =
  | "not_ready"
  | "weak"
  | "usable_for_demo"
  | "usable_for_training"
  | "strong";

export interface CaseFact {
  label: string;
  text: string;
}

export interface DraftArtifact {
  id: string;
  title: string;
  type: string;
  status: "Drafting" | "Reviewing" | "Ready for Filing";
  updatedAt: string;
  createdAt?: string;
  owner: string;
  summary: string;
  content?: string;
  version?: number;
}

export interface CaseMatter {
  id: string;
  title: string;
  caseNumber: string;
  forum: string;
  matterType: string;
  status: CaseStatus;
  priority: PriorityLevel;
  stage: string;
  client: string;
  opposingParty: string;
  nextHearingDate: string;
  assignedCounsel: string[];
  teamAgents: string[];
  summary: string;
  issues: string[];
  reliefSought: string[];
  importantNotes: string[];
  factsBackground: CaseFact[];
  linkedStatutes: string[];
  precedents: string[];
  linkedDocumentIds: string[];
  timelineIds: string[];
  researchNoteIds: string[];
  draftArtifacts: DraftArtifact[];
  riskFlags: string[];
  proceduralAlerts: string[];
  tags: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface CaseDocument {
  id: string;
  caseId: string;
  name: string;
  type: DocumentType;
  category: string;
  uploadDate: string;
  status: DocumentStatus;
  extractionStatus: ExtractionStatus;
  intelligenceStatus: IntelligenceStatus;
  tags: string[];
  pages: number;
  filedBy: string;
  summary: string;
  previewText: string;
  extractedText: string;
  extractionError: string;
  processedAt?: string | null;
  fileName?: string;
  filePath?: string;
  fileUrl?: string;
  mimeType?: string;
  ocrStatus?: string;
  ocrEngine?: string;
  ocrOutcome?: string;
  ocrConfidence?: number | null;
  detectedLanguage?: string;
  pageExtractions?: Array<{
    pageNumber: number;
    method: string;
    confidence?: number | null;
    textPreview: string;
  }>;
  parsingStatus?: string;
  metadataJson?: Record<string, unknown>;
  caseTitle?: string;
  caseNumber?: string;
  caseForum?: string;
  casePriority?: PriorityLevel;
}

export interface IntelligenceArtifact {
  id: string;
  caseId: string;
  documentId?: string | null;
  artifactType: IntelligenceArtifactType;
  title: string;
  content: string;
  structuredJson: Record<string, unknown>;
  source: string;
  status: IntelligenceStatus;
  groundingStatus: string;
  legalSources: GroundingSource[];
  createdAt: string;
  updatedAt: string;
}

export interface TimelineEntry {
  id: string;
  caseId: string;
  date: string;
  title: string;
  description: string;
  actor: string;
  type: "Filing" | "Hearing" | "Notice" | "Research" | "Draft" | "Order";
}

export interface ResearchNote {
  id: string;
  caseId: string;
  title: string;
  status: "Fresh" | "Verified" | "Needs Review";
  author: string;
  updatedAt: string;
  query?: string;
  sourceType?: string;
  authorities: string[];
  summary: string;
  nextQuestion: string;
}

export type ResearchWorkflowStatus =
  | "pending"
  | "running"
  | "completed"
  | "completed_with_warnings"
  | "failed";

export interface ResearchWorkflowRequest {
  caseId: string;
  draftType?: string | null;
  focusIssues?: string[] | null;
  includeDocuments?: boolean;
  includePriorNotes?: boolean;
  includeTimeline?: boolean;
  maxSources?: number;
  maxLiveSources?: number;
  generatePdf?: boolean;
  pdfMode?: PdfMode;
  useLiveWeb?: boolean;
  useLlm?: boolean;
  generateFullDraft?: boolean;
}

export type PdfMode = "draft_only" | "draft_with_research" | "full_trace";

export interface ResearchIssue {
  label: string;
  probability?: number | null;
  source: string;
  explanation?: string | null;
}

export interface ResearchQuery {
  query: string;
  issue?: string | null;
  priority: number;
  source: string;
  rationale?: string | null;
}

export interface RetrievedLegalSource {
  id?: string | null;
  title: string;
  sourceType: string;
  court?: string | null;
  citation?: string | null;
  statute?: string | null;
  section?: string | null;
  excerpt: string;
  relevanceScore?: number | null;
  retrievalMethod?: string | null;
  url?: string | null;
  localPath?: string | null;
  confidence?: number | null;
  sourceOrigin?: string | null;
  domain?: string | null;
  sourceProvider?: string | null;
}

export interface StructuredResearchMemo {
  factualBasis: string[];
  legalIssues: string[];
  applicableStatutes: Record<string, unknown>[];
  relevantCaseLaw: Record<string, unknown>[];
  proceduralPosition: string[];
  argumentsForClient: string[];
  argumentsAgainstClient: string[];
  researchGaps: string[];
  recommendedDraftType: string;
  draftingInstructions: string[];
  sourceList: Record<string, unknown>[];
  legalAuthorityWarning: string;
}

export interface CriticReport {
  passed: boolean;
  severity?: "low" | "medium" | "high" | string;
  unsupportedClaims: string[];
  fakeOrUnverifiedCitations?: string[];
  weakSources: string[];
  missingAuthorities: string[];
  draftingDefects?: string[];
  overclaimingWarnings: string[];
  draftingRisks: string[];
  requiredLawyerChecks?: string[];
  recommendation: string;
}

export interface GeneratedDraft {
  draftType: string;
  title: string;
  draftMarkdown: string;
  editedDraftMarkdown?: string | null;
  finalDraftMarkdown: string;
  sections: Array<{ heading?: string; content?: string }>;
  authoritiesUsed: string[];
  factsUsed: string[];
  assumptions: string[];
  missingInformation: string[];
  lawyerReviewChecklist: string[];
  legalAuthorityWarning: string;
  lastEditedAt?: string | null;
  pdfStale?: boolean;
  pdfGeneratedAt?: string | null;
  previousDraftMarkdown?: string | null;
}

export interface ResearchDraftResponse {
  runId: string;
  caseId: string;
  saved: boolean;
  draftMarkdown: string;
  editedDraftMarkdown?: string | null;
  finalDraftMarkdown: string;
  lastEditedAt?: string | null;
  generatedDraft: GeneratedDraft;
  legalAuthorityWarning: string;
}

export interface PdfRegenerateResponse {
  runId: string;
  pdfGenerated: boolean;
  pdfPath: string;
  pdfUrl: string;
  fileSizeBytes: number;
  pdfMode: PdfMode;
}

export interface DraftingInstructions {
  recommendedDraftType?: string;
  selectedDraftType?: string;
  clientPosition?: string;
  coreIssuesToPlead?: string[];
  factsToHighlight?: string[];
  legalBasesToUse?: Record<string, unknown>[];
  authoritiesToCite?: string[];
  risksToAddress?: string[];
  missingInformationNeeded?: string[];
  draftingCautions?: string[];
}

export interface ResearchWorkflowResponse {
  runId: string;
  caseId: string;
  status: ResearchWorkflowStatus;
  detectedIssues: ResearchIssue[];
  queryPlan: ResearchQuery[];
  retrievedSources: RetrievedLegalSource[];
  researchMemo: StructuredResearchMemo;
  generatedDraft?: GeneratedDraft | null;
  criticReport: CriticReport;
  draftingInstructions: DraftingInstructions;
  liveWebUsed: boolean;
  llmUsedForResearch: boolean;
  llmUsedForDrafting: boolean;
  sourcesByOrigin: Record<string, RetrievedLegalSource[] | number>;
  lawyerReviewChecklist: string[];
  providerStatus: Record<string, unknown>;
  pdfPath?: string | null;
  markdownPath?: string | null;
  legalAuthorityWarning: string;
  privacyNotice?: string;
  warnings?: string[];
  createdAt: string;
  completedAt?: string | null;
}

export interface ResearchRunSummary {
  runId: string;
  caseId: string;
  status: ResearchWorkflowStatus;
  workflowType: string;
  detectedIssueCount: number;
  sourceCount: number;
  criticPassed: boolean;
  recommendedDraftType: string;
  pdfPath?: string | null;
  markdownPath?: string | null;
  createdAt: string;
  completedAt?: string | null;
}

export interface ResearchHealth {
  workflowAvailable: boolean;
  legalIssueClassifier: Record<string, unknown>;
  localRetrievalAvailable: boolean;
  retrievalAdapterAvailable: boolean;
  liveWebSearchEnabled: boolean;
  liveWebSearchAvailable: boolean;
  searchProvider: string;
  llmEnabled: boolean;
  llmAvailable: boolean;
  llmModel: string;
  llmConfigured: boolean;
  pdfAvailable: boolean;
  artifactDirectoryWritable: boolean;
  privacyNotice: string;
  legalAuthorityWarning: string;
}

export interface BackendHealth {
  ok: boolean;
  status: string;
  service: string;
  version: string;
  environment: string;
  host: string;
  port: number;
  apiPrefix: string;
  corsOrigins: string[];
}

export interface NoteEntry {
  id: string;
  caseId: string;
  title: string;
  content: string;
  noteType: string;
  author: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentDefinition {
  id: string;
  name: string;
  role: string;
  description: string;
  status: AgentStatus;
  lastRun: string;
  specialties: string[];
  queueDepth: number;
  confidence: string;
}

export interface AgentOutput {
  id: string;
  caseId: string;
  agentId: string;
  title: string;
  generatedAt: string;
  confidence: string;
  rawStatus?: string;
  taskType?: string;
  inputSummary?: string;
  confidenceScore?: number | null;
  status: "Published" | "Needs Review";
  summary: string;
  citations: string[];
  nextAction: string;
}

export interface MemorySource {
  sourceId: string;
  sourceType: string;
  title: string;
  detail: string;
  excerpt: string;
}

export interface GroundingSource {
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
  usageType: GroundingUsageType;
}

export interface CrawlSource {
  id: string;
  name: string;
  sourceType: CrawlSourceType;
  baseUrl: string;
  allowedDomains: string[];
  crawlMode: CrawlMode;
  languageHint: string;
  category: string;
  isActive: boolean;
  configJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface CrawlJob {
  id: string;
  sourceId: string;
  sourceName: string;
  status: CrawlJobStatus;
  startedAt: string;
  completedAt: string | null;
  pagesFetched: number;
  documentsDiscovered: number;
  documentsSaved: number;
  errorsCount: number;
  metadataJson: Record<string, unknown>;
}

export interface CrawledDocument {
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
  crawlStatus: CrawlDocumentStatus;
  processingStatus: CrawlProcessingStatus;
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

export interface CorpusEntry {
  id: string;
  sourceKind: CorpusSourceKind;
  crawledDocumentId: string | null;
  legalSourceId: string | null;
  title: string;
  language: string;
  normalizedText: string;
  chunkCount: number;
  readyForRetrieval: boolean;
  readyForTraining: boolean;
  datasetSplit: DatasetSplit;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface MlDataset {
  id: string;
  taskName: MlTaskName;
  name: string;
  version: string;
  status: MlDatasetStatus;
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

export interface DatasetReadiness {
  datasetId: string;
  taskName: string;
  datasetName: string;
  datasetVersion: string;
  status: DatasetReadinessStatus;
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

export interface MlModel {
  id: string;
  datasetId: string;
  taskName: MlTaskName;
  modelFamily: MlModelFamily;
  name: string;
  status: MlModelStatus;
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

export interface MlModelDiagnostics {
  modelId: string;
  taskName: MlTaskName;
  modelFamily: MlModelFamily;
  modelName: string;
  diagnostics: Record<string, unknown>;
}

export interface CalibrationRecord {
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

export interface MlLeaderboardEntry {
  modelId: string;
  name: string;
  modelFamily: MlModelFamily;
  primaryMetric: number;
  metricsJson: Record<string, unknown>;
  createdAt: string;
}

export interface MlTaskLeaderboard {
  taskName: MlTaskName;
  entries: MlLeaderboardEntry[];
}

export interface CasePrediction {
  id: string;
  caseId: string;
  modelId: string;
  taskName: MlTaskName;
  predictedLabel: string;
  confidence: number;
  probabilitiesJson: Record<string, number>;
  inputSummary: string;
  warningText: string;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  modelName: string;
  modelFamily: MlModelFamily;
  datasetId: string;
}

export interface PredictionExplanation {
  predictionId: string;
  taskName: MlTaskName;
  predictedLabel: string;
  confidence: number;
  modelFamily: string;
  modelName: string;
  explanationNote: string;
  topProbabilities: Array<{ label: string; score: number }>;
  structuredSignals: Record<string, unknown>;
  diagnostics: Record<string, unknown>;
}

export interface EmbeddingIndexMetadata {
  id: string;
  name: string;
  retrievalMode: RetrievalMode;
  modelName: string;
  status: EmbeddingIndexStatus;
  corpusVersion: string;
  indexPath: string;
  vectorDimension: number;
  sourceCount: number;
  metadataJson: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface RetrievalSearchResult {
  query: string;
  mode: RetrievalMode;
  status: string;
  summary: string;
  diagnostics: Record<string, unknown>;
  sources: GroundingSource[];
}

export interface RetrievalLeaderboardEntry {
  mode: string;
  query: string;
  topLabels: string[];
  sourceTypeMix: Record<string, number>;
  averageScore: number;
  diagnostics: Record<string, unknown>;
}

export interface RetrievalLeaderboard {
  generatedAt: string;
  entries: RetrievalLeaderboardEntry[];
}

export interface RetrievalBenchmarkResult {
  query: string;
  taskType: string;
  mode: string;
  topK: number;
  expectedLabels: string[];
  metricsJson: Record<string, unknown>;
  resultsJson: Array<Record<string, unknown>>;
  diagnostics: Record<string, unknown>;
}

export interface RetrievalBenchmarkRun {
  id: string;
  name: string;
  retrievalModesCompared: string[];
  queryCount: number;
  metricsJson: Record<string, unknown>;
  createdAt: string;
  results: RetrievalBenchmarkResult[];
}

export interface RunGroundingDiagnostics {
  runId: string;
  retrievalMode: string;
  groundingStatus: string;
  diagnostics: Record<string, unknown>;
  sources: GroundingSource[];
}

export interface ChamberRunQuality {
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

export interface CaseQualitySummary {
  caseId: string;
  recentRunCount: number;
  averageRunConfidence: number | null;
  latestRunQuality: ChamberRunQuality | null;
  groundedRunCount: number;
  criticalWarningCount: number;
  qualityWarnings: string[];
}

export interface EvaluationReport {
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

export interface Tier1ImportResult {
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

export interface Tier1Document {
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

export interface Tier1Label {
  id: string;
  documentId: string;
  documentTitle: string;
  taskName: MlTaskName;
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

export interface Tier1Readiness {
  taskName: MlTaskName;
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

export interface Tier1DatasetBuildResult {
  status: string;
  message: string;
  datasets: Array<Record<string, unknown>>;
  warnings: string[];
}

export interface Tier1ExportResult {
  status: string;
  message: string;
  exportDir: string;
  zipPath: string;
  datasetCounts: Record<string, Record<string, number>>;
  warnings: string[];
}

export interface Tier1Report {
  generatedAt: string;
  documentCount: number;
  labelCount: number;
  sourceTypeCounts: Record<string, number>;
  languageCounts: Record<string, number>;
  reviewCounts: Record<string, number>;
  readiness: Tier1Readiness[];
}

export interface CorpusBuildResult {
  legalSourcesUpserted: number;
  corpusEntriesUpserted: number;
  crawledDocumentsPromoted: number;
}

export interface CorpusExportResult {
  outputDir: string;
  retrievalRecords: number;
  classificationRecords: number;
  bilingualRecords: number;
  files: string[];
}

export interface ChamberRunStep {
  id: string;
  runId: string;
  stepOrder: number;
  agentName: string;
  taskLabel: string;
  inputSummary: string;
  outputSummary: string;
  fullOutput: string;
  structuredJson: Record<string, unknown>;
  status: ChamberRunStepStatus;
  confidenceScore: number | null;
  sourceArtifactIds: string[];
  metadataJson: Record<string, unknown>;
  createdAt: string;
  completedAt: string | null;
}

export interface ChamberRunSummary {
  id: string;
  caseId: string;
  taskType: ChamberTaskType;
  userInstruction: string;
  selectedWorkflow: string;
  status: ChamberRunStatus;
  finalSummary: string;
  confidenceScore: number | null;
  agentNames: string[];
  memorySources: MemorySource[];
  criticSummary: string;
  finalArtifactId: string | null;
  linkedDraftId: string | null;
  linkedResearchEntryId: string | null;
  groundingStatus: string;
  retrievalMode: string;
  retrievalDiagnostics: Record<string, unknown>;
  legalRetrievalQuery: string;
  legalSourceCount: number;
  legalSources: GroundingSource[];
  startedAt: string;
  completedAt: string | null;
}

export interface ChamberRun extends ChamberRunSummary {
  finalOutput: string;
  steps: ChamberRunStep[];
  metadataJson: Record<string, unknown>;
}

export interface AgentActivity {
  stepId: string;
  runId: string;
  caseId: string;
  caseTitle: string;
  agentName: string;
  taskLabel: string;
  status: ChamberRunStepStatus;
  outputSummary: string;
  confidenceScore: number | null;
  completedAt: string | null;
}

export interface Deadline {
  id: string;
  caseId: string;
  title: string;
  dueDate: string;
  owner: string;
  severity: PriorityLevel;
  note: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  tone: "info" | "warning" | "success";
}

export interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  category: "Agent" | "Court" | "Document" | "Team";
}

export interface WorkflowStep {
  id: string;
  title: string;
  detail: string;
}

export interface WorkspaceAgentResponse {
  agent: string;
  role: string;
  tone: "analysis" | "draft" | "critical" | "procedure";
  title: string;
  summary: string;
  bullets: string[];
  citations: string[];
}

export interface WorkspaceRun {
  id: string;
  prompt: string;
  createdAt: string;
  decomposition: string[];
  citedMaterials: string[];
  flaggedIssues: string[];
  outputs: WorkspaceAgentResponse[];
  finalSummary: string;
}

export interface DashboardSummaryData {
  activeCaseCount: number;
  urgentDeadlinesCount: number;
  pendingFilingsCount: number;
  uploadedDocumentsCount: number;
  recentActivity: ActivityItem[];
  upcomingHearings: Deadline[];
  urgentDeadlines: Deadline[];
  notifications: NotificationItem[];
  recentCases: CaseMatter[];
}

export interface CaseDetailData {
  caseItem: CaseMatter;
  documents: CaseDocument[];
  timeline: TimelineEntry[];
  notes: NoteEntry[];
  research: ResearchNote[];
  drafts: DraftArtifact[];
  agentOutputs: AgentOutput[];
  intelligence: IntelligenceArtifact[];
  runs: ChamberRunSummary[];
  legalBasis: GroundingSource[];
  predictions: CasePrediction[];
}
