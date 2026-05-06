from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.schemas.research import LEGAL_RESEARCH_WARNING
from app.services.llm.provider import generate_json, is_llm_available


ISSUE_ARGUMENTS_FOR = {
    "constitutional_petition": "Article 199 or writ-related facts may support supervisory constitutional jurisdiction where public authority action is challenged.",
    "natural_justice": "Absence of notice or opportunity of hearing may support a natural justice challenge, depending on the authority and supplied record.",
    "injunction": "Interim protection may be argued through prima facie case, balance of convenience, and irreparable loss if the facts and sources support those elements.",
    "property_dispute": "Possession, title, allotment, transfer, or specific performance facts may support civil/property relief if matched with documents and authority.",
    "criminal_bail": "Bail arguments may turn on FIR allegations, role, delay, recovery, further inquiry, and statutory grounds under Pakistani criminal procedure.",
    "alternate_remedy": "Recognized exceptions may be argued where the alternate remedy is not efficacious or where jurisdiction/natural justice issues are present.",
}

ISSUE_ARGUMENTS_AGAINST = {
    "alternate_remedy": "Maintainability may be challenged where an efficacious alternate statutory remedy exists, subject to recognized exceptions.",
    "maintainability": "The opposing side may raise preliminary objections on forum, locus, limitation, alternate remedy, or statutory bar.",
    "limitation": "Delay, laches, or a statutory limitation bar may weaken the matter unless explained by facts and law.",
    "jurisdiction": "Forum or subject-matter jurisdiction should be verified before drafting relief.",
    "natural_justice": "Natural justice arguments may weaken if prior notice, appeal, or hearing opportunity appears in the record.",
}


def _clean_list(values: list[Any]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _source_reference(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source.get("id"),
        "title": source.get("title"),
        "sourceType": source.get("source_type") or source.get("sourceType"),
        "citation": source.get("citation"),
        "statute": source.get("statute"),
        "section": source.get("section"),
        "excerpt": source.get("excerpt"),
        "relevanceScore": source.get("relevance_score") or source.get("relevanceScore"),
        "retrievalMethod": source.get("retrieval_method") or source.get("retrievalMethod"),
    }


def _recommended_draft_type(issue_labels: list[str], context: dict[str, Any]) -> str:
    text = str(context.get("combined_text") or "").casefold()
    if "constitutional_petition" in issue_labels or "article 199" in text or "writ" in text:
        return "writ_petition"
    if "injunction" in issue_labels:
        return "injunction_application"
    if "criminal_bail" in issue_labels or "bail" in text:
        return "bail_application"
    if {"contract_breach", "property_dispute"} & set(issue_labels):
        return "civil_suit_draft"
    if "legal notice" in text:
        return "legal_notice"
    return "research_memo"


def generate_structured_research_memo(
    context: dict[str, Any],
    issues: list[dict[str, Any]],
    query_plan: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    issue_labels = [str(issue.get("label")) for issue in issues if issue.get("label")]
    factual_basis = _clean_list(
        [
            f"Case: {context.get('case_title')}",
            f"Forum/stage: {context.get('forum') or 'Not recorded'} / {context.get('stage') or 'Not recorded'}",
            f"Client/opponent: {context.get('client') or 'Not recorded'} v. {context.get('opposing_party') or 'Not recorded'}",
            str(context.get("facts") or "").strip(),
            f"Relief sought: {context.get('relief_sought') or 'Not recorded'}",
        ]
    )

    source_refs = [_source_reference(source) for source in sources]
    statutes = [
        ref
        for ref in source_refs
        if str(ref.get("sourceType") or "").casefold() in {"constitution", "statute", "rules", "manual"}
        or ref.get("statute")
        or ref.get("section")
    ]
    case_law = [
        ref
        for ref in source_refs
        if "case" in str(ref.get("sourceType") or "").casefold()
        or "judgment" in str(ref.get("sourceType") or "").casefold()
    ]

    arguments_for = [
        ISSUE_ARGUMENTS_FOR[label]
        for label in issue_labels
        if label in ISSUE_ARGUMENTS_FOR
    ]
    arguments_against = [
        ISSUE_ARGUMENTS_AGAINST[label]
        for label in issue_labels
        if label in ISSUE_ARGUMENTS_AGAINST
    ]
    if not arguments_for:
        arguments_for.append(
            "The available case facts may support focused legal submissions, but the exact strength depends on verified documents and authorities."
        )
    if not arguments_against:
        arguments_against.append(
            "The opposing side may challenge factual sufficiency, maintainability, or lack of directly applicable authority."
        )

    research_gaps = list(context.get("missing_context") or [])
    if not sources:
        research_gaps.append("No Pakistani legal sources were retrieved for the generated query plan.")
    if not case_law:
        research_gaps.append("No case-law source was retrieved; counsel should verify authorities before filing.")
    if query_plan and len(sources) < min(3, len(query_plan)):
        research_gaps.append("Retrieved source count is low compared with the query plan.")

    recommended = _recommended_draft_type(issue_labels, context)
    drafting_instructions = [
        "Use only verified sources from the source list as authorities.",
        "Separate factual assertions from legal submissions.",
        "Address maintainability and procedural objections before merits where they appear.",
        "Include research gaps as items for lawyer review rather than treating them as resolved.",
    ]
    if recommended == "writ_petition":
        drafting_instructions.append("Frame public authority action, jurisdiction, alternate remedy, and natural justice exceptions carefully.")
    elif recommended == "injunction_application":
        drafting_instructions.append("Plead prima facie case, balance of convenience, and irreparable loss with document references.")
    elif recommended == "bail_application":
        drafting_instructions.append("Tie bail grounds to FIR role, recovery, further inquiry, delay, and statutory considerations.")

    return {
        "factual_basis": factual_basis,
        "legal_issues": issue_labels,
        "applicable_statutes": statutes,
        "relevant_case_law": case_law,
        "procedural_position": _clean_list(
            [
                f"The matter is currently at: {context.get('stage') or 'not recorded'}.",
                f"The forum is: {context.get('forum') or 'not recorded'}.",
                "Procedural posture should be verified against the latest order sheet and filing record.",
            ]
        ),
        "arguments_for_client": _clean_list(arguments_for),
        "arguments_against_client": _clean_list(arguments_against),
        "research_gaps": _clean_list(research_gaps),
        "recommended_draft_type": recommended,
        "drafting_instructions": drafting_instructions,
        "source_list": source_refs,
        "legal_authority_warning": LEGAL_RESEARCH_WARNING,
    }


def _compact_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": context.get("case_id"),
        "case_title": context.get("case_title"),
        "forum": context.get("forum"),
        "stage": context.get("stage"),
        "client": context.get("client"),
        "opposing_party": context.get("opposing_party"),
        "facts": str(context.get("facts") or "")[:5000],
        "relief_sought": context.get("relief_sought"),
        "missing_context": context.get("missing_context", []),
    }


def _compact_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for index, source in enumerate(sources, start=1):
        source_id = str(source.get("id") or f"source-{index}")
        compact.append(
            {
                "source_id": source_id,
                "title": source.get("title"),
                "source_origin": source.get("source_origin"),
                "source_type": source.get("source_type"),
                "citation": source.get("citation"),
                "statute": source.get("statute"),
                "section": source.get("section"),
                "court": source.get("court"),
                "url": source.get("url"),
                "excerpt": str(source.get("excerpt") or "")[:1200],
            }
        )
    return compact


def _validate_llm_memo(memo: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    source_ids = {
        str(source.get("id") or f"source-{index}")
        for index, source in enumerate(sources, start=1)
    }
    source_titles = {str(source.get("title") or "") for source in sources}
    memo["legal_authority_warning"] = LEGAL_RESEARCH_WARNING
    memo.setdefault("factual_basis", [])
    memo.setdefault("legal_issues", [])
    memo.setdefault("applicable_statutes", [])
    memo.setdefault("relevant_case_law", [])
    memo.setdefault("procedural_position", [])
    memo.setdefault("arguments_for_client", [])
    memo.setdefault("arguments_against_client", [])
    memo.setdefault("research_gaps", [])
    memo.setdefault("recommended_draft_type", "research_memo")
    memo.setdefault("drafting_instructions", [])
    memo["source_list"] = _compact_sources(sources)

    valid_case_law = []
    for item in memo.get("relevant_case_law", []):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source_id") or "")
        title = str(item.get("case_name_or_title") or item.get("title") or "")
        if source_id in source_ids or title in source_titles:
            valid_case_law.append(item)
        else:
            memo["research_gaps"].append(
                f"LLM mentioned `{title or 'an authority'}` without a matching retrieved source; it was excluded from cited case law."
            )
    memo["relevant_case_law"] = valid_case_law
    return memo


def generate_llm_structured_research_memo(
    context: dict[str, Any],
    issues: list[dict[str, Any]],
    query_plan: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    fallback = generate_structured_research_memo(context, issues, query_plan, sources)
    if not settings.llm_drafting_enabled or not is_llm_available():
        fallback["_llm_used"] = False
        fallback["_llm_warning"] = "LLM unavailable or disabled; deterministic research memo was used."
        return fallback

    prompt = f"""
You are a Pakistani legal research assistant.

Rules:
- Use only the supplied sources as authorities.
- Do not invent cases, statutes, citations, courts, dates, or holdings.
- Do not cite a case unless it appears in the supplied sources.
- If a source has no citation, refer to it by title/source_id and mark citation unavailable.
- If authority is missing, write "Research gap".
- Separate facts, retrieved law, inference, and gaps.
- Use cautious language.
- Output valid JSON only.

Required JSON keys:
factual_basis, legal_issues, applicable_statutes, relevant_case_law,
procedural_position, arguments_for_client, arguments_against_client,
research_gaps, recommended_draft_type, drafting_instructions, source_list,
legal_authority_warning.

Case context:
{json.dumps(_compact_context(context), ensure_ascii=False)}

Detected issues:
{json.dumps(issues, ensure_ascii=False)}

Research query plan:
{json.dumps(query_plan, ensure_ascii=False)}

Retrieved sources:
{json.dumps(_compact_sources(sources), ensure_ascii=False)}

Legal warning:
{LEGAL_RESEARCH_WARNING}
"""
    try:
        memo = generate_json(prompt, "StructuredResearchMemo", temperature=0.15)
        memo = _validate_llm_memo(memo, sources)
        memo["_llm_used"] = True
        return memo
    except Exception as exc:
        fallback["_llm_used"] = False
        fallback["_llm_warning"] = f"LLM research memo failed; deterministic fallback used. {type(exc).__name__}"
        return fallback
