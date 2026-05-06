from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_log import AgentRunLog
from app.schemas.agent_log import AgentRunLogCreate


def list_agent_logs(db: Session, case_id: str) -> list[AgentRunLog]:
    return list(
        db.scalars(
            select(AgentRunLog)
            .where(AgentRunLog.case_id == case_id)
            .order_by(AgentRunLog.started_at.desc())
        ).all()
    )


def create_agent_log(db: Session, case_id: str, payload: AgentRunLogCreate) -> AgentRunLog:
    log_kwargs = {
        "case_id": case_id,
        "agent_name": payload.agent_name,
        "title": payload.title,
        "task_type": payload.task_type,
        "input_summary": payload.input_summary,
        "output_summary": payload.output_summary,
        "status": payload.status,
        "confidence_score": payload.confidence_score,
        "citations": payload.citations,
        "next_action": payload.next_action,
        "metadata_json": payload.metadata_json,
        "completed_at": payload.completed_at,
    }
    if payload.started_at is not None:
        log_kwargs["started_at"] = payload.started_at

    log = AgentRunLog(
        **log_kwargs,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
