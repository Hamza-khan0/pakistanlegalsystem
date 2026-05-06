from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.schemas.research import LEGAL_RESEARCH_WARNING
from app.services.llm.provider import generate_json, is_llm_available


DRAFT_TYPE_LABELS = {
    "research_memo": "Research Memo",
    "legal_notice": "Legal Notice",
    "plaint": "Plaint",
    "written_statement": "Written Statement",
    "writ_petition": "Writ Petition",
    "injunction_application": "Injunction Application",
    "bail_application": "Bail Application",
    "civil_application": "Civil Application",
    "hearing_note": "Hearing Note",
}


def _selected_draft_type(context: dict[str, Any], memo: dict[str, Any], draft_type: str | None) -> str:
    if draft_type and draft_type != "auto":
        return draft_type
    recommended = str(memo.get("recommended_draft_type") or "research_memo")
    return recommended if recommended in DRAFT_TYPE_LABELS else "research_memo"


def _source_labels(sources: list[dict[str, Any]]) -> list[str]:
    labels = []
    for source in sources:
        title = str(source.get("title") or "").strip()
        citation = str(source.get("citation") or "").strip()
        source_id = str(source.get("id") or "").strip()
        if title:
            labels.append(f"{title}{f' ({citation})' if citation else ''}{f' [{source_id}]' if source_id else ''}")
    return labels[:12]


def _draft_sections_for_type(draft_type: str) -> list[str]:
    mapping = {
        "writ_petition": [
            "In the High Court of appropriate jurisdiction",
            "Constitutional jurisdiction",
            "Parties",
            "Synopsis / brief facts",
            "Grounds",
            "Legal basis",
            "Maintainability",
            "Prayer",
            "Interim relief",
            "Verification",
        ],
        "plaint": [
            "Court heading",
            "Parties",
            "Facts",
            "Cause of action",
            "Jurisdiction",
            "Valuation and court fee",
            "Legal grounds",
            "Relief",
            "Verification",
        ],
        "injunction_application": [
            "Case heading",
            "Application under Order XXXIX Rules 1 and 2 CPC",
            "Facts",
            "Prima facie case",
            "Balance of convenience",
            "Irreparable loss",
            "Prayer",
        ],
        "bail_application": [
            "Court heading",
            "FIR and offence details",
            "Facts",
            "Grounds for bail",
            "Section 497 CrPC considerations",
            "Prayer",
        ],
        "legal_notice": [
            "To",
            "Subject",
            "Facts",
            "Legal position",
            "Demand",
            "Time for compliance",
            "Consequences",
            "Without prejudice clause",
        ],
        "written_statement": [
            "Preliminary objections",
            "Para-wise reply",
            "Legal objections",
            "Prayer",
        ],
        "hearing_note": [
            "Bench-facing issue list",
            "Facts to open with",
            "Authorities to mention",
            "Likely questions",
            "Concessions and cautions",
        ],
    }
    return mapping.get(draft_type, ["Matter overview", "Issues", "Research position", "Drafting note", "Lawyer checklist"])


def _deterministic_draft(
    context: dict[str, Any],
    research_memo: dict[str, Any],
    critic_report: dict[str, Any],
    draft_type: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    label = DRAFT_TYPE_LABELS.get(draft_type, "Research Memo")
    facts = research_memo.get("factual_basis", [])
    issues = research_memo.get("legal_issues", [])
    authorities = _source_labels(sources)
    sections = []
    for heading in _draft_sections_for_type(draft_type):
        if "parties" in heading.casefold():
            content = (
                f"Petitioner/Plaintiff/Applicant: {context.get('client') or '[TO BE VERIFIED: client name]'}.\n\n"
                f"Respondent/Defendant/Opposing party: {context.get('opposing_party') or '[TO BE VERIFIED: opposing party]'}."
            )
        elif "facts" in heading.casefold() or "synopsis" in heading.casefold():
            content = "\n".join(f"- {fact}" for fact in facts[:8]) or "[TO BE VERIFIED: factual chronology and supporting documents]."
        elif "legal" in heading.casefold() or "grounds" in heading.casefold() or "maintainability" in heading.casefold():
            content = (
                "The following legal points may be pleaded subject to verification:\n"
                + "\n".join(f"- {item}" for item in research_memo.get("arguments_for_client", [])[:6])
            )
            if authorities:
                content += "\n\nAuthorities retrieved for lawyer review:\n" + "\n".join(f"- {item}" for item in authorities[:8])
        elif "prayer" in heading.casefold() or "relief" in heading.casefold():
            content = (
                f"Respectfully pray for relief consistent with: {context.get('relief_sought') or '[TO BE VERIFIED: relief sought]'}.\n"
                "Any interim or final relief must be tailored by counsel before filing."
            )
        elif "verification" in heading.casefold():
            content = "[TO BE VERIFIED: verification clause, date, place, and authorized signatory]."
        else:
            content = (
                "This section should be finalized after counsel checks the record, retrieved authorities, "
                "and critic warnings."
            )
        sections.append({"heading": heading, "content": content})

    draft_markdown = "\n\n".join(f"## {section['heading']}\n\n{section['content']}" for section in sections)
    return {
        "draft_type": draft_type,
        "title": f"{label} - {context.get('case_title') or context.get('case_id')}",
        "draft_markdown": f"> {LEGAL_RESEARCH_WARNING}\n\n{draft_markdown}",
        "sections": sections,
        "authorities_used": authorities,
        "facts_used": facts[:10],
        "assumptions": [
            "Draft is generated from currently stored case data and retrieved sources only.",
            "Missing client-specific facts are marked for verification.",
        ],
        "missing_information": list(context.get("missing_context", [])) + research_memo.get("research_gaps", []),
        "lawyer_review_checklist": [
            "Verify forum, parties, case number, dates, addresses, and signing authority.",
            "Check every authority in the retrieved source list before citation.",
            "Remove or revise any point unsupported by the final document bundle.",
            *critic_report.get("drafting_risks", [])[:5],
        ],
        "legal_authority_warning": LEGAL_RESEARCH_WARNING,
        "_llm_used": False,
    }


def _validate_draft(draft: dict[str, Any], sources: list[dict[str, Any]], fallback: dict[str, Any]) -> dict[str, Any]:
    source_text = json.dumps(_source_labels(sources), ensure_ascii=False).casefold()
    draft.setdefault("draft_type", fallback["draft_type"])
    draft.setdefault("title", fallback["title"])
    draft.setdefault("sections", fallback["sections"])
    draft.setdefault("draft_markdown", fallback["draft_markdown"])
    draft.setdefault("authorities_used", [])
    draft.setdefault("facts_used", fallback["facts_used"])
    draft.setdefault("assumptions", fallback["assumptions"])
    draft.setdefault("missing_information", fallback["missing_information"])
    draft.setdefault("lawyer_review_checklist", fallback["lawyer_review_checklist"])
    draft["legal_authority_warning"] = LEGAL_RESEARCH_WARNING
    filtered_authorities = []
    for authority in draft.get("authorities_used", []):
        text = str(authority)
        if text.casefold() in source_text or any(part and part.casefold() in source_text for part in text.split(" [")[:1]):
            filtered_authorities.append(text)
    draft["authorities_used"] = filtered_authorities
    if not filtered_authorities and sources:
        draft["lawyer_review_checklist"].append(
            "LLM did not return verifiable authority labels; use the retrieved source list before finalizing citations."
        )
    if LEGAL_RESEARCH_WARNING not in str(draft.get("draft_markdown", "")):
        draft["draft_markdown"] = f"> {LEGAL_RESEARCH_WARNING}\n\n{draft.get('draft_markdown', '')}"
    return draft


def generate_full_legal_draft(
    context: dict[str, Any],
    research_memo: dict[str, Any],
    critic_report: dict[str, Any],
    draft_type: str | None,
    sources: list[dict[str, Any]],
    *,
    use_llm: bool = True,
) -> dict[str, Any]:
    selected = _selected_draft_type(context, research_memo, draft_type)
    fallback = _deterministic_draft(context, research_memo, critic_report, selected, sources)
    if not use_llm or not settings.llm_drafting_enabled or not is_llm_available():
        fallback["_llm_warning"] = "LLM unavailable or disabled; deterministic draft skeleton was used."
        return fallback

    prompt = f"""
You are a Pakistani legal drafting assistant.

Rules:
- Draft in formal Pakistani legal style.
- Use only the supplied research memo and retrieved sources.
- Do not invent cases, statutes, citations, courts, dates, FIR numbers, property numbers, addresses, CNICs, or facts.
- Mark missing client-specific facts as [TO BE VERIFIED: ...].
- Authorities must come only from the source list.
- Use cautious language: may support, may be argued, subject to authority, requires lawyer review.
- Include this warning exactly: {LEGAL_RESEARCH_WARNING}
- Output valid JSON only.

Draft type: {selected}
Case context:
{json.dumps(context, ensure_ascii=False)[:12000]}

Research memo:
{json.dumps(research_memo, ensure_ascii=False)[:18000]}

Critic report:
{json.dumps(critic_report, ensure_ascii=False)}

Retrieved sources:
{json.dumps(_source_labels(sources), ensure_ascii=False)}

Required JSON keys:
draft_type, title, draft_markdown, sections, authorities_used, facts_used,
assumptions, missing_information, lawyer_review_checklist, legal_authority_warning.
"""
    try:
        draft = generate_json(prompt, "GeneratedLegalDraft", temperature=0.18)
        draft = _validate_draft(draft, sources, fallback)
        draft["_llm_used"] = True
        return draft
    except Exception as exc:
        fallback["_llm_warning"] = f"LLM draft generation failed; deterministic skeleton used. {type(exc).__name__}"
        return fallback
