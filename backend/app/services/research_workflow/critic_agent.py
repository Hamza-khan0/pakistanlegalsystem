from __future__ import annotations

from typing import Any

from app.schemas.research import LEGAL_RESEARCH_WARNING


OVERCLAIMING_PHRASES = [
    "guaranteed success",
    "definitely maintainable",
    "court will allow",
    "clearly wins",
    "settled beyond doubt",
]


def critic_review_research_memo(
    memo: dict[str, Any],
    sources: list[dict[str, Any]],
    context: dict[str, Any],
    generated_draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    unsupported_claims: list[str] = []
    fake_or_unverified_citations: list[str] = []
    weak_sources: list[str] = []
    missing_authorities: list[str] = []
    overclaiming_warnings: list[str] = []
    drafting_risks: list[str] = []
    drafting_defects: list[str] = []
    required_lawyer_checks: list[str] = []

    if not sources:
        missing_authorities.append("No retrieved legal authority was attached to this research run.")
    if memo.get("relevant_case_law") and not any(
        "case" in str(source.get("source_type") or source.get("sourceType") or "").casefold()
        or "judgment" in str(source.get("source_type") or source.get("sourceType") or "").casefold()
        for source in sources
    ):
        unsupported_claims.append("The memo lists case law, but no case-law source was retrieved.")
    if not memo.get("research_gaps"):
        weak_sources.append("Memo contains no explicit research gaps; lawyer should still verify completeness.")
    if memo.get("legal_authority_warning") != LEGAL_RESEARCH_WARNING:
        unsupported_claims.append("Required legal authority warning is missing or altered.")

    serialized_memo = " ".join(str(value) for value in memo.values()).casefold()
    for phrase in OVERCLAIMING_PHRASES:
        if phrase in serialized_memo:
            overclaiming_warnings.append(f"Overclaiming phrase detected: `{phrase}`.")

    low_confidence_sources = [
        str(source.get("title") or "Untitled source")
        for source in sources
        if source.get("confidence") is not None and float(source.get("confidence") or 0) < 0.35
    ]
    if low_confidence_sources:
        weak_sources.extend(low_confidence_sources[:5])

    if context.get("missing_context"):
        drafting_risks.extend(str(item) for item in context["missing_context"][:5])
    if not memo.get("applicable_statutes") and not memo.get("relevant_case_law"):
        drafting_risks.append("Drafting would rely on inference because no statute or case-law source was retrieved.")

    source_dump = " ".join(
        str(source.get("citation") or source.get("title") or source.get("id") or "")
        for source in sources
    ).casefold()
    if generated_draft:
        draft_text = str(generated_draft.get("draft_markdown") or "").casefold()
        if LEGAL_RESEARCH_WARNING.casefold() not in draft_text:
            drafting_defects.append("Generated draft is missing the required legal warning.")
        if "[to be verified" in draft_text:
            required_lawyer_checks.append("Resolve all [TO BE VERIFIED] placeholders before use.")
        if not generated_draft.get("sections"):
            drafting_defects.append("Generated draft does not contain structured sections.")
        if "prayer" not in draft_text and str(generated_draft.get("draft_type")) in {
            "writ_petition",
            "plaint",
            "injunction_application",
            "bail_application",
        }:
            drafting_defects.append("Draft may be missing a prayer/relief section.")
        for authority in generated_draft.get("authorities_used", []):
            authority_text = str(authority).casefold()
            if authority_text and authority_text not in source_dump:
                fake_or_unverified_citations.append(str(authority))
        for phrase in OVERCLAIMING_PHRASES:
            if phrase in draft_text and f"Overclaiming phrase detected: `{phrase}`." not in overclaiming_warnings:
                overclaiming_warnings.append(f"Overclaiming phrase detected: `{phrase}`.")

    severity = "low"
    if unsupported_claims or fake_or_unverified_citations or overclaiming_warnings:
        severity = "high"
    elif missing_authorities or weak_sources or drafting_defects or drafting_risks:
        severity = "medium"

    passed = severity == "low" and bool(sources)
    recommendation = (
        "Research memo can support drafting, subject to lawyer review and verification of cited authorities."
        if passed
        else "Proceed with caution. Resolve the listed source and drafting risks before treating this as filing-ready."
    )
    return {
        "passed": passed,
        "severity": severity,
        "unsupported_claims": unsupported_claims,
        "fake_or_unverified_citations": fake_or_unverified_citations,
        "weak_sources": weak_sources,
        "missing_authorities": missing_authorities,
        "drafting_defects": drafting_defects,
        "overclaiming_warnings": overclaiming_warnings,
        "drafting_risks": drafting_risks,
        "required_lawyer_checks": required_lawyer_checks,
        "recommendation": recommendation,
    }
