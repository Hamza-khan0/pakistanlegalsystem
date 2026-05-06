from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research import ResearchEntry
from app.schemas.research import ResearchEntryCreate


def list_research_entries(db: Session, case_id: str) -> list[ResearchEntry]:
    return list(
        db.scalars(
            select(ResearchEntry)
            .where(ResearchEntry.case_id == case_id)
            .order_by(ResearchEntry.updated_at.desc())
        ).all()
    )


def create_research_entry(db: Session, case_id: str, payload: ResearchEntryCreate) -> ResearchEntry:
    entry = ResearchEntry(
        case_id=case_id,
        title=payload.title,
        query=payload.query,
        summary=payload.summary,
        citations=payload.citations,
        source_type=payload.source_type,
        status=payload.status,
        author=payload.author,
        next_question=payload.next_question,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
