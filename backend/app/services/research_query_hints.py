from __future__ import annotations

from typing import Any

from app.services.ml.training.imported_legal_issue import predict_legal_issues

ISSUE_QUERY_HINTS: dict[str, list[str]] = {
    "constitutional_petition": [
        "Article 199 maintainability Pakistan",
        "writ petition public authority Pakistan",
    ],
    "alternate_remedy": [
        "alternate remedy writ petition Pakistan Supreme Court",
        "constitutional petition alternative efficacious remedy Pakistan",
    ],
    "natural_justice": [
        "natural justice opportunity of hearing Pakistan Supreme Court",
        "administrative order without notice Pakistan",
    ],
    "injunction": [
        "temporary injunction prima facie case balance of convenience Pakistan",
        "Order XXXIX CPC injunction Pakistan",
    ],
    "limitation": [
        "Limitation Act delay laches Pakistan civil suit",
        "time barred suit Pakistan limitation",
    ],
    "property_dispute": [
        "property allotment cancellation Pakistan case law",
        "specific performance property agreement Pakistan",
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
}


def detect_legal_issues_for_research(text: str) -> dict[str, Any]:
    try:
        result = predict_legal_issues(text, top_k=10, include_probabilities=False, include_metadata=True)
    except Exception:
        result = predict_legal_issues("", top_k=10, include_probabilities=False, include_metadata=True)
    issues = [item["label"] for item in result.get("selected_issues", []) if isinstance(item, dict)]
    if not issues:
        issues = [
            item["label"]
            for item in result.get("top_issues", [])[:3]
            if isinstance(item, dict) and isinstance(item.get("label"), str)
        ]
    return {
        "selectedIssues": result.get("selected_issues", []),
        "topIssues": result.get("top_issues", []),
        "modelSource": result.get("model_source", "demo_fallback"),
        "modelStatus": result.get("model_status", "demo_fallback"),
        "queryHints": build_research_query_hints_from_issues(issues, text),
        "legalAuthorityWarning": result.get("legal_authority_warning", ""),
    }


def build_research_query_hints_from_issues(issues: list[str], case_text: str | None = None) -> list[str]:
    hints: list[str] = []
    for issue in issues:
        for hint in ISSUE_QUERY_HINTS.get(issue, []):
            if hint not in hints:
                hints.append(hint)
    if case_text:
        normalized = case_text.lower()
        if "article 199" in normalized and "Article 199 maintainability Pakistan" not in hints:
            hints.append("Article 199 maintainability Pakistan")
        if "notice" in normalized and "natural justice opportunity of hearing Pakistan Supreme Court" not in hints:
            hints.append("natural justice opportunity of hearing Pakistan Supreme Court")
    return hints[:12]
