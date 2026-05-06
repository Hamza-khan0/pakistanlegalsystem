from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.case import Case
from app.models.chamber_run import ChamberRun
from app.models.chamber_run_step import ChamberRunStep
from app.models.grounding_link import GroundingLink


def _base_run_query():
    return (
        select(ChamberRun)
        .options(
            joinedload(ChamberRun.case),
            selectinload(ChamberRun.steps),
            selectinload(ChamberRun.grounding_links)
            .joinedload(GroundingLink.source),
            selectinload(ChamberRun.grounding_links)
            .joinedload(GroundingLink.chunk),
        )
    )


def get_run_or_none(db: Session, run_id: str) -> ChamberRun | None:
    return db.scalar(_base_run_query().where(ChamberRun.id == run_id))


def list_case_runs(db: Session, case_id: str, *, limit: int | None = None) -> list[ChamberRun]:
    query = (
        _base_run_query()
        .where(ChamberRun.case_id == case_id)
        .order_by(desc(ChamberRun.started_at))
    )
    if limit is not None:
        query = query.limit(limit)
    return list(db.scalars(query).all())


def list_agent_activity(
    db: Session,
    *,
    case_id: str | None = None,
    limit: int = 20,
) -> list[ChamberRunStep]:
    query = (
        select(ChamberRunStep)
        .join(ChamberRunStep.run)
        .join(ChamberRun.case)
        .options(
            joinedload(ChamberRunStep.run).joinedload(ChamberRun.case),
        )
        .order_by(desc(ChamberRunStep.completed_at), desc(ChamberRunStep.created_at))
        .limit(limit)
    )
    if case_id:
        query = query.where(ChamberRun.case_id == case_id)
    return list(db.scalars(query).all())


def list_case_run_steps(db: Session, run_id: str) -> list[ChamberRunStep]:
    query = (
        select(ChamberRunStep)
        .where(ChamberRunStep.run_id == run_id)
        .options(joinedload(ChamberRunStep.run).joinedload(ChamberRun.case))
        .order_by(ChamberRunStep.step_order)
    )
    return list(db.scalars(query).all())
