from datetime import datetime

from pydantic import Field

from app.models.enums import NoteType
from app.schemas.base import APIModel


class NoteBase(APIModel):
    title: str
    content: str
    note_type: NoteType = Field(serialization_alias="noteType")
    author: str = ""


class NoteCreate(NoteBase):
    pass


class NoteUpdate(APIModel):
    title: str | None = None
    content: str | None = None
    note_type: NoteType | None = Field(default=None, serialization_alias="noteType")
    author: str | None = None


class NoteRead(NoteBase):
    id: str
    case_id: str = Field(serialization_alias="caseId")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
