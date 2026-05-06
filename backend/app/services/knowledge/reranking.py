from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import ChamberTaskType
from app.services.corpus.normalization import unique_tokens
from app.services.knowledge.retrieval import RetrievedLegalSource


@dataclass(slots=True)
class RerankResult:
    final_score: float
    bonus_score: float
    components: dict[str, float]
    explanation: str


def reranker_metadata() -> dict[str, object]:
    return {
        "mode": "heuristic_legal_reranker",
        "crossEncoderReady": True,
        "supportedSignals": [
            "lexical_score",
            "semantic_score",
            "task_type",
            "source_type",
            "language_match",
            "citation_match",
            "section_match",
            "source_quality",
        ],
    }


def score_retrieval_candidate(
    *,
    query: str,
    task_type: ChamberTaskType,
    source: RetrievedLegalSource,
    lexical_weight: float,
    semantic_weight: float,
    language_hint: str | None = None,
) -> RerankResult:
    lexical_score = float(source.lexical_score or 0.0)
    semantic_score = float(source.semantic_score or 0.0)
    base_score = (lexical_score * lexical_weight) + (semantic_score * semantic_weight)
    query_lower = query.casefold()
    query_terms = set(unique_tokens(query))
    title_terms = set(unique_tokens(f"{source.title} {source.citation_label} {source.section_label}"))

    components: dict[str, float] = {
        "baseLexical": round(lexical_score * lexical_weight, 4),
        "baseSemantic": round(semantic_score * semantic_weight, 4),
    }

    if (
        task_type in {ChamberTaskType.PRELIMINARY_OBJECTIONS, ChamberTaskType.PROCEDURAL_CHECK}
        and source.source_type in {"Statute", "Rules", "Constitution"}
    ):
        components["proceduralSourceBoost"] = 0.2
    elif task_type in {ChamberTaskType.RESEARCH_MEMO, ChamberTaskType.ISSUE_SPOTTING} and source.source_type == "Case Law":
        components["researchSourceBoost"] = 0.15

    if source.section_label and source.section_label.casefold() in query_lower:
        components["sectionMatch"] = 0.08
    if source.citation_label and source.citation_label.casefold() in query_lower:
        components["citationMatch"] = 0.08
    if query_terms and query_terms & title_terms:
        components["titleOverlap"] = 0.05
    if language_hint and source.language in {language_hint, "Mixed"}:
        components["languageMatch"] = 0.05
    if source.citation_label:
        components["sourceQuality"] = 0.02

    bonus_score = round(sum(value for key, value in components.items() if key not in {"baseLexical", "baseSemantic"}), 4)
    final_score = round(base_score + bonus_score, 4)
    explanation = (
        f"Hybrid fusion lexical {lexical_weight:.2f} / semantic {semantic_weight:.2f}; "
        f"reranker added {bonus_score:.2f} through {', '.join(key for key in components if key not in {'baseLexical', 'baseSemantic'}) or 'no extra legal boosts'}."
    )
    return RerankResult(
        final_score=final_score,
        bonus_score=bonus_score,
        components=components,
        explanation=explanation,
    )
