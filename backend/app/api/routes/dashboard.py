from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryRead
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard")


@router.get("/summary", response_model=DashboardSummaryRead)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryRead:
    return get_dashboard_summary(db)
