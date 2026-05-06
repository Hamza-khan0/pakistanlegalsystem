from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


def list_notes(db: Session, case_id: str) -> list[Note]:
    return list(
        db.scalars(
            select(Note)
            .where(Note.case_id == case_id)
            .order_by(Note.updated_at.desc())
        ).all()
    )


def get_note_or_none(db: Session, note_id: str) -> Note | None:
    return db.scalar(select(Note).where(Note.id == note_id))


def create_note(db: Session, case_id: str, payload: NoteCreate) -> Note:
    note = Note(
        case_id=case_id,
        title=payload.title,
        content=payload.content,
        note_type=payload.note_type,
        author=payload.author,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, note: Note, payload: NoteUpdate) -> Note:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(note, field, value)

    db.add(note)
    db.commit()
    db.refresh(note)
    return note
