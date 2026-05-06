from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentMetadataCreate, DocumentRead
from app.services import cases as case_service
from app.services import documents as document_service
from app.services.intelligence.document_extraction import process_document_by_id
from app.services.serializers import serialize_document
from app.utils.http import not_found

router = APIRouter()


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(
    q: str | None = Query(default=None),
    case_id: str | None = Query(default=None, alias="caseId"),
    document_type: str | None = Query(default=None, alias="type"),
    extraction_status: str | None = Query(default=None, alias="extractionStatus"),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    records = document_service.list_documents(
        db,
        q=q,
        case_id=case_id,
        document_type=document_type,
        extraction_status=extraction_status,
    )
    return [serialize_document(record) for record in records]


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentMetadataCreate,
    db: Session = Depends(get_db),
) -> DocumentRead:
    if not case_service.case_exists(db, payload.case_id):
        raise not_found("Case not found.")
    document = document_service.create_document_record(db, payload)
    return serialize_document(document_service.get_document_or_none(db, document.id) or document)


@router.post("/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: str = Form(alias="caseId"),
    name: str = Form(),
    type: str = Form(),
    status_value: str = Form(default="Reference", alias="status"),
    category: str = Form(default=""),
    tags: str = Form(default=""),
    extraction_status: str = Form(default="Ready for Indexing", alias="extractionStatus"),
    ocr_status: str = Form(default="Not Started", alias="ocrStatus"),
    parsing_status: str = Form(default="Not Started", alias="parsingStatus"),
    preview_text: str = Form(default="", alias="previewText"),
    summary: str = Form(default=""),
    filed_by: str = Form(default="", alias="filedBy"),
    pages: int = Form(default=0),
    file: UploadFile = File(),
    db: Session = Depends(get_db),
) -> DocumentRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a filename.")

    file_path, original_name = await document_service.save_upload_file(file, case_id=case_id)
    tags_list = [item.strip() for item in tags.split(",") if item.strip()]

    payload = DocumentMetadataCreate(
        case_id=case_id,
        name=name,
        type=type,
        status=status_value,
        category=category,
        file_name=original_name,
        file_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        tags=tags_list,
        extraction_status=extraction_status,
        ocr_status=ocr_status,
        parsing_status=parsing_status,
        preview_text=preview_text,
        summary=summary,
        filed_by=filed_by,
        pages=pages,
        metadata_json={},
    )
    document = document_service.create_document_record(db, payload)
    return serialize_document(document_service.get_document_or_none(db, document.id) or document)


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentRead:
    document = document_service.get_document_or_none(db, document_id)
    if not document:
        raise not_found("Document not found.")
    return serialize_document(document)


@router.post("/documents/{document_id}/process", response_model=DocumentRead)
def process_document(document_id: str, db: Session = Depends(get_db)) -> DocumentRead:
    document = process_document_by_id(db, document_id)
    if not document:
        raise not_found("Document not found.")
    return serialize_document(document)


@router.get("/documents/{document_id}/extraction", response_model=DocumentRead)
def get_document_extraction(document_id: str, db: Session = Depends(get_db)) -> DocumentRead:
    document = document_service.get_document_or_none(db, document_id)
    if not document:
        raise not_found("Document not found.")
    return serialize_document(document)


@router.get("/cases/{case_id}/documents", response_model=list[DocumentRead])
def get_case_documents(case_id: str, db: Session = Depends(get_db)) -> list[DocumentRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [
        serialize_document(document)
        for document in document_service.list_documents(db, case_id=case_id)
    ]
