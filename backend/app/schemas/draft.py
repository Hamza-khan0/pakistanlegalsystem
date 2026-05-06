from datetime import datetime

from pydantic import Field

from app.models.enums import DraftStatus
from app.schemas.base import APIModel


class DraftBase(APIModel):
    title: str
    type: str
    status: DraftStatus
    content: str = ""
    version: int = 1
    owner: str = ""
    summary: str = ""


class DraftCreate(DraftBase):
    pass


class DraftUpdate(APIModel):
    title: str | None = None
    type: str | None = None
    status: DraftStatus | None = None
    content: str | None = None
    version: int | None = None
    owner: str | None = None
    summary: str | None = None


class DraftRead(DraftBase):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
