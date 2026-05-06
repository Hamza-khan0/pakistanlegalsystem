from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.enums import ChamberTaskType, IntelligenceArtifactType


@dataclass(slots=True)
class MemorySource:
    source_id: str
    source_type: str
    title: str
    detail: str = ""
    excerpt: str = ""


@dataclass(slots=True)
class LegalGroundingSource:
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
    lexical_score: float | None = None
    semantic_score: float | None = None
    rerank_score: float | None = None
    retrieval_mode: str = "Lexical"
    explanation: str = ""
    usage_type: str = "Retrieved"


@dataclass(slots=True)
class LegalGroundingBundle:
    query: str
    status: str
    summary: str
    retrieval_mode: str = "Lexical"
    diagnostics: dict[str, Any] = field(default_factory=dict)
    sources: list[LegalGroundingSource] = field(default_factory=list)


@dataclass(slots=True)
class CaseMemoryBundle:
    summary: str
    sources: list[MemorySource] = field(default_factory=list)
    source_artifact_ids: list[str] = field(default_factory=list)
    source_document_ids: list[str] = field(default_factory=list)
    source_run_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkflowPlan:
    task_type: ChamberTaskType
    workflow_name: str
    objective: str
    routing_notes: str
    decomposition: list[str]
    agent_sequence: list[str]
    draft_type: str | None = None
    focus_issue: str | None = None
    requires_legal_retrieval: bool = False
    retrieval_focus: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentStepResult:
    agent_name: str
    task_label: str
    input_summary: str
    output_summary: str
    full_output: str
    structured_output: dict[str, Any] = field(default_factory=dict)
    confidence_score: float | None = None
    citations: list[str] = field(default_factory=list)
    source_artifact_ids: list[str] = field(default_factory=list)
    grounding_source_ids: list[str] = field(default_factory=list)
    metadata_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FinalRunOutput:
    final_summary: str
    final_output: str
    confidence_score: float | None
    artifact_type: IntelligenceArtifactType
    artifact_title: str
    structured_output: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""
    citations: list[str] = field(default_factory=list)
    draft_payload: dict[str, Any] | None = None
    research_payload: dict[str, Any] | None = None
    grounding_status: str = "Retrieval not used"
    grounding_query: str = ""
    grounding_sources: list[LegalGroundingSource] = field(default_factory=list)
