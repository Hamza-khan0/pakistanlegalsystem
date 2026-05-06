from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.draft import DraftCreate, DraftRead, DraftUpdate
from app.services import cases as case_service
from app.services import drafts as draft_service
from app.services.serializers import serialize_draft
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/drafts", response_model=list[DraftRead])
def get_case_drafts(case_id: str, db: Session = Depends(get_db)) -> list[DraftRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [serialize_draft(draft) for draft in draft_service.list_drafts(db, case_id)]


@router.post("/cases/{case_id}/drafts", response_model=DraftRead, status_code=status.HTTP_201_CREATED)
def create_case_draft(
    case_id: str,
    payload: DraftCreate,
    db: Session = Depends(get_db),
) -> DraftRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    draft = draft_service.create_draft(db, case_id, payload)
    return serialize_draft(draft)


@router.patch("/drafts/{draft_id}", response_model=DraftRead)
def update_draft(
    draft_id: str,
    payload: DraftUpdate,
    db: Session = Depends(get_db),
) -> DraftRead:
    draft = draft_service.get_draft_or_none(db, draft_id)
    if not draft:
        raise not_found("Draft not found.")
    updated = draft_service.update_draft(db, draft, payload)
    return serialize_draft(updated)
