from datetime import date, datetime

from pydantic import Field

from app.models.enums import CaseStatus, PriorityLevel
from app.schemas.base import APIModel
from app.schemas.common import CaseFactRead


class CaseBase(APIModel):
    title: str
    case_number: str = Field(serialization_alias="caseNumber")
    forum: str
    matter_type: str = Field(serialization_alias="matterType")
    status: CaseStatus
    priority: PriorityLevel
    client: str
    opposing_party: str = Field(serialization_alias="opposingParty")
    summary: str = ""
    issues: list[str] = Field(default_factory=list)
    relief_sought: list[str] = Field(default_factory=list, serialization_alias="reliefSought")
    next_hearing_date: date | None = Field(default=None, serialization_alias="nextHearingDate")
    assigned_counsel: list[str] = Field(default_factory=list, serialization_alias="assignedCounsel")
    stage: str = ""
    risk_flags: list[str] = Field(default_factory=list, serialization_alias="riskFlags")
    important_notes: list[str] = Field(default_factory=list, serialization_alias="importantNotes")
    facts_background: list[CaseFactRead] = Field(default_factory=list, serialization_alias="factsBackground")
    linked_statutes: list[str] = Field(default_factory=list, serialization_alias="linkedStatutes")
    precedents: list[str] = Field(default_factory=list)
    procedural_alerts: list[str] = Field(default_factory=list, serialization_alias="proceduralAlerts")
    tags: list[str] = Field(default_factory=list)


class CaseCreate(APIModel):
    title: str
    case_number: str | None = Field(default=None, serialization_alias="caseNumber")
    forum: str | None = None
    court: str | None = None
    matter_type: str | None = Field(default=None, serialization_alias="matterType")
    case_type: str | None = Field(default=None, serialization_alias="caseType")
    status: CaseStatus = CaseStatus.ACTIVE
    priority: PriorityLevel = PriorityLevel.MEDIUM
    client: str | None = None
    client_name: str | None = Field(default=None, serialization_alias="clientName")
    opposing_party: str | None = Field(default=None, serialization_alias="opposingParty")
    summary: str = ""
    facts: str | None = None
    issues: list[str] = Field(default_factory=list)
    relief_sought: list[str] | str | None = Field(default_factory=list, serialization_alias="reliefSought")
    next_hearing_date: date | None = Field(default=None, serialization_alias="nextHearingDate")
    assigned_counsel: list[str] = Field(default_factory=list, serialization_alias="assignedCounsel")
    stage: str = ""
    risk_flags: list[str] = Field(default_factory=list, serialization_alias="riskFlags")
    important_notes: list[str] = Field(default_factory=list, serialization_alias="importantNotes")
    facts_background: list[CaseFactRead] = Field(default_factory=list, serialization_alias="factsBackground")
    linked_statutes: list[str] = Field(default_factory=list, serialization_alias="linkedStatutes")
    precedents: list[str] = Field(default_factory=list)
    procedural_alerts: list[str] = Field(default_factory=list, serialization_alias="proceduralAlerts")
    tags: list[str] = Field(default_factory=list)


class CaseUpdate(APIModel):
    title: str | None = None
    case_number: str | None = Field(default=None, serialization_alias="caseNumber")
    forum: str | None = None
    matter_type: str | None = Field(default=None, serialization_alias="matterType")
    status: CaseStatus | None = None
    priority: PriorityLevel | None = None
    client: str | None = None
    opposing_party: str | None = Field(default=None, serialization_alias="opposingParty")
    summary: str | None = None
    issues: list[str] | None = None
    relief_sought: list[str] | None = Field(default=None, serialization_alias="reliefSought")
    next_hearing_date: date | None = Field(default=None, serialization_alias="nextHearingDate")
    assigned_counsel: list[str] | None = Field(default=None, serialization_alias="assignedCounsel")
    stage: str | None = None
    risk_flags: list[str] | None = Field(default=None, serialization_alias="riskFlags")
    important_notes: list[str] | None = Field(default=None, serialization_alias="importantNotes")
    facts_background: list[CaseFactRead] | None = Field(default=None, serialization_alias="factsBackground")
    linked_statutes: list[str] | None = Field(default=None, serialization_alias="linkedStatutes")
    precedents: list[str] | None = None
    procedural_alerts: list[str] | None = Field(default=None, serialization_alias="proceduralAlerts")
    tags: list[str] | None = None


class CaseRead(CaseBase):
    id: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
