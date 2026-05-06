from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.grounding_link import GroundingLink
from app.models.intelligence_artifact import IntelligenceArtifact


def list_case_intelligence(db: Session, case_id: str) -> list[IntelligenceArtifact]:
    return list(
        db.scalars(
            select(IntelligenceArtifact)
            .options(
                selectinload(IntelligenceArtifact.document),
                selectinload(IntelligenceArtifact.grounding_links).joinedload(GroundingLink.source),
                selectinload(IntelligenceArtifact.grounding_links).joinedload(GroundingLink.chunk),
            )
            .where(IntelligenceArtifact.case_id == case_id)
            .order_by(IntelligenceArtifact.updated_at.desc())
        ).all()
    )


def get_artifact_or_none(db: Session, artifact_id: str) -> IntelligenceArtifact | None:
    return db.scalar(
        select(IntelligenceArtifact)
        .options(
            selectinload(IntelligenceArtifact.document),
            selectinload(IntelligenceArtifact.grounding_links).joinedload(GroundingLink.source),
            selectinload(IntelligenceArtifact.grounding_links).joinedload(GroundingLink.chunk),
        )
        .where(IntelligenceArtifact.id == artifact_id)
    )
