from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.timeline import TimelineEvent
from app.schemas.timeline import TimelineEventCreate


def list_timeline_events(db: Session, case_id: str) -> list[TimelineEvent]:
    return list(
        db.scalars(
            select(TimelineEvent)
            .where(TimelineEvent.case_id == case_id)
            .order_by(TimelineEvent.event_date.desc(), TimelineEvent.created_at.desc())
        ).all()
    )


def create_timeline_event(db: Session, case_id: str, payload: TimelineEventCreate) -> TimelineEvent:
    event = TimelineEvent(
        case_id=case_id,
        title=payload.title,
        event_type=payload.type,
        description=payload.description,
        actor=payload.actor,
        event_date=payload.date,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
