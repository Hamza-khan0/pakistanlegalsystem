from app.schemas.base import APIModel
from app.schemas.case import CaseRead
from app.schemas.common import DashboardActivityRead, DeadlineRead, NotificationRead


class DashboardSummaryRead(APIModel):
    active_case_count: int
    urgent_deadlines_count: int
    pending_filings_count: int
    uploaded_documents_count: int
    recent_activity: list[DashboardActivityRead]
    upcoming_hearings: list[DeadlineRead]
    urgent_deadlines: list[DeadlineRead]
    notifications: list[NotificationRead]
    recent_cases: list[CaseRead]
