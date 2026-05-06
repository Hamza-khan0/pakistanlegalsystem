from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.services import cases as case_service
from app.services import notes as note_service
from app.services.serializers import serialize_note
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/notes", response_model=list[NoteRead])
def get_case_notes(case_id: str, db: Session = Depends(get_db)) -> list[NoteRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [serialize_note(note) for note in note_service.list_notes(db, case_id)]


@router.post("/cases/{case_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_case_note(
    case_id: str,
    payload: NoteCreate,
    db: Session = Depends(get_db),
) -> NoteRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    note = note_service.create_note(db, case_id, payload)
    return serialize_note(note)


@router.patch("/notes/{note_id}", response_model=NoteRead)
def update_note(
    note_id: str,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
) -> NoteRead:
    note = note_service.get_note_or_none(db, note_id)
    if not note:
        raise not_found("Note not found.")
    updated = note_service.update_note(db, note, payload)
    return serialize_note(updated)
