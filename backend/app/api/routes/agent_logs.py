from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agent_log import AgentRunLogCreate, AgentRunLogRead
from app.services import agent_logs as agent_log_service
from app.services import cases as case_service
from app.services.serializers import serialize_agent_log
from app.utils.http import not_found

router = APIRouter()


@router.get("/cases/{case_id}/agent-logs", response_model=list[AgentRunLogRead])
def get_case_agent_logs(case_id: str, db: Session = Depends(get_db)) -> list[AgentRunLogRead]:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    return [
        serialize_agent_log(log)
        for log in agent_log_service.list_agent_logs(db, case_id)
    ]


@router.post(
    "/cases/{case_id}/agent-logs",
    response_model=AgentRunLogRead,
    status_code=status.HTTP_201_CREATED,
)
def create_case_agent_log(
    case_id: str,
    payload: AgentRunLogCreate,
    db: Session = Depends(get_db),
) -> AgentRunLogRead:
    if not case_service.case_exists(db, case_id):
        raise not_found("Case not found.")
    log = agent_log_service.create_agent_log(db, case_id, payload)
    return serialize_agent_log(log)
