from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MlTaskName
from app.models.tier1_document import Tier1Document
from app.models.tier1_label import Tier1Label


@dataclass(slots=True)
class LabelCandidate:
    task_name: MlTaskName
    label: str
    label_source: str
    confidence_score: float
    evidence_text: str
    rule_name: str
    needs_review: bool


OUTCOME_RULES: tuple[tuple[str, str], ...] = (
    ("partly_allowed", "partly allowed"),
    ("partly_allowed", "partially allowed"),
    ("allowed", "appeal is allowed"),
    ("allowed", "petition is allowed"),
    ("allowed", "application is allowed"),
    ("allowed", "suit is decreed"),
    ("dismissed", "appeal is dismissed"),
    ("dismissed", "petition is dismissed"),
    ("dismissed", "application is dismissed"),
    ("dismissed", "suit is dismissed"),
    ("remanded", "matter is remanded"),
    ("remanded", "case is remanded"),
    ("remanded", "remanded back"),
    ("disposed", "stands disposed"),
    ("disposed", "disposed of"),
    ("withdrawn", "dismissed as withdrawn"),
    ("withdrawn", "withdrawn"),
)

CASE_TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("constitutional", ("article 199", "writ", "constitutional petition")),
    ("criminal", ("bail", "fir", "crpc", "criminal", "section 497")),
    ("revenue", ("mutation", "revenue", "land record", "board of revenue")),
    ("customs", ("customs", "seizure", "fbr", "valuation")),
    ("service", ("service tribunal", "appointment", "promotion", "seniority")),
    ("family", ("family", "guardian", "maintenance", "custody")),
    ("tax", ("income tax", "sales tax", "tax reference")),
    ("commercial", ("company", "contract", "commercial", "recovery")),
    ("property", ("property", "injunction", "declaration", "specific relief")),
    ("civil", ("cpc", "civil suit", "order vii", "plaint")),
)


def _window(text: str, phrase: str) -> str:
    lower = text.casefold()
    index = lower.find(phrase)
    if index == -1:
        return text[-360:].strip()
    return text[max(index - 140, 0) : index + len(phrase) + 180].strip()


def _outcome_label(text: str) -> LabelCandidate:
    final_text = text[-6000:].casefold()
    matches: list[tuple[str, str]] = []
    for label, phrase in OUTCOME_RULES:
        if phrase in final_text:
            matches.append((label, phrase))

    labels = {label for label, _phrase in matches}
    if len(labels) == 1:
        label, phrase = matches[0]
        return LabelCandidate(
            task_name=MlTaskName.CASE_OUTCOME,
            label=label,
            label_source="weak_supervision",
            confidence_score=0.82,
            evidence_text=_window(text, phrase),
            rule_name=f"outcome_phrase:{phrase}",
            needs_review=False,
        )
    if len(labels) > 1:
        return LabelCandidate(
            task_name=MlTaskName.CASE_OUTCOME,
            label="unknown",
            label_source="weak_supervision",
            confidence_score=0.2,
            evidence_text="Conflicting outcome phrases: " + ", ".join(sorted(labels)),
            rule_name="outcome_conflict",
            needs_review=True,
        )
    return LabelCandidate(
        task_name=MlTaskName.CASE_OUTCOME,
        label="unknown",
        label_source="weak_supervision",
        confidence_score=0.1,
        evidence_text=text[-360:].strip(),
        rule_name="outcome_unknown",
        needs_review=True,
    )


def _maintainability_label(text: str) -> LabelCandidate:
    lower = text.casefold()
    hard_phrases = ("not maintainable", "dismissed on maintainability", "plaint rejected")
    objection_phrases = (
        "maintainability",
        "alternate remedy",
        "barred by law",
        "limitation",
        "locus standi",
        "jurisdiction",
        "res judicata",
        "order vii rule 11",
    )
    for phrase in hard_phrases:
        if phrase in lower:
            return LabelCandidate(
                task_name=MlTaskName.MAINTAINABILITY,
                label="not_maintainable",
                label_source="weak_supervision",
                confidence_score=0.74,
                evidence_text=_window(text, phrase),
                rule_name=f"maintainability_hard:{phrase}",
                needs_review=True,
            )
    for phrase in objection_phrases:
        if phrase in lower:
            return LabelCandidate(
                task_name=MlTaskName.MAINTAINABILITY,
                label="objection_prone",
                label_source="weak_supervision",
                confidence_score=0.62,
                evidence_text=_window(text, phrase),
                rule_name=f"maintainability_signal:{phrase}",
                needs_review=True,
            )
    if "petition is allowed" in lower or "suit is decreed" in lower:
        return LabelCandidate(
            task_name=MlTaskName.MAINTAINABILITY,
            label="likely_maintainable",
            label_source="weak_supervision",
            confidence_score=0.54,
            evidence_text=_window(text, "allowed" if "allowed" in lower else "decreed"),
            rule_name="maintainability_inferred_from_positive_outcome",
            needs_review=True,
        )
    return LabelCandidate(
        task_name=MlTaskName.MAINTAINABILITY,
        label="uncertain",
        label_source="weak_supervision",
        confidence_score=0.2,
        evidence_text=text[:360].strip(),
        rule_name="maintainability_uncertain",
        needs_review=True,
    )


def _risk_label(text: str, metadata: dict[str, Any]) -> LabelCandidate:
    lower = text.casefold()
    high_signals = (
        "not maintainable",
        "dismissed",
        "limitation",
        "jurisdiction",
        "barred by law",
        "conflicting",
    )
    medium_signals = ("maintainability", "alternate remedy", "procedural", "uncertain", "partial")
    missing_metadata = sum(
        1
        for key in ("court", "date", "citation", "case_number")
        if not str(metadata.get(key) or "").strip()
    )
    if any(signal in lower for signal in high_signals) or missing_metadata >= 3:
        label = "high"
        confidence = 0.68
        rule = "risk_high_procedural_or_metadata"
    elif any(signal in lower for signal in medium_signals) or missing_metadata:
        label = "medium"
        confidence = 0.58
        rule = "risk_medium_procedural_or_metadata"
    else:
        label = "low"
        confidence = 0.52
        rule = "risk_low_no_major_signal"
    return LabelCandidate(
        task_name=MlTaskName.RISK_SCORING,
        label=label,
        label_source="weak_supervision",
        confidence_score=confidence,
        evidence_text=text[-360:].strip(),
        rule_name=rule,
        needs_review=True,
    )


def _case_type_label(text: str, title: str) -> LabelCandidate:
    haystack = f"{title}\n{text}".casefold()
    for label, phrases in CASE_TYPE_RULES:
        for phrase in phrases:
            if phrase in haystack:
                return LabelCandidate(
                    task_name=MlTaskName.CASE_TYPE,
                    label=label,
                    label_source="weak_supervision",
                    confidence_score=0.72,
                    evidence_text=_window(f"{title}\n{text}", phrase),
                    rule_name=f"case_type_keyword:{phrase}",
                    needs_review=True,
                )
    return LabelCandidate(
        task_name=MlTaskName.CASE_TYPE,
        label="unknown",
        label_source="weak_supervision",
        confidence_score=0.1,
        evidence_text=title,
        rule_name="case_type_unknown",
        needs_review=True,
    )


def extract_label_candidates(document: Tier1Document) -> list[LabelCandidate]:
    text = document.raw_text or document.normalized_text
    metadata = {
        "court": document.court,
        "date": document.date,
        "citation": document.citation,
        "case_number": document.case_number,
    }
    return [
        _outcome_label(text),
        _maintainability_label(text),
        _risk_label(text, metadata),
        _case_type_label(text, document.title),
    ]


def extract_labels_for_document(db: Session, document: Tier1Document) -> int:
    written = 0
    for candidate in extract_label_candidates(document):
        label = db.scalar(
            select(Tier1Label).where(
                Tier1Label.document_id == document.id,
                Tier1Label.task_name == candidate.task_name,
            )
        )
        if label is not None and label.reviewed:
            continue
        if label is None:
            label = Tier1Label(document_id=document.id, task_name=candidate.task_name)
        label.label = candidate.label
        label.label_source = candidate.label_source
        label.confidence_score = candidate.confidence_score
        label.evidence_text = candidate.evidence_text[:1600]
        label.rule_name = candidate.rule_name
        label.needs_review = candidate.needs_review
        db.add(label)
        written += 1
    db.commit()
    return written


def extract_labels_for_documents(db: Session, documents: list[Tier1Document]) -> int:
    return sum(extract_labels_for_document(db, document) for document in documents)
