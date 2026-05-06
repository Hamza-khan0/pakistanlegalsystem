from enum import StrEnum


class CaseStatus(StrEnum):
    ACTIVE = "Active"
    HEARING_DUE = "Hearing Due"
    AWAITING_FILING = "Awaiting Filing"
    RESEARCH = "Research"
    DRAFTING = "Drafting"
    CLOSED = "Closed"


class PriorityLevel(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DocumentType(StrEnum):
    PLAINT = "Plaint"
    WRITTEN_STATEMENT = "Written Statement"
    AFFIDAVIT = "Affidavit"
    REJOINDER = "Rejoinder"
    APPLICATION = "Application"
    ANNEXURE = "Annexure"
    ORDER_SHEET = "Order Sheet"
    JUDGMENT = "Judgment"
    VAKALATNAMA = "Vakalatnama"
    BRIEF = "Brief"


class DocumentStatus(StrEnum):
    FILED = "Filed"
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    PENDING_SIGNATURE = "Pending Signature"
    REFERENCE = "Reference"


class ExtractionStatus(StrEnum):
    PARSED = "Parsed"
    OCR_RUNNING = "OCR Running"
    MANUAL_REVIEW = "Manual Review"
    READY_FOR_INDEXING = "Ready for Indexing"


class OcrStatus(StrEnum):
    NOT_STARTED = "Not Started"
    QUEUED = "Queued"
    COMPLETED = "Completed"


class ParsingStatus(StrEnum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class IntelligenceStatus(StrEnum):
    NOT_PROCESSED = "Not Processed"
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    GENERATED = "Generated"
    STALE = "Stale"
    NEEDS_REVIEW = "Needs Review"
    FAILED = "Failed"


class IntelligenceArtifactType(StrEnum):
    FACTUAL_SUMMARY = "Factual Summary"
    PROCEDURAL_SUMMARY = "Procedural Summary"
    ISSUE_SPOTTING = "Issue Spotting"
    RISK_ASSESSMENT = "Risk Assessment"
    DRAFT_OUTLINE = "Draft Outline"
    PRELIMINARY_OBJECTIONS = "Preliminary Objections"
    PETITION_SKELETON = "Petition Skeleton"
    REPLY_SKELETON = "Reply Skeleton"
    HEARING_NOTE = "Hearing Note"
    CASE_MEMO = "Case Memo"
    STRATEGY_NOTE = "Strategy Note"
    RESEARCH_NOTE = "Research Note"


class TimelineEventType(StrEnum):
    FILING = "Filing"
    HEARING = "Hearing"
    NOTICE = "Notice"
    RESEARCH = "Research"
    DRAFT = "Draft"
    ORDER = "Order"


class NoteType(StrEnum):
    INTERNAL = "Internal Note"
    CLIENT = "Client Note"
    STRATEGY = "Strategy Note"
    HEARING = "Hearing Note"


class ResearchStatus(StrEnum):
    FRESH = "Fresh"
    VERIFIED = "Verified"
    NEEDS_REVIEW = "Needs Review"


class ResearchRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class DraftStatus(StrEnum):
    DRAFTING = "Drafting"
    REVIEWING = "Reviewing"
    READY_FOR_FILING = "Ready for Filing"


class AgentRunStatus(StrEnum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    NEEDS_REVIEW = "Needs Review"
    FAILED = "Failed"


class ChamberTaskType(StrEnum):
    SUMMARY = "summary"
    ISSUE_SPOTTING = "issue_spotting"
    PRELIMINARY_OBJECTIONS = "preliminary_objections"
    HEARING_NOTES = "hearing_notes"
    DRAFT_OUTLINE = "draft_outline"
    DRAFT_REVIEW = "draft_review"
    RESEARCH_MEMO = "research_memo"
    PROCEDURAL_CHECK = "procedural_check"


class ChamberRunStatus(StrEnum):
    QUEUED = "Queued"
    PLANNING = "Planning"
    RUNNING = "Running"
    CRITIC_REVIEW = "Critic Review"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ChamberRunStepStatus(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class LegalSourceType(StrEnum):
    CONSTITUTION = "Constitution"
    STATUTE = "Statute"
    RULES = "Rules"
    CASE_LAW = "Case Law"
    MANUAL = "Manual"


class GroundingUsageType(StrEnum):
    RETRIEVED = "Retrieved"
    CITED = "Cited"
    RELIED_ON = "Relied On"
    SUGGESTED = "Suggested"


class CrawlSourceType(StrEnum):
    HTML = "HTML"
    PDF = "PDF"
    MIXED = "Mixed"


class CrawlMode(StrEnum):
    INDEX = "Index"
    PAGINATED_INDEX = "Paginated Index"
    DETAIL = "Detail Pages"
    DIRECT = "Direct Documents"


class CrawlJobStatus(StrEnum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class CrawlDocumentStatus(StrEnum):
    DISCOVERED = "Discovered"
    FETCHED = "Fetched"
    DOWNLOADED = "Downloaded"
    DUPLICATE = "Duplicate"
    FAILED = "Failed"


class CrawlProcessingStatus(StrEnum):
    PENDING = "Pending"
    TEXT_EXTRACTED = "Text Extracted"
    OCR_REQUIRED = "OCR Required"
    OCR_COMPLETED = "OCR Completed"
    PARTIALLY_EXTRACTED = "Partially Extracted"
    FAILED = "Failed"


class CorpusSourceKind(StrEnum):
    SEEDED_LEGAL_SOURCE = "Seeded Legal Source"
    CRAWLED_DOCUMENT = "Crawled Document"


class DatasetSplit(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class MlTaskName(StrEnum):
    CASE_OUTCOME = "case_outcome"
    MAINTAINABILITY = "maintainability"
    RISK_SCORING = "risk_scoring"
    CASE_TYPE = "case_type"
    LEGAL_ISSUE_CLASSIFIER = "legal_issue_classifier"


class MlDatasetStatus(StrEnum):
    READY = "Ready"
    FAILED = "Failed"


class MlModelFamily(StrEnum):
    BASELINE = "Baseline"
    TRANSFORMER = "Transformer"
    HYBRID_MLP = "Hybrid MLP"


class MlModelStatus(StrEnum):
    TRAINING = "Training"
    READY = "Ready"
    FAILED = "Failed"


class RetrievalMode(StrEnum):
    LEXICAL = "Lexical"
    SEMANTIC = "Semantic"
    HYBRID = "Hybrid"


class EmbeddingIndexStatus(StrEnum):
    BUILDING = "Building"
    READY = "Ready"
    FAILED = "Failed"
