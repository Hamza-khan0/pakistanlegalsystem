from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.agent_log import AgentRunLog
from app.models.case import Case
from app.models.document import Document
from app.models.draft import Draft
from app.models.enums import AgentRunStatus, DraftStatus, PriorityLevel
from app.models.timeline import TimelineEvent
from app.schemas.dashboard import DashboardSummaryRead
from app.services.serializers import (
    make_activity,
    make_deadline,
    make_notification,
    serialize_case,
    severity_from_priority,
)


def get_dashboard_summary(db: Session) -> DashboardSummaryRead:
    active_cases = list(
        db.scalars(
            select(Case)
            .where(Case.archived.is_(False))
            .order_by(Case.next_hearing_date.asc().nullslast(), desc(Case.updated_at))
            .limit(6)
        ).all()
    )
    documents_count = db.query(Document).join(Document.case).filter(Case.archived.is_(False)).count()
    pending_filings_count = db.query(Draft).join(Draft.case).filter(
        Case.archived.is_(False),
        Draft.status.in_([DraftStatus.DRAFTING, DraftStatus.REVIEWING]),
    ).count()

    upcoming_cases = [
        case for case in active_cases if case.next_hearing_date and case.next_hearing_date >= date.today()
    ]
    urgent_deadlines = [
        make_deadline(
            item_id=f"deadline-{case.id}",
            case_id=case.id,
            title=f"Prepare for {case.case_number}",
            due_date=case.next_hearing_date,
            owner=(case.assigned_counsel[0] if case.assigned_counsel else "Case Team"),
            severity=severity_from_priority(case.priority),
            note=case.filing_stage or case.summary[:120],
        )
        for case in upcoming_cases[:4]
    ]

    recent_timeline = list(
        db.scalars(
            select(TimelineEvent)
            .join(TimelineEvent.case)
            .where(Case.archived.is_(False))
            .order_by(TimelineEvent.event_date.desc(), TimelineEvent.created_at.desc())
            .limit(5)
        ).all()
    )
    recent_agent_logs = list(
        db.scalars(
            select(AgentRunLog)
            .join(AgentRunLog.case)
            .where(Case.archived.is_(False))
            .order_by(AgentRunLog.started_at.desc())
            .limit(3)
        ).all()
    )

    recent_activity = [
        *[
            make_activity(
                item_id=event.id,
                title=event.title,
                detail=event.description,
                timestamp=event.created_at.strftime("%H:%M"),
                category=event.event_type.value,
            )
            for event in recent_timeline
        ],
        *[
            make_activity(
                item_id=log.id,
                title=f"{log.agent_name} completed {log.task_type}",
                detail=log.output_summary,
                timestamp=log.started_at.strftime("%H:%M"),
                category="Agent",
            )
            for log in recent_agent_logs
        ],
    ]

    notifications = [
        *[
            make_notification(
                item_id=f"notification-hearing-{case.id}",
                title=f"{case.case_number} approaching hearing",
                detail=f"{case.title} is listed on {case.next_hearing_date:%d %b %Y}.",
                timestamp=case.updated_at,
                tone="warning" if case.priority in {PriorityLevel.CRITICAL, PriorityLevel.HIGH} else "info",
            )
            for case in upcoming_cases[:2]
        ],
        *[
            make_notification(
                item_id=f"notification-agent-{log.id}",
                title=f"{log.agent_name} output available",
                detail=log.title or log.output_summary,
                timestamp=log.started_at,
                tone="success" if log.status == AgentRunStatus.COMPLETED else "info",
            )
            for log in recent_agent_logs[:2]
        ],
    ]

    urgent_deadlines_count = sum(
        1 for item in urgent_deadlines if item.severity in {PriorityLevel.CRITICAL.value, PriorityLevel.HIGH.value}
    )

    return DashboardSummaryRead(
        active_case_count=db.query(Case).filter(Case.archived.is_(False)).count(),
        urgent_deadlines_count=urgent_deadlines_count,
        pending_filings_count=pending_filings_count,
        uploaded_documents_count=documents_count,
        recent_activity=recent_activity[:6],
        upcoming_hearings=urgent_deadlines,
        urgent_deadlines=urgent_deadlines,
        notifications=notifications[:4],
        recent_cases=[serialize_case(case) for case in active_cases],
    )
