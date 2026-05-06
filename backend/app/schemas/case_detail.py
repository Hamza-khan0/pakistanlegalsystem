from app.schemas.agent_log import AgentRunLogRead
from app.schemas.case import CaseRead
from app.schemas.document import DocumentRead
from app.schemas.draft import DraftRead
from app.schemas.intelligence import IntelligenceArtifactRead
from app.schemas.legal_sources import GroundingSourceRead
from app.schemas.note import NoteRead
from app.schemas.research import ResearchEntryRead
from app.schemas.runs import ChamberRunSummaryRead
from app.schemas.timeline import TimelineEventRead


class CaseDetailRead(CaseRead):
    documents: list[DocumentRead]
    timeline: list[TimelineEventRead]
    notes: list[NoteRead]
    research: list[ResearchEntryRead]
    drafts: list[DraftRead]
    agent_outputs: list[AgentRunLogRead]
    intelligence: list[IntelligenceArtifactRead]
    runs: list[ChamberRunSummaryRead]
    legal_basis: list[GroundingSourceRead]
