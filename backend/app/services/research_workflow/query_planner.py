from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from app.services.research_query_hints import build_research_query_hints_from_issues


ISSUE_QUERY_TEMPLATES: dict[str, list[str]] = {
    "constitutional_petition": [
        "Article 199 maintainability Pakistan Supreme Court",
        "writ petition public authority Pakistan",
    ],
    "alternate_remedy": [
        "Article 199 alternate remedy Pakistan Supreme Court",
        "writ petition maintainability alternate efficacious remedy Pakistan",
    ],
    "natural_justice": [
        "natural justice opportunity of hearing Pakistan Supreme Court",
        "administrative order without notice Pakistan",
    ],
    "injunction": [
        "Order XXXIX CPC temporary injunction prima facie case balance of convenience Pakistan",
        "temporary injunction property dispute Pakistan",
    ],
    "property_dispute": [
        "cancellation of allotment property rights Pakistan Supreme Court",
        "specific performance property agreement Pakistan",
    ],
    "limitation": [
        "Limitation Act time barred civil suit Pakistan",
        "delay laches constitutional petition Pakistan",
    ],
    "jurisdiction": [
        "jurisdiction objection civil court Pakistan",
        "coram non judice jurisdiction Pakistan case law",
    ],
    "criminal_bail": [
        "section 497 CrPC bail Pakistan Supreme Court",
        "post arrest bail grounds Pakistan",
    ],
    "service_matter": [
        "service tribunal jurisdiction Pakistan",
        "dismissal from service departmental appeal Pakistan",
    ],
    "family_matter": [
        "family court maintenance custody Pakistan",
        "khula maintenance guardian Pakistan",
    ],
    "tax_customs": [
        "customs seizure jurisdiction Pakistan",
        "FBR customs duty tax appeal Pakistan",
    ],
}


def _similar(left: str, right: str) -> bool:
    if left.casefold() == right.casefold():
        return True
    return SequenceMatcher(None, left.casefold(), right.casefold()).ratio() >= 0.86


def _add_query(
    queries: list[dict[str, Any]],
    *,
    query: str,
    issue: str | None,
    priority: int,
    source: str,
    rationale: str,
) -> None:
    normalized = " ".join(query.split())
    if not normalized:
        return
    if any(_similar(normalized, item["query"]) for item in queries):
        return
    queries.append(
        {
            "query": normalized,
            "issue": issue,
            "priority": priority,
            "source": source,
            "rationale": rationale,
        }
    )


def build_legal_research_query_plan(context: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    issue_labels = [str(issue.get("label")) for issue in issues if issue.get("label")]
    context_text = str(context.get("combined_text") or "")

    for issue in issues:
        label = str(issue.get("label") or "")
        priority = 1 if issue.get("source") == "user_focus" else 2
        for template in ISSUE_QUERY_TEMPLATES.get(label, []):
            _add_query(
                queries,
                query=template,
                issue=label,
                priority=priority,
                source=str(issue.get("source") or "issue_classifier"),
                rationale=f"Research required for detected issue `{label}`.",
            )

    for hint in build_research_query_hints_from_issues(issue_labels, context_text):
        matched_issue = next((label for label in issue_labels if label.replace("_", " ") in hint.casefold()), None)
        _add_query(
            queries,
            query=hint,
            issue=matched_issue,
            priority=3,
            source="issue_classifier",
            rationale="Generated from legal issue classifier query hints.",
        )

    forum = str(context.get("forum") or "").strip()
    matter_type = str(context.get("matter_type") or "").strip()
    relief = str(context.get("relief_sought") or "").strip()
    if forum or matter_type:
        _add_query(
            queries,
            query=f"{matter_type} {forum} maintainability procedural law Pakistan",
            issue=None,
            priority=4,
            source="case_context",
            rationale="Forum and matter-type query to catch procedural authorities.",
        )
    if relief:
        _add_query(
            queries,
            query=f"{relief} Pakistan legal requirements",
            issue=None,
            priority=5,
            source="case_context",
            rationale="Relief-specific query to support drafting posture.",
        )
    for statute in context.get("linked_statutes", [])[:4]:
        _add_query(
            queries,
            query=f"{statute} Pakistan case law",
            issue=None,
            priority=4,
            source="case_context",
            rationale="Linked statute on case profile.",
        )

    return sorted(queries, key=lambda item: (item["priority"], item["query"]))[:20]
