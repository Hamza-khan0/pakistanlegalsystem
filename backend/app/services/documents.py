from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.case import Case
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentMetadataCreate


def list_documents(
    db: Session,
    *,
    q: str | None = None,
    case_id: str | None = None,
    document_type: str | None = None,
    extraction_status: str | None = None,
) -> list[Document]:
    query = select(Document).join(Document.case).where(Case.archived.is_(False)).options(selectinload(Document.case))

    if q:
        like_value = f"%{q.strip()}%"
        query = query.where(
            or_(
                Document.name.ilike(like_value),
                Document.summary.ilike(like_value),
                Document.file_name.ilike(like_value),
            )
        )

    if case_id:
        query = query.where(Document.case_id == case_id)

    if document_type:
        query = query.where(Document.document_type == document_type)

    if extraction_status:
        query = query.where(Document.extraction_status == extraction_status)

    query = query.order_by(Document.upload_date.desc())
    return list(db.scalars(query).all())


def get_document_or_none(db: Session, document_id: str) -> Document | None:
    return db.scalar(
        select(Document)
        .options(selectinload(Document.case))
        .where(Document.id == document_id)
    )


def create_document_record(db: Session, payload: DocumentCreate | DocumentMetadataCreate) -> Document:
    document = Document(
        case_id=payload.case_id,
        name=payload.name,
        document_type=payload.type,
        status=payload.status,
        category=payload.category,
        file_name=payload.file_name,
        file_path=payload.file_path,
        mime_type=payload.mime_type,
        tags=payload.tags,
        extraction_status=payload.extraction_status,
        ocr_status=payload.ocr_status,
        parsing_status=payload.parsing_status,
        intelligence_status=payload.intelligence_status,
        extracted_text_preview=payload.preview_text,
        extracted_text=payload.extracted_text,
        extraction_error=payload.extraction_error,
        processed_at=payload.processed_at,
        summary=payload.summary,
        filed_by=payload.filed_by,
        pages=payload.pages,
        metadata_json=payload.metadata_json,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


async def save_upload_file(upload: UploadFile, *, case_id: str) -> tuple[str, str]:
    upload_root = Path(settings.uploads_dir)
    case_directory = upload_root / case_id
    case_directory.mkdir(parents=True, exist_ok=True)

    suffix = Path(upload.filename or "document.bin").suffix
    stored_name = f"{uuid4().hex}{suffix}"
    destination = case_directory / stored_name

    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            output.write(chunk)

    return str(destination), upload.filename or stored_name
