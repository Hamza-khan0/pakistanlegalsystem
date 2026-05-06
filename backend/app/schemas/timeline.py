from datetime import date, datetime

from pydantic import Field

from app.models.enums import TimelineEventType
from app.schemas.base import APIModel


class TimelineEventBase(APIModel):
    title: str
    type: TimelineEventType
    description: str = ""
    actor: str = ""
    date: date


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventRead(TimelineEventBase):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    created_at: datetime = Field(serialization_alias="createdAt")
