from __future__ import annotations

from collections import OrderedDict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import GroundingUsageType
from app.models.grounding_link import GroundingLink
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.chamber_run import ChamberRun
from app.services.knowledge.retrieval import RetrievedLegalSource


def persist_grounding_links(
    db: Session,
    *,
    run: ChamberRun | None = None,
    artifact: IntelligenceArtifact | None = None,
    sources: list[RetrievedLegalSource],
    usage_type: GroundingUsageType = GroundingUsageType.RETRIEVED,
) -> list[GroundingLink]:
    created: list[GroundingLink] = []
    seen: set[tuple[str, str | None]] = set()
    for source in sources:
        identity = (source.source_id, source.chunk_id)
        if identity in seen:
            continue
        seen.add(identity)
        link = GroundingLink(
            run_id=run.id if run else None,
            artifact_id=artifact.id if artifact else None,
            source_id=source.source_id,
            chunk_id=source.chunk_id,
            relevance_score=source.relevance_score,
            usage_type=usage_type,
            excerpt=source.excerpt,
            metadata_json={
                "lexicalScore": source.lexical_score,
                "semanticScore": source.semantic_score,
                "rerankScore": source.rerank_score,
                "retrievalMode": source.retrieval_mode,
                "explanation": source.explanation,
            },
        )
        db.add(link)
        created.append(link)
    db.flush()
    return created


def _grounding_link_query():
    return (
        select(GroundingLink)
        .options(
            joinedload(GroundingLink.source),
            joinedload(GroundingLink.chunk),
        )
        .order_by(desc(GroundingLink.relevance_score), desc(GroundingLink.created_at))
    )


def list_run_grounding_links(db: Session, run_id: str) -> list[GroundingLink]:
    return list(db.scalars(_grounding_link_query().where(GroundingLink.run_id == run_id)).all())


def list_artifact_grounding_links(db: Session, artifact_id: str) -> list[GroundingLink]:
    return list(
        db.scalars(_grounding_link_query().where(GroundingLink.artifact_id == artifact_id)).all()
    )


def collect_case_legal_basis(db: Session, case_id: str, *, limit: int = 12) -> list[GroundingLink]:
    run_links = (
        select(GroundingLink)
        .join(GroundingLink.run, isouter=True)
        .join(GroundingLink.artifact, isouter=True)
        .options(joinedload(GroundingLink.source), joinedload(GroundingLink.chunk))
        .where(
            (ChamberRun.case_id == case_id) | (IntelligenceArtifact.case_id == case_id)
        )
        .order_by(desc(GroundingLink.relevance_score), desc(GroundingLink.created_at))
    )
    links = list(db.scalars(run_links).all())

    deduped: "OrderedDict[tuple[str, str | None], GroundingLink]" = OrderedDict()
    for link in links:
        key = (link.source_id, link.chunk_id)
        if key not in deduped:
            deduped[key] = link
        if len(deduped) >= limit:
            break
    return list(deduped.values())
