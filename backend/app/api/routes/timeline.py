from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.timeline import TimelineEventCreate, TimelineEventRead
from app.services import cases as case_service
from app.services import timeline as timeline_service
from app.services.serializers import serialize_timeline_event
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/timeline", response_model=list[TimelineEventRead])
def get_case_timeline(case_id: str, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [
        serialize_timeline_event(item)
        for item in timeline_service.list_timeline_events(db, case_id)
    ]


@router.post(
    "/cases/{case_id}/timeline",
    response_model=TimelineEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_case_timeline_event(
    case_id: str,
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
) -> TimelineEventRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    event = timeline_service.create_timeline_event(db, case_id, payload)
    return serialize_timeline_event(event)
