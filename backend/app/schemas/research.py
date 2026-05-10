from datetime import datetime

from typing import Any

from pydantic import Field

from app.models.enums import ResearchRunStatus, ResearchStatus
from app.schemas.base import APIModel


class ResearchEntryBase(APIModel):
    title: str
    query: str = ""
    summary: str = ""
    citations: list[str] = Field(default_factory=list)
    source_type: str = Field(default="Internal Research", serialization_alias="sourceType")
    status: ResearchStatus = ResearchStatus.FRESH
    author: str = ""
    next_question: str = Field(default="", serialization_alias="nextQuestion")


class ResearchEntryCreate(ResearchEntryBase):
    pass


class ResearchEntryRead(ResearchEntryBase):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


LEGAL_RESEARCH_WARNING = (
    "This document is AI-assisted and must be reviewed, corrected, and approved by a qualified lawyer before use. "
    "It is not legal advice and is not legally authoritative."
)

PDF_MODE_DRAFT_ONLY = "draft_only"
PDF_MODE_DRAFT_WITH_RESEARCH = "draft_with_research"
PDF_MODE_FULL_TRACE = "full_trace"
PDF_MODES = {PDF_MODE_DRAFT_ONLY, PDF_MODE_DRAFT_WITH_RESEARCH, PDF_MODE_FULL_TRACE}


class ResearchWorkflowRequest(APIModel):
    case_id: str = Field(serialization_alias="caseId")
    draft_type: str | None = Field(default="auto", serialization_alias="draftType")
    focus_issues: list[str] | None = Field(default=None, serialization_alias="focusIssues")
    include_documents: bool = Field(default=True, serialization_alias="includeDocuments")
    include_prior_notes: bool = Field(default=True, serialization_alias="includePriorNotes")
    include_timeline: bool = Field(default=True, serialization_alias="includeTimeline")
    max_sources: int = Field(default=12, ge=1, le=40, serialization_alias="maxSources")
    max_live_sources: int = Field(default=8, ge=0, le=20, serialization_alias="maxLiveSources")
    generate_pdf: bool = Field(default=True, serialization_alias="generatePdf")
    pdf_mode: str = Field(default=PDF_MODE_DRAFT_WITH_RESEARCH, serialization_alias="pdfMode")
    use_live_web: bool = Field(default=True, serialization_alias="useLiveWeb")
    use_llm: bool = Field(default=True, serialization_alias="useLlm")
    generate_full_draft: bool = Field(default=True, serialization_alias="generateFullDraft")


class CaseResearchDraftRequest(APIModel):
    draft_type: str | None = Field(default="auto", serialization_alias="draftType")
    focus_issues: list[str] | None = Field(default=None, serialization_alias="focusIssues")
    include_documents: bool = Field(default=True, serialization_alias="includeDocuments")
    include_prior_notes: bool = Field(default=True, serialization_alias="includePriorNotes")
    include_timeline: bool = Field(default=True, serialization_alias="includeTimeline")
    max_sources: int = Field(default=12, ge=1, le=40, serialization_alias="maxSources")
    max_live_sources: int = Field(default=8, ge=0, le=20, serialization_alias="maxLiveSources")
    generate_pdf: bool = Field(default=True, serialization_alias="generatePdf")
    pdf_mode: str = Field(default=PDF_MODE_DRAFT_WITH_RESEARCH, serialization_alias="pdfMode")
    use_live_web: bool = Field(default=True, serialization_alias="useLiveWeb")
    use_llm: bool = Field(default=True, serialization_alias="useLlm")
    generate_full_draft: bool = Field(default=True, serialization_alias="generateFullDraft")


class ResearchIssue(APIModel):
    label: str
    probability: float | None = None
    source: str
    explanation: str | None = None


class ResearchQuery(APIModel):
    query: str
    issue: str | None = None
    priority: int
    source: str
    rationale: str | None = None


class RetrievedLegalSource(APIModel):
    id: str | None = None
    title: str
    source_type: str = Field(serialization_alias="sourceType")
    court: str | None = None
    citation: str | None = None
    statute: str | None = None
    section: str | None = None
    excerpt: str
    relevance_score: float | None = Field(default=None, serialization_alias="relevanceScore")
    retrieval_method: str | None = Field(default=None, serialization_alias="retrievalMethod")
    url: str | None = None
    local_path: str | None = Field(default=None, serialization_alias="localPath")
    confidence: float | None = None
    source_origin: str | None = Field(default=None, serialization_alias="sourceOrigin")
    domain: str | None = None
    source_provider: str | None = Field(default=None, serialization_alias="sourceProvider")


class StructuredResearchMemo(APIModel):
    factual_basis: list[str] = Field(default_factory=list, serialization_alias="factualBasis")
    legal_issues: list[str] = Field(default_factory=list, serialization_alias="legalIssues")
    applicable_statutes: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="applicableStatutes")
    relevant_case_law: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="relevantCaseLaw")
    procedural_position: list[str] = Field(default_factory=list, serialization_alias="proceduralPosition")
    arguments_for_client: list[str] = Field(default_factory=list, serialization_alias="argumentsForClient")
    arguments_against_client: list[str] = Field(default_factory=list, serialization_alias="argumentsAgainstClient")
    research_gaps: list[str] = Field(default_factory=list, serialization_alias="researchGaps")
    recommended_draft_type: str = Field(default="research_memo", serialization_alias="recommendedDraftType")
    drafting_instructions: list[str] = Field(default_factory=list, serialization_alias="draftingInstructions")
    source_list: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="sourceList")
    legal_authority_warning: str = Field(default=LEGAL_RESEARCH_WARNING, serialization_alias="legalAuthorityWarning")


class CriticReport(APIModel):
    passed: bool
    severity: str = "medium"
    unsupported_claims: list[str] = Field(default_factory=list, serialization_alias="unsupportedClaims")
    fake_or_unverified_citations: list[str] = Field(default_factory=list, serialization_alias="fakeOrUnverifiedCitations")
    weak_sources: list[str] = Field(default_factory=list, serialization_alias="weakSources")
    missing_authorities: list[str] = Field(default_factory=list, serialization_alias="missingAuthorities")
    drafting_defects: list[str] = Field(default_factory=list, serialization_alias="draftingDefects")
    overclaiming_warnings: list[str] = Field(default_factory=list, serialization_alias="overclaimingWarnings")
    drafting_risks: list[str] = Field(default_factory=list, serialization_alias="draftingRisks")
    required_lawyer_checks: list[str] = Field(default_factory=list, serialization_alias="requiredLawyerChecks")
    recommendation: str


class GeneratedDraft(APIModel):
    draft_type: str = Field(default="research_memo", serialization_alias="draftType")
    title: str
    draft_markdown: str = Field(serialization_alias="draftMarkdown")
    edited_draft_markdown: str | None = Field(default=None, serialization_alias="editedDraftMarkdown")
    final_draft_markdown: str = Field(default="", serialization_alias="finalDraftMarkdown")
    sections: list[dict[str, Any]] = Field(default_factory=list)
    authorities_used: list[str] = Field(default_factory=list, serialization_alias="authoritiesUsed")
    facts_used: list[str] = Field(default_factory=list, serialization_alias="factsUsed")
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list, serialization_alias="missingInformation")
    lawyer_review_checklist: list[str] = Field(default_factory=list, serialization_alias="lawyerReviewChecklist")
    legal_authority_warning: str = Field(default=LEGAL_RESEARCH_WARNING, serialization_alias="legalAuthorityWarning")
    last_edited_at: datetime | None = Field(default=None, serialization_alias="lastEditedAt")
    pdf_stale: bool = Field(default=False, serialization_alias="pdfStale")
    pdf_generated_at: datetime | None = Field(default=None, serialization_alias="pdfGeneratedAt")
    previous_draft_markdown: str | None = Field(default=None, serialization_alias="previousDraftMarkdown")


class ResearchDraftUpdateRequest(APIModel):
    edited_draft_markdown: str = Field(min_length=1, serialization_alias="editedDraftMarkdown")
    edit_note: str | None = Field(default=None, serialization_alias="editNote")


class ResearchDraftResponse(APIModel):
    run_id: str = Field(serialization_alias="runId")
    case_id: str = Field(serialization_alias="caseId")
    saved: bool = True
    draft_markdown: str = Field(serialization_alias="draftMarkdown")
    edited_draft_markdown: str | None = Field(default=None, serialization_alias="editedDraftMarkdown")
    final_draft_markdown: str = Field(serialization_alias="finalDraftMarkdown")
    last_edited_at: datetime | None = Field(default=None, serialization_alias="lastEditedAt")
    generated_draft: GeneratedDraft = Field(serialization_alias="generatedDraft")
    legal_authority_warning: str = Field(default=LEGAL_RESEARCH_WARNING, serialization_alias="legalAuthorityWarning")


class PdfRegenerateRequest(APIModel):
    use_edited_draft: bool = Field(default=True, serialization_alias="useEditedDraft")
    pdf_mode: str = Field(default=PDF_MODE_DRAFT_WITH_RESEARCH, serialization_alias="pdfMode")


class ResearchDraftRegenerateRequest(APIModel):
    draft_type: str = Field(default="writ_petition", serialization_alias="draftType")
    use_llm: bool = Field(default=True, serialization_alias="useLlm")


class PdfRegenerateResponse(APIModel):
    run_id: str = Field(serialization_alias="runId")
    pdf_generated: bool = Field(serialization_alias="pdfGenerated")
    pdf_path: str = Field(serialization_alias="pdfPath")
    pdf_url: str = Field(serialization_alias="pdfUrl")
    file_size_bytes: int = Field(serialization_alias="fileSizeBytes")
    pdf_mode: str = Field(default=PDF_MODE_DRAFT_WITH_RESEARCH, serialization_alias="pdfMode")


class ResearchWorkflowResponse(APIModel):
    run_id: str = Field(serialization_alias="runId")
    case_id: str = Field(serialization_alias="caseId")
    status: ResearchRunStatus | str
    detected_issues: list[ResearchIssue] = Field(default_factory=list, serialization_alias="detectedIssues")
    query_plan: list[ResearchQuery] = Field(default_factory=list, serialization_alias="queryPlan")
    retrieved_sources: list[RetrievedLegalSource] = Field(default_factory=list, serialization_alias="retrievedSources")
    research_memo: StructuredResearchMemo = Field(serialization_alias="researchMemo")
    generated_draft: GeneratedDraft | None = Field(default=None, serialization_alias="generatedDraft")
    critic_report: CriticReport = Field(serialization_alias="criticReport")
    drafting_instructions: dict[str, Any] = Field(default_factory=dict, serialization_alias="draftingInstructions")
    live_web_used: bool = Field(default=False, serialization_alias="liveWebUsed")
    llm_used_for_research: bool = Field(default=False, serialization_alias="llmUsedForResearch")
    llm_used_for_drafting: bool = Field(default=False, serialization_alias="llmUsedForDrafting")
    sources_by_origin: dict[str, Any] = Field(default_factory=dict, serialization_alias="sourcesByOrigin")
    lawyer_review_checklist: list[str] = Field(default_factory=list, serialization_alias="lawyerReviewChecklist")
    provider_status: dict[str, Any] = Field(default_factory=dict, serialization_alias="providerStatus")
    pdf_path: str | None = Field(default=None, serialization_alias="pdfPath")
    markdown_path: str | None = Field(default=None, serialization_alias="markdownPath")
    legal_authority_warning: str = Field(default=LEGAL_RESEARCH_WARNING, serialization_alias="legalAuthorityWarning")
    privacy_notice: str = Field(default="", serialization_alias="privacyNotice")
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class ResearchRunSummary(APIModel):
    run_id: str = Field(serialization_alias="runId")
    case_id: str = Field(serialization_alias="caseId")
    status: ResearchRunStatus | str
    workflow_type: str = Field(serialization_alias="workflowType")
    detected_issue_count: int = Field(serialization_alias="detectedIssueCount")
    source_count: int = Field(serialization_alias="sourceCount")
    critic_passed: bool = Field(serialization_alias="criticPassed")
    recommended_draft_type: str = Field(serialization_alias="recommendedDraftType")
    pdf_path: str | None = Field(default=None, serialization_alias="pdfPath")
    markdown_path: str | None = Field(default=None, serialization_alias="markdownPath")
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class ResearchHealthRead(APIModel):
    workflow_available: bool = Field(serialization_alias="workflowAvailable")
    legal_issue_classifier: dict[str, Any] = Field(serialization_alias="legalIssueClassifier")
    local_retrieval_available: bool = Field(default=True, serialization_alias="localRetrievalAvailable")
    retrieval_adapter_available: bool = Field(serialization_alias="retrievalAdapterAvailable")
    live_web_search_enabled: bool = Field(default=False, serialization_alias="liveWebSearchEnabled")
    live_web_search_available: bool = Field(default=False, serialization_alias="liveWebSearchAvailable")
    search_provider: str = Field(default="none", serialization_alias="searchProvider")
    llm_enabled: bool = Field(default=False, serialization_alias="llmEnabled")
    llm_available: bool = Field(default=False, serialization_alias="llmAvailable")
    llm_model: str = Field(default="", serialization_alias="llmModel")
    llm_configured: bool = Field(serialization_alias="llmConfigured")
    pdf_available: bool = Field(serialization_alias="pdfAvailable")
    artifact_directory_writable: bool = Field(serialization_alias="artifactDirectoryWritable")
    privacy_notice: str = Field(default="", serialization_alias="privacyNotice")
    legal_authority_warning: str = Field(default=LEGAL_RESEARCH_WARNING, serialization_alias="legalAuthorityWarning")


class WebSearchTestRequest(APIModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=10, serialization_alias="maxResults")
