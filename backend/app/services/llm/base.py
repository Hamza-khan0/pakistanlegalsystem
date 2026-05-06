from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.models.enums import IntelligenceArtifactType


@dataclass(slots=True)
class DocumentContext:
    id: str
    name: str
    document_type: str
    summary: str
    excerpt: str
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CaseContext:
    case_id: str
    title: str
    case_number: str
    forum: str
    matter_type: str
    client_name: str
    opposing_party: str
    summary: str
    legal_issues: list[str]
    relief_sought: list[str]
    assigned_counsel: list[str]
    filing_stage: str
    next_hearing_date: str | None
    risk_flags: list[str]
    important_notes: list[str]
    facts_background: list[dict[str, str]]
    linked_statutes: list[str]
    precedents: list[str]
    procedural_alerts: list[str]
    documents: list[DocumentContext]
    timeline: list[dict[str, str]]
    notes: list[dict[str, str]]
    research_entries: list[dict[str, Any]]
    source_excerpt: str


@dataclass(slots=True)
class GroundedSourceContext:
    source_id: str
    chunk_id: str | None
    title: str
    short_title: str
    citation_label: str
    source_type: str
    category: str
    act_name: str
    section_label: str
    excerpt: str
    relevance_score: float
    usage_type: str = "Retrieved"


@dataclass(slots=True)
class GroundingContext:
    query: str
    status: str
    summary: str
    sources: list[GroundedSourceContext] = field(default_factory=list)


@dataclass(slots=True)
class SummaryOutput:
    factual_summary: str
    procedural_summary: str
    key_parties: list[str]
    important_dates: list[str]
    relief_sought: list[str]
    next_steps: list[str]
    citations: list[str]
    confidence_score: float


@dataclass(slots=True)
class IssueOutput:
    legal_issues: list[str]
    maintainability_concerns: list[str]
    missing_information: list[str]
    risk_flags: list[str]
    recommendations: list[str]
    citations: list[str]
    confidence_score: float


@dataclass(slots=True)
class DraftOutput:
    artifact_type: IntelligenceArtifactType
    title: str
    summary: str
    content: str
    citations: list[str]
    next_action: str
    confidence_score: float


@dataclass(slots=True)
class ResearchOutput:
    title: str
    query: str
    summary: str
    content: str
    citations: list[str]
    source_type: str
    next_question: str
    analysis_direction: list[str]
    statutory_hooks: list[str]
    factual_dependencies: list[str]
    next_steps: list[str]
    confidence_score: float


class ChamberGenerationProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate_case_summary(
        self,
        context: CaseContext,
        *,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> SummaryOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_issue_spotting(
        self,
        context: CaseContext,
        *,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> IssueOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_draft_assistance(
        self,
        context: CaseContext,
        *,
        draft_type: str,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> DraftOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_research_note(
        self,
        context: CaseContext,
        *,
        issue: str = "",
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> ResearchOutput:
        raise NotImplementedError
