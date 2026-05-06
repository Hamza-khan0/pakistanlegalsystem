from datetime import datetime

from pydantic import Field

from app.models.enums import (
    DocumentStatus,
    DocumentType,
    ExtractionStatus,
    IntelligenceStatus,
    OcrStatus,
    ParsingStatus,
    PriorityLevel,
)
from app.schemas.base import APIModel


class DocumentBase(APIModel):
    case_id: str = Field(serialization_alias="caseId")
    name: str
    type: DocumentType
    status: DocumentStatus = DocumentStatus.REFERENCE
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    extraction_status: ExtractionStatus = Field(
        default=ExtractionStatus.READY_FOR_INDEXING,
        serialization_alias="extractionStatus",
    )
    ocr_status: OcrStatus = Field(default=OcrStatus.NOT_STARTED, serialization_alias="ocrStatus")
    parsing_status: ParsingStatus = Field(
        default=ParsingStatus.NOT_STARTED,
        serialization_alias="parsingStatus",
    )
    intelligence_status: IntelligenceStatus = Field(
        default=IntelligenceStatus.NOT_PROCESSED,
        serialization_alias="intelligenceStatus",
    )
    preview_text: str = Field(default="", serialization_alias="previewText")
    extracted_text: str = Field(default="", serialization_alias="extractedText")
    extraction_error: str = Field(default="", serialization_alias="extractionError")
    processed_at: datetime | None = Field(default=None, serialization_alias="processedAt")
    summary: str = ""
    filed_by: str = Field(default="", serialization_alias="filedBy")
    pages: int = 0
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")


class DocumentCreate(DocumentBase):
    file_name: str = Field(serialization_alias="fileName")
    file_path: str = Field(serialization_alias="filePath")
    mime_type: str = Field(default="application/octet-stream", serialization_alias="mimeType")


class DocumentMetadataCreate(DocumentBase):
    file_name: str = Field(serialization_alias="fileName")
    file_path: str = Field(serialization_alias="filePath")
    mime_type: str = Field(default="application/octet-stream", serialization_alias="mimeType")


class DocumentRead(DocumentBase):
    id: str
    file_name: str = Field(serialization_alias="fileName")
    file_path: str = Field(serialization_alias="filePath")
    file_url: str = Field(serialization_alias="fileUrl")
    mime_type: str = Field(serialization_alias="mimeType")
    upload_date: datetime = Field(serialization_alias="uploadDate")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    case_title: str | None = Field(default=None, serialization_alias="caseTitle")
    case_number: str | None = Field(default=None, serialization_alias="caseNumber")
    case_forum: str | None = Field(default=None, serialization_alias="caseForum")
    case_priority: PriorityLevel | None = Field(default=None, serialization_alias="casePriority")
