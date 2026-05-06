from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.draft import Draft
from app.schemas.draft import DraftCreate, DraftUpdate


def list_drafts(db: Session, case_id: str) -> list[Draft]:
    return list(
        db.scalars(
            select(Draft)
            .where(Draft.case_id == case_id)
            .order_by(Draft.updated_at.desc())
        ).all()
    )


def get_draft_or_none(db: Session, draft_id: str) -> Draft | None:
    return db.scalar(select(Draft).where(Draft.id == draft_id))


def create_draft(db: Session, case_id: str, payload: DraftCreate) -> Draft:
    draft = Draft(
        case_id=case_id,
        title=payload.title,
        draft_type=payload.type,
        status=payload.status,
        content=payload.content,
        version=payload.version,
        owner=payload.owner,
        summary=payload.summary,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def update_draft(db: Session, draft: Draft, payload: DraftUpdate) -> Draft:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "type":
            draft.draft_type = value
        else:
            setattr(draft, field, value)

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
