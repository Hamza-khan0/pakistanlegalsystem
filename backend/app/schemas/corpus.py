from datetime import datetime

from pydantic import Field

from app.models.enums import CorpusSourceKind, DatasetSplit
from app.schemas.base import APIModel


class CorpusEntryRead(APIModel):
    id: str
    source_kind: CorpusSourceKind = Field(serialization_alias="sourceKind")
    crawled_document_id: str | None = Field(default=None, serialization_alias="crawledDocumentId")
    legal_source_id: str | None = Field(default=None, serialization_alias="legalSourceId")
    title: str
    language: str
    normalized_text: str = Field(serialization_alias="normalizedText")
    chunk_count: int = Field(serialization_alias="chunkCount")
    ready_for_retrieval: bool = Field(serialization_alias="readyForRetrieval")
    ready_for_training: bool = Field(serialization_alias="readyForTraining")
    dataset_split: DatasetSplit = Field(serialization_alias="datasetSplit")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class CorpusBuildRead(APIModel):
    legal_sources_upserted: int = Field(serialization_alias="legalSourcesUpserted")
    corpus_entries_upserted: int = Field(serialization_alias="corpusEntriesUpserted")
    crawled_documents_promoted: int = Field(serialization_alias="crawledDocumentsPromoted")


class CorpusExportRead(APIModel):
    output_dir: str = Field(serialization_alias="outputDir")
    retrieval_records: int = Field(serialization_alias="retrievalRecords")
    classification_records: int = Field(serialization_alias="classificationRecords")
    bilingual_records: int = Field(serialization_alias="bilingualRecords")
    files: list[str] = Field(default_factory=list)
