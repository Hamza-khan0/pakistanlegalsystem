from datetime import datetime

from pydantic import Field

from app.models.enums import (
    CrawlDocumentStatus,
    CrawlJobStatus,
    CrawlMode,
    CrawlProcessingStatus,
    CrawlSourceType,
)
from app.schemas.base import APIModel


class CrawlSourceBase(APIModel):
    name: str
    source_type: CrawlSourceType = Field(serialization_alias="sourceType")
    base_url: str = Field(default="", serialization_alias="baseUrl")
    allowed_domains: list[str] = Field(default_factory=list, serialization_alias="allowedDomains")
    crawl_mode: CrawlMode = Field(serialization_alias="crawlMode")
    language_hint: str = Field(default="English", serialization_alias="languageHint")
    category: str = ""
    is_active: bool = Field(default=True, serialization_alias="isActive")
    config_json: dict = Field(default_factory=dict, serialization_alias="configJson")


class CrawlSourceCreate(CrawlSourceBase):
    pass


class CrawlSourceRead(CrawlSourceBase):
    id: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class CrawlRunRequest(APIModel):
    source_id: str = Field(serialization_alias="sourceId")


class CrawlJobRead(APIModel):
    id: str
    source_id: str = Field(serialization_alias="sourceId")
    source_name: str = Field(default="", serialization_alias="sourceName")
    status: CrawlJobStatus
    started_at: datetime = Field(serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    pages_fetched: int = Field(serialization_alias="pagesFetched")
    documents_discovered: int = Field(serialization_alias="documentsDiscovered")
    documents_saved: int = Field(serialization_alias="documentsSaved")
    errors_count: int = Field(serialization_alias="errorsCount")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")


class CrawledDocumentRead(APIModel):
    id: str
    source_id: str = Field(serialization_alias="sourceId")
    source_name: str = Field(default="", serialization_alias="sourceName")
    legal_source_id: str | None = Field(default=None, serialization_alias="legalSourceId")
    source_url: str = Field(serialization_alias="sourceUrl")
    title: str
    document_type: str = Field(serialization_alias="documentType")
    language: str
    jurisdiction: str
    raw_html_path: str = Field(serialization_alias="rawHtmlPath")
    raw_html_url: str = Field(default="", serialization_alias="rawHtmlUrl")
    downloaded_file_path: str = Field(serialization_alias="downloadedFilePath")
    downloaded_file_url: str = Field(default="", serialization_alias="downloadedFileUrl")
    mime_type: str = Field(serialization_alias="mimeType")
    crawl_status: CrawlDocumentStatus = Field(serialization_alias="crawlStatus")
    processing_status: CrawlProcessingStatus = Field(serialization_alias="processingStatus")
    duplicate_hash: str = Field(serialization_alias="duplicateHash")
    extracted_text: str = Field(serialization_alias="extractedText")
    extracted_text_preview: str = Field(serialization_alias="extractedTextPreview")
    normalized_text: str = Field(serialization_alias="normalizedText")
    ocr_engine: str = Field(serialization_alias="ocrEngine")
    ocr_status: str = Field(serialization_alias="ocrStatus")
    ocr_confidence_summary: float | None = Field(default=None, serialization_alias="ocrConfidenceSummary")
    language_detected: str = Field(serialization_alias="languageDetected")
    page_count: int = Field(serialization_alias="pageCount")
    errors_json: dict = Field(default_factory=dict, serialization_alias="errorsJson")
    processed_at: datetime | None = Field(default=None, serialization_alias="processedAt")
    metadata_json: dict = Field(default_factory=dict, serialization_alias="metadataJson")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
