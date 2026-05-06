from datetime import datetime

from pydantic import Field

from app.models.enums import IntelligenceArtifactType, IntelligenceStatus
from app.schemas.agent_log import AgentRunLogRead
from app.schemas.base import APIModel
from app.schemas.draft import DraftRead
from app.schemas.legal_sources import GroundingSourceRead
from app.schemas.research import ResearchEntryRead


class IntelligenceGenerationBase(APIModel):
    document_ids: list[str] = Field(default_factory=list, serialization_alias="documentIds")
    instructions: str = ""


class GenerateSummaryRequest(IntelligenceGenerationBase):
    pass


class GenerateIssuesRequest(IntelligenceGenerationBase):
    pass


class GenerateDraftRequest(IntelligenceGenerationBase):
    draft_type: str = Field(serialization_alias="draftType")


class GenerateResearchRequest(IntelligenceGenerationBase):
    issue: str = ""


class IntelligenceArtifactRead(APIModel):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    document_id: str | None = Field(default=None, serialization_alias="documentId")
    artifact_type: IntelligenceArtifactType = Field(serialization_alias="artifactType")
    title: str
    content: str
    structured_json: dict = Field(default_factory=dict, serialization_alias="structuredJson")
    source: str
    status: IntelligenceStatus
    grounding_status: str = Field(default="Retrieval not used", serialization_alias="groundingStatus")
    legal_sources: list[GroundingSourceRead] = Field(
        default_factory=list,
        serialization_alias="legalSources",
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class CaseGenerationRead(APIModel):
    artifacts: list[IntelligenceArtifactRead]
    agent_output: AgentRunLogRead = Field(serialization_alias="agentOutput")


class DraftGenerationRead(APIModel):
    draft: DraftRead
    artifact: IntelligenceArtifactRead
    agent_output: AgentRunLogRead = Field(serialization_alias="agentOutput")


class ResearchGenerationRead(APIModel):
    research_entry: ResearchEntryRead = Field(serialization_alias="researchEntry")
    artifact: IntelligenceArtifactRead
    agent_output: AgentRunLogRead = Field(serialization_alias="agentOutput")
