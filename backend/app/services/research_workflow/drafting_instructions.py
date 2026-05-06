from __future__ import annotations

from typing import Any


def _draft_type(context: dict[str, Any], issue_labels: list[str], requested: str | None) -> str:
    if requested and requested != "auto":
        return requested
    text = str(context.get("combined_text") or "").casefold()
    if "constitutional_petition" in issue_labels or "article 199" in text or "writ" in text:
        return "writ_petition"
    if "injunction" in issue_labels:
        return "injunction_application"
    if "criminal_bail" in issue_labels or "bail" in text:
        return "bail_application"
    if {"property_dispute", "contract_breach"} & set(issue_labels):
        return "civil_suit_draft"
    if "legal notice" in text:
        return "legal_notice"
    return "research_memo"


def build_drafting_instructions(
    context: dict[str, Any],
    memo: dict[str, Any],
    critic_report: dict[str, Any],
    draft_type: str | None,
) -> dict[str, Any]:
    issue_labels = [str(issue) for issue in memo.get("legal_issues", [])]
    selected = _draft_type(context, issue_labels, draft_type)
    authorities = []
    for source in memo.get("source_list", []):
        title = source.get("title")
        citation = source.get("citation")
        if title:
            authorities.append(f"{title}{f' ({citation})' if citation else ''}")

    return {
        "recommended_draft_type": memo.get("recommended_draft_type") or selected,
        "selected_draft_type": selected,
        "client_position": (
            f"Prepare from the position of {context.get('client') or 'the client'}, "
            "subject to lawyer review of facts, forum, and authorities."
        ),
        "core_issues_to_plead": issue_labels,
        "facts_to_highlight": memo.get("factual_basis", [])[:8],
        "legal_bases_to_use": memo.get("applicable_statutes", []),
        "authorities_to_cite": authorities,
        "risks_to_address": critic_report.get("drafting_risks", []) + memo.get("research_gaps", []),
        "missing_information_needed": context.get("missing_context", []),
        "drafting_cautions": critic_report.get("overclaiming_warnings", [])
        + critic_report.get("unsupported_claims", [])
        + ["Do not cite any authority that is not verified in the retrieved source list."],
    }
