from uuid import uuid4

from sqlalchemy import Select, asc, desc, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.case_prediction import CasePrediction
from app.models.chamber_run import ChamberRun
from app.models.grounding_link import GroundingLink
from app.models.intelligence_artifact import IntelligenceArtifact
from app.schemas.case import CaseCreate, CaseUpdate


def _normalize_fact_rows(facts: list[object]) -> list[dict]:
    normalized: list[dict] = []
    for fact in facts:
        if isinstance(fact, dict):
            normalized.append(fact)
            continue
        if hasattr(fact, "model_dump"):
            normalized.append(fact.model_dump())
            continue
        normalized.append(
            {
                "label": getattr(fact, "label", ""),
                "text": getattr(fact, "text", ""),
            }
        )
    return normalized


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _generate_case_number(db: Session) -> str:
    for _ in range(10):
        candidate = f"CASE-{uuid4().hex[:8].upper()}"
        exists = db.scalar(select(Case.id).where(Case.case_number == candidate))
        if not exists:
            return candidate
    return f"CASE-{uuid4().hex.upper()}"


def base_case_query() -> Select[tuple[Case]]:
    return (
        select(Case)
        .where(Case.archived.is_(False))
        .options(
            selectinload(Case.documents),
            selectinload(Case.timeline_events),
            selectinload(Case.notes),
            selectinload(Case.research_entries),
            selectinload(Case.drafts),
            selectinload(Case.agent_run_logs),
            selectinload(Case.intelligence_artifacts)
            .selectinload(IntelligenceArtifact.grounding_links)
            .joinedload(GroundingLink.source),
            selectinload(Case.intelligence_artifacts)
            .selectinload(IntelligenceArtifact.grounding_links)
            .joinedload(GroundingLink.chunk),
            selectinload(Case.chamber_runs).selectinload(ChamberRun.steps),
            selectinload(Case.chamber_runs)
            .selectinload(ChamberRun.grounding_links)
            .joinedload(GroundingLink.source),
            selectinload(Case.chamber_runs)
            .selectinload(ChamberRun.grounding_links)
            .joinedload(GroundingLink.chunk),
            selectinload(Case.predictions).selectinload(CasePrediction.model),
        )
    )


def list_cases(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    forum: str | None = None,
    sort: str = "hearing",
    order: str = "asc",
    limit: int | None = None,
) -> list[Case]:
    query = select(Case).where(Case.archived.is_(False))

    if q:
        like_value = f"%{q.strip()}%"
        query = query.where(
            or_(
                Case.title.ilike(like_value),
                Case.case_number.ilike(like_value),
                Case.client_name.ilike(like_value),
                Case.opposing_party.ilike(like_value),
                Case.forum.ilike(like_value),
            )
        )

    if status:
        query = query.where(Case.status == status)

    if priority:
        query = query.where(Case.priority == priority)

    if forum:
        query = query.where(Case.forum.ilike(f"%{forum.strip()}%"))

    sort_map = {
        "title": Case.title,
        "priority": Case.priority,
        "updated": Case.updated_at,
        "hearing": Case.next_hearing_date,
    }
    sort_column = sort_map.get(sort, Case.next_hearing_date)
    sort_fn = desc if order.lower() == "desc" else asc
    query = query.order_by(sort_fn(sort_column), desc(Case.updated_at))

    if limit is not None:
        query = query.limit(limit)

    return list(db.scalars(query).all())


def get_case_or_none(db: Session, case_id: str) -> Case | None:
    return db.scalar(base_case_query().where(Case.id == case_id))


def case_exists(db: Session, case_id: str) -> bool:
    return db.scalar(select(Case.id).where(Case.id == case_id, Case.archived.is_(False))) is not None


def create_case(db: Session, payload: CaseCreate) -> Case:
    facts_background = _normalize_fact_rows(payload.facts_background)
    if payload.facts and not facts_background:
        facts_background = [{"label": "Case facts", "text": payload.facts.strip()}]

    case = Case(
        title=payload.title,
        case_number=payload.case_number or _generate_case_number(db),
        forum=payload.forum or payload.court or "Forum to be confirmed",
        matter_type=payload.matter_type or payload.case_type or "General Matter",
        status=payload.status,
        priority=payload.priority,
        client_name=payload.client or payload.client_name or "Client to be confirmed",
        opposing_party=payload.opposing_party or "Opposing party to be confirmed",
        summary=payload.summary or payload.facts or "",
        legal_issues=_normalize_string_list(payload.issues),
        relief_sought=_normalize_string_list(payload.relief_sought),
        next_hearing_date=payload.next_hearing_date,
        assigned_counsel=_normalize_string_list(payload.assigned_counsel),
        filing_stage=payload.stage,
        risk_flags=_normalize_string_list(payload.risk_flags),
        important_notes=_normalize_string_list(payload.important_notes),
        facts_background=facts_background,
        linked_statutes=_normalize_string_list(payload.linked_statutes),
        precedents=_normalize_string_list(payload.precedents),
        procedural_alerts=_normalize_string_list(payload.procedural_alerts),
        tags=_normalize_string_list(payload.tags),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_case(db: Session, case: Case, payload: CaseUpdate) -> Case:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "client":
            case.client_name = value
        elif field == "stage":
            case.filing_stage = value
        elif field == "issues":
            case.legal_issues = value
        elif field == "facts_background":
            case.facts_background = _normalize_fact_rows(value)
        elif field == "type":
            case.matter_type = value
        elif field == "matter_type":
            case.matter_type = value
        elif field == "relief_sought":
            case.relief_sought = value
        elif field == "opposing_party":
            case.opposing_party = value
        elif field == "case_number":
            case.case_number = value
        elif field == "next_hearing_date":
            case.next_hearing_date = value
        elif field == "assigned_counsel":
            case.assigned_counsel = value
        elif field == "risk_flags":
            case.risk_flags = value
        elif field == "important_notes":
            case.important_notes = value
        elif field == "linked_statutes":
            case.linked_statutes = value
        elif field == "procedural_alerts":
            case.procedural_alerts = value
        else:
            setattr(case, field, value)

    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def archive_case(db: Session, case: Case) -> None:
    case.archived = True
    db.add(case)
    db.commit()
