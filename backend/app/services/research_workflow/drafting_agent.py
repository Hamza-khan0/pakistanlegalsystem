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


def _issue_labels(context: dict[str, Any], memo: dict[str, Any]) -> set[str]:
    labels = {str(item).strip().casefold() for item in _ensure_string_list(memo.get("legal_issues"))}
    labels.update(str(item).strip().casefold() for item in _ensure_string_list(context.get("recorded_issues")))
    text = " ".join(
        [
            str(context.get("combined_text") or ""),
            str(context.get("facts") or ""),
            str(context.get("relief_sought") or ""),
            str(context.get("matter_type") or ""),
            str(memo.get("recommended_draft_type") or ""),
        ]
    ).casefold()
    if "article 199" in text or "constitutional petition" in text or "writ" in text:
        labels.add("constitutional_petition")
    if "notice" in text and "hearing" in text:
        labels.add("natural_justice")
    if "injunction" in text or "stay" in text or "interim relief" in text:
        labels.add("injunction")
    if "property" in text or "allotment" in text or "possession" in text:
        labels.add("property_dispute")
    if "alternate remedy" in text or "alternative remedy" in text:
        labels.add("alternate_remedy")
    return {label for label in labels if label}


def _normalize_requested_draft_type(value: str | None) -> str:
    normalized = str(value or "").strip().casefold().replace(" ", "_").replace("-", "_")
    aliases = {
        "constitutional_petition": "writ_petition",
        "writ": "writ_petition",
        "civil_suit": "plaint",
        "civil_suit_draft": "plaint",
        "injunction": "injunction_application",
        "stay_application": "injunction_application",
        "bail": "bail_application",
        "memo": "research_memo",
    }
    return aliases.get(normalized, normalized)


def _selected_draft_type(context: dict[str, Any], memo: dict[str, Any], draft_type: str | None) -> str:
    requested = _normalize_requested_draft_type(draft_type)
    if requested and requested != "auto":
        return requested if requested in DRAFT_TYPE_LABELS else "research_memo"

    labels = _issue_labels(context, memo)
    text = " ".join(
        [
            str(context.get("combined_text") or ""),
            str(context.get("forum") or ""),
            str(context.get("court") or ""),
            str(context.get("case_title") or ""),
            str(context.get("case_type") or ""),
            str(context.get("opposing_party") or ""),
            str(context.get("relief_sought") or ""),
            str(memo.get("recommended_draft_type") or ""),
        ]
    ).casefold()
    public_authority_terms = (
        "public authority",
        "development authority",
        "defence housing authority",
        "dha",
        "government",
        "department",
        "statutory",
    )
    public_authority_dispute = any(term in text for term in public_authority_terms) and any(
        term in text for term in ("cancellation", "allotment", "impugned", "without notice", "coercive", "transfer")
    )
    if "constitutional_petition" in labels or "article 199" in text or "writ" in text:
        return "writ_petition"
    if public_authority_dispute and ("high court" in text or "injunction" in labels or "stay" in text):
        return "writ_petition"
    if "injunction" in labels and ("property_dispute" in labels or "allotment" in text or "possession" in text):
        return "injunction_application"
    if "criminal_bail" in labels or "bail" in text:
        return "bail_application"
    if "legal notice" in text:
        return "legal_notice"
    if {"contract_breach", "property_dispute"} & labels:
        return "plaint"

    recommended = _normalize_requested_draft_type(str(memo.get("recommended_draft_type") or "research_memo"))
    if recommended and recommended != "research_memo":
        return recommended if recommended in DRAFT_TYPE_LABELS else "research_memo"
    return "research_memo"


def _is_demo_source(source: dict[str, Any]) -> bool:
    joined = " ".join(
        str(source.get(key) or "")
        for key in ("title", "citation", "excerpt", "url", "id")
    ).casefold()
    return "demo" in joined or "fixture" in joined


def _is_irrelevant_web_source(source: dict[str, Any]) -> bool:
    url = str(source.get("url") or "").casefold()
    title = str(source.get("title") or "").casefold()
    irrelevant_markers = ["judge", "profile", "biography", "career", "contact", "cause-list", "cause_list"]
    return any(marker in url or marker in title for marker in irrelevant_markers)


def _usable_authority_sources(sources: list[dict[str, Any]], *, include_demo: bool = False) -> list[dict[str, Any]]:
    usable: list[dict[str, Any]] = []
    for source in sources:
        if not include_demo and _is_demo_source(source):
            continue
        if _is_irrelevant_web_source(source):
            continue
        source_type = str(source.get("source_type") or source.get("sourceType") or "").casefold()
        citation = str(source.get("citation") or "").strip()
        statute = str(source.get("statute") or "").strip()
        section = str(source.get("section") or "").strip()
        title = str(source.get("title") or "").strip()
        confidence = float(source.get("confidence") or 0)
        if source_type == "unknown" and not (citation or statute or section):
            continue
        if source.get("source_origin") == "live_web" and confidence < 0.45 and not (citation or statute or section):
            continue
        if title and (citation or statute or section or "constitution" in source_type or "statute" in source_type or "rules" in source_type or "case" in source_type):
            usable.append(source)
    return usable[:10]


def _source_labels(sources: list[dict[str, Any]]) -> list[str]:
    labels = []
    for source in _usable_authority_sources(sources):
        title = str(source.get("title") or "").strip()
        citation = str(source.get("citation") or "").strip()
        source_id = str(source.get("id") or "").strip()
        if title:
            labels.append(f"{title}{f' ({citation})' if citation else ''}{f' [{source_id}]' if source_id else ''}")
    return labels[:12]


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items()]
    return [value]


def _ensure_string_list(value: Any) -> list[str]:
    cleaned: list[str] = []
    for item in _ensure_list(value):
        text = str(item).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _ensure_sections(value: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(value, list):
        sections = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                sections.append(
                    {
                        "heading": str(item.get("heading") or item.get("title") or f"Section {index}"),
                        "content": str(item.get("content") or item.get("body") or ""),
                    }
                )
            elif str(item).strip():
                sections.append({"heading": f"Section {index}", "content": str(item).strip()})
        return sections or fallback
    if isinstance(value, dict):
        return [
            {"heading": str(key), "content": str(item)}
            for key, item in value.items()
            if str(item).strip()
        ] or fallback
    if value:
        return [{"heading": "Draft", "content": str(value)}]
    return fallback


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
    facts = _ensure_string_list(research_memo.get("factual_basis"))
    authorities = _source_labels(sources)
    issue_labels = _issue_labels(context, research_memo)
    client = context.get("client") or context.get("case_title") or "[TO BE VERIFIED: petitioner/applicant name]"
    opponent = context.get("opposing_party") or "[TO BE VERIFIED: respondent/opposing party]"
    forum = context.get("forum") or "[TO BE VERIFIED: Province/City]"
    case_title = context.get("case_title") or context.get("case_id")
    relief = context.get("relief_sought") or "[TO BE VERIFIED: specific relief sought]"
    fact_text = "\n".join(f"{index}. {fact}" for index, fact in enumerate(facts[:8], start=1)) or (
        "1. [TO BE VERIFIED: factual chronology and supporting documents]."
    )
    authority_text = "\n".join(f"{index}. {item}" for index, item in enumerate(authorities[:8], start=1)) or (
        "1. No filing-ready authority is cited in this draft. Counsel must verify and insert authorities before filing."
    )

    if draft_type == "writ_petition":
        interim = ""
        if "injunction" in issue_labels or "stay" in str(relief).casefold():
            interim = """
## 7. INTERIM RELIEF / STAY

Pending final disposal of this petition, it is respectfully prayed that this Honourable Court may suspend the operation of the impugned action/order and restrain the Respondent(s) from taking coercive or adverse steps affecting the Petitioner's rights, subject to lawyer review and verification of the record.
"""
        draft_markdown = f"""> {LEGAL_RESEARCH_WARNING}

# IN THE HIGH COURT OF {forum}
## CONSTITUTIONAL JURISDICTION

Constitutional Petition No. ____ of 2026

**{client}**<br>
...Petitioner

Versus

**{opponent}**<br>
...Respondent

# CONSTITUTIONAL PETITION UNDER ARTICLE 199 OF THE CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN, 1973

Respectfully Sheweth:

## 1. PARTIES

1. The Petitioner is {client}. The exact legal status, address, authorization, and representative capacity must be verified from the case file.
2. The Respondent is {opponent}. The precise department/authority, address for service, and statutory capacity must be verified before filing.

## 2. BRIEF FACTS

{fact_text}

## 3. CAUSE OF ACTION

The cause of action arose when the Respondent(s), being public/statutory authority or persons performing functions in connection with public affairs, allegedly took or maintained the impugned action affecting the Petitioner without lawful authority and/or without adequate procedural safeguards.

## 4. IMPUGNED ACTION

The impugned action/order/communication is: [TO BE VERIFIED: identify order, date, reference number, authority, and annexure].

## 5. GROUNDS

### A. Action without lawful authority
The impugned action may be assailed as without lawful authority and of no legal effect if the record confirms that the Respondent acted beyond jurisdiction, contrary to statute, or without lawful basis.

### B. Violation of natural justice
The Petitioner may plead that no adequate notice, hearing, or opportunity to respond was provided before adverse action was taken.

### C. Failure to provide notice and hearing
The record should be checked for any show-cause notice, hearing notice, reply, personal hearing, order sheet, or reasons supplied by the Respondent.

### D. Protection of allotment/property rights
Where allotment, possession, payments, title, or property interests are involved, the Petitioner may seek protection against arbitrary cancellation or dispossession, subject to verification of documents.

### E. Maintainability under ARTICLE 199
The petition may be maintainable where the Respondent performs public/statutory functions and where the impugned action is alleged to be without lawful authority, in violation of due process, or otherwise amenable to constitutional review.

### F. Alternate remedy, if any, is not efficacious
If an alternate remedy is asserted, the Petitioner may plead that it is not adequate or efficacious in the circumstances, especially where jurisdictional defect, natural justice, urgency, or irreparable prejudice is involved. Counsel must verify this position against binding authority.

## 6. LEGAL BASIS / AUTHORITIES

{authority_text}

These authorities are included only as retrieved research support. Counsel must verify citations, holdings, current status, and applicability before filing.
{interim}
## 8. PRAYER

In view of the foregoing, it is respectfully prayed that this Honourable Court may be pleased to:

1. Declare that the impugned action/order is without lawful authority and of no legal effect, subject to final lawyer verification of the record;
2. Set aside/suspend the impugned action/order;
3. Direct the Respondent(s) to decide the matter strictly in accordance with law after notice and opportunity of hearing;
4. Grant interim protection/stay against coercive or adverse action where justified by the record;
5. Grant any other relief deemed just and proper in the circumstances.

## 9. ANY OTHER RELIEF

Any other relief that this Honourable Court may deem just and proper may also be granted.

## 10. VERIFICATION

Verified on oath at [TO BE VERIFIED: place] on [TO BE VERIFIED: date] that the contents of this petition are true and correct to the best of the Petitioner's knowledge and belief, and nothing material has been concealed.

Petitioner / Authorized Representative<br>
[TO BE VERIFIED: name, signature, CNIC, authority]

## 11. LAWYER REVIEW CHECKLIST

1. Verify court/forum, territorial jurisdiction, and maintainability.
2. Verify parties, addresses, authority letters, dates, impugned order, and annexures.
3. Verify all citations and authorities before filing.
4. Remove any unsupported allegation or replace it with record-backed pleading.
5. Finalize prayer and interim relief according to the latest instructions and documents.
"""
        headings = [
            "Court heading",
            "Parties",
            "Brief facts",
            "Cause of action",
            "Impugned action",
            "Grounds",
            "Legal basis / authorities",
            "Interim relief",
            "Prayer",
            "Verification",
            "Lawyer review checklist",
        ]
        sections = [{"heading": heading, "content": ""} for heading in headings]
    else:
        sections = []
        for heading in _draft_sections_for_type(draft_type):
            if "parties" in heading.casefold():
                content = (
                    f"Petitioner/Plaintiff/Applicant: {client}.\n\n"
                    f"Respondent/Defendant/Opposing party: {opponent}."
                )
            elif "facts" in heading.casefold() or "synopsis" in heading.casefold():
                content = fact_text
            elif "legal" in heading.casefold() or "grounds" in heading.casefold() or "maintainability" in heading.casefold():
                content = (
                    "The following legal points may be pleaded subject to verification:\n"
                    + "\n".join(f"- {item}" for item in research_memo.get("arguments_for_client", [])[:6])
                )
                if authorities:
                    content += "\n\nAuthorities retrieved for lawyer review:\n" + "\n".join(f"- {item}" for item in authorities[:8])
            elif "prayer" in heading.casefold() or "relief" in heading.casefold() or "demand" in heading.casefold():
                content = (
                    f"Respectfully pray/demand relief consistent with: {relief}.\n"
                    "Any interim or final relief must be tailored by counsel before use."
                )
            elif "verification" in heading.casefold():
                content = "[TO BE VERIFIED: verification clause, date, place, and authorized signatory]."
            else:
                content = (
                    "This section should be finalized after counsel checks the record, retrieved authorities, "
                    "and critic warnings."
                )
            sections.append({"heading": heading, "content": content})
        draft_markdown = f"> {LEGAL_RESEARCH_WARNING}\n\n# {label.upper()} - {case_title}\n\n" + "\n\n".join(
            f"## {section['heading']}\n\n{section['content']}" for section in sections
        )

    return {
        "draft_type": draft_type,
        "title": f"{label} - {case_title}",
        "draft_markdown": draft_markdown,
        "sections": sections,
        "authorities_used": authorities,
        "facts_used": facts[:10],
        "assumptions": [
            "Draft is generated from currently stored case data and retrieved sources only.",
            "Missing client-specific facts are marked for verification.",
        ],
        "missing_information": _ensure_string_list(context.get("missing_context")) + _ensure_string_list(research_memo.get("research_gaps")),
        "lawyer_review_checklist": [
            "Verify forum, parties, case number, dates, addresses, and signing authority.",
            "Check every authority in the retrieved source list before citation.",
            "Remove or revise any point unsupported by the final document bundle.",
            "Verify cited authorities before filing.",
            *critic_report.get("drafting_risks", [])[:5],
        ],
        "legal_authority_warning": LEGAL_RESEARCH_WARNING,
        "_llm_used": False,
    }


def _validate_draft(draft: dict[str, Any], sources: list[dict[str, Any]], fallback: dict[str, Any]) -> dict[str, Any]:
    source_text = json.dumps(_source_labels(sources), ensure_ascii=False).casefold()
    draft["draft_type"] = fallback["draft_type"]
    draft.setdefault("title", fallback["title"])
    draft["sections"] = _ensure_sections(draft.get("sections"), fallback["sections"])
    draft.setdefault("draft_markdown", fallback["draft_markdown"])
    draft["draft_markdown"] = str(draft.get("draft_markdown") or fallback["draft_markdown"])
    draft["authorities_used"] = _ensure_string_list(draft.get("authorities_used"))
    draft["facts_used"] = _ensure_string_list(draft.get("facts_used") or fallback["facts_used"])
    draft["assumptions"] = _ensure_string_list(draft.get("assumptions") or fallback["assumptions"])
    draft["missing_information"] = _ensure_string_list(draft.get("missing_information") or fallback["missing_information"])
    draft["lawyer_review_checklist"] = _ensure_string_list(
        draft.get("lawyer_review_checklist") or fallback["lawyer_review_checklist"]
    )
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
    if draft["draft_type"] == "writ_petition":
        draft_text = str(draft.get("draft_markdown") or "").casefold()
        required_terms = ["in the high court", "constitutional petition", "article 199", "prayer", "verification"]
        if not all(term in draft_text for term in required_terms):
            fallback_copy = dict(fallback)
            fallback_copy["_llm_warning"] = "LLM draft lacked writ-petition filing structure; deterministic writ petition was used."
            return fallback_copy
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
        result = generate_json(
            prompt,
            schema_name="GeneratedLegalDraft",
            temperature=0.18,
            max_output_tokens=4500,
        )
        if not result.get("ok") or not isinstance(result.get("json"), dict):
            raise RuntimeError(str(result.get("error") or "LLM did not return valid draft JSON."))
        draft = result["json"]
        draft = _validate_draft(draft, sources, fallback)
        draft["_llm_used"] = True
        draft["_llm_metadata"] = {
            "provider": result.get("provider"),
            "model": result.get("model"),
            "duration_ms": result.get("duration_ms"),
        }
        return draft
    except Exception as exc:
        fallback["_llm_warning"] = f"LLM draft generation failed; deterministic skeleton used. {type(exc).__name__}"
        return fallback
