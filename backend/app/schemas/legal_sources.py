from datetime import datetime

from pydantic import Field

from app.models.enums import ChamberTaskType, GroundingUsageType, LegalSourceType
from app.schemas.base import APIModel


class LegalSourceChunkRead(APIModel):
    id: str
    source_id: str = Field(serialization_alias="sourceId")
    chunk_index: int = Field(serialization_alias="chunkIndex")
    heading: str
    text: str
    token_count: int = Field(serialization_alias="tokenCount")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")


class GroundingSourceRead(APIModel):
    source_id: str = Field(serialization_alias="sourceId")
    chunk_id: str | None = Field(default=None, serialization_alias="chunkId")
    title: str
    short_title: str = Field(default="", serialization_alias="shortTitle")
    citation_label: str = Field(default="", serialization_alias="citationLabel")
    source_type: str = Field(serialization_alias="sourceType")
    category: str = ""
    act_name: str = Field(default="", serialization_alias="actName")
    section_label: str = Field(default="", serialization_alias="sectionLabel")
    language: str = ""
    source_origin: str = Field(default="", serialization_alias="sourceOrigin")
    source_url: str = Field(default="", serialization_alias="sourceUrl")
    excerpt: str = ""
    relevance_score: float | None = Field(default=None, serialization_alias="relevanceScore")
    lexical_score: float | None = Field(default=None, serialization_alias="lexicalScore")
    semantic_score: float | None = Field(default=None, serialization_alias="semanticScore")
    rerank_score: float | None = Field(default=None, serialization_alias="rerankScore")
    retrieval_mode: str = Field(default="Lexical", serialization_alias="retrievalMode")
    explanation: str = ""
    usage_type: GroundingUsageType = Field(serialization_alias="usageType")


class LegalSourceRead(APIModel):
    id: str
    source_type: LegalSourceType = Field(serialization_alias="sourceType")
    title: str
    short_title: str = Field(serialization_alias="shortTitle")
    jurisdiction: str
    category: str
    act_name: str = Field(serialization_alias="actName")
    section_label: str = Field(serialization_alias="sectionLabel")
    section_number: str = Field(serialization_alias="sectionNumber")
    order_rule_label: str = Field(serialization_alias="orderRuleLabel")
    year: int | None = None
    language: str
    citation_label: str = Field(serialization_alias="citationLabel")
    content: str
    source_origin: str = Field(default="", serialization_alias="sourceOrigin")
    source_url: str = Field(default="", serialization_alias="sourceUrl")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")
    chunks: list[LegalSourceChunkRead] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class LegalRetrievalRequest(APIModel):
    query: str
    task_type: ChamberTaskType | None = Field(default=None, serialization_alias="taskType")
    case_id: str | None = Field(default=None, serialization_alias="caseId")
    language: str | None = None


class LegalRetrievalRead(APIModel):
    query: str
    status: str
    summary: str
    sources: list[GroundingSourceRead] = Field(default_factory=list)


class LegalIngestionRead(APIModel):
    sources_created: int = Field(serialization_alias="sourcesCreated")
    chunks_created: int = Field(serialization_alias="chunksCreated")


class CaseLegalBasisRead(APIModel):
    case_id: str = Field(serialization_alias="caseId")
    sources: list[GroundingSourceRead] = Field(default_factory=list)
