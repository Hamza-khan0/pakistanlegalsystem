from datetime import date, datetime

from app.schemas.base import APIModel


class CaseFactRead(APIModel):
    label: str
    text: str


class DashboardActivityRead(APIModel):
    id: str
    title: str
    detail: str
    timestamp: str
    category: str


class DeadlineRead(APIModel):
    id: str
    case_id: str
    title: str
    due_date: date
    owner: str
    severity: str
    note: str


class NotificationRead(APIModel):
    id: str
    title: str
    detail: str
    timestamp: datetime
    tone: str
