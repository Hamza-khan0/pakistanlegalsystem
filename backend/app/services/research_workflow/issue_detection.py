from __future__ import annotations

from typing import Any

from app.services.research_query_hints import detect_legal_issues_for_research


ISSUE_PRIORITY = {
    "constitutional_petition": 10,
    "maintainability": 9,
    "alternate_remedy": 9,
    "natural_justice": 8,
    "jurisdiction": 8,
    "injunction": 7,
    "limitation": 7,
    "property_dispute": 6,
    "criminal_bail": 6,
    "service_matter": 6,
    "family_matter": 5,
    "tax_customs": 5,
    "evidence_issue": 5,
    "contract_breach": 4,
    "pre_emption": 4,
    "execution": 4,
}


def _issue_from_item(item: Any, *, source: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    label = str(item.get("label") or "").strip()
    if not label:
        return None
    probability = item.get("probability")
    try:
        probability_value = float(probability) if probability is not None else None
    except (TypeError, ValueError):
        probability_value = None
    return {
        "label": label,
        "probability": probability_value,
        "source": source,
        "explanation": f"Detected by {source.replace('_', ' ')}.",
    }


def detect_research_issues(context: dict[str, Any], focus_issues: list[str] | None = None) -> list[dict[str, Any]]:
    text = str(context.get("combined_text") or "")
    try:
        detected = detect_legal_issues_for_research(text)
    except Exception:
        detected = {}
    issues_by_label: dict[str, dict[str, Any]] = {}

    model_source = str(detected.get("modelSource") or detected.get("model_source") or "legal_issue_classifier")
    for item in detected.get("selectedIssues", []) or detected.get("selected_issues", []):
        issue = _issue_from_item(item, source=model_source)
        if issue:
            issues_by_label[issue["label"]] = issue

    for item in detected.get("topIssues", []) or detected.get("top_issues", []):
        issue = _issue_from_item(item, source=model_source)
        if issue and issue["label"] not in issues_by_label:
            issues_by_label[issue["label"]] = issue

    for recorded_issue in context.get("recorded_issues", []) or []:
        label = str(recorded_issue).strip().lower().replace(" ", "_")
        if label and label not in issues_by_label:
            issues_by_label[label] = {
                "label": label,
                "probability": None,
                "source": "case_metadata",
                "explanation": "Recorded on the case profile.",
            }

    for focus_issue in focus_issues or []:
        label = str(focus_issue).strip().lower().replace(" ", "_")
        if label:
            issues_by_label[label] = {
                "label": label,
                "probability": 1.0,
                "source": "user_focus",
                "explanation": "Provided as a user focus issue for this run.",
            }

    return sorted(
        issues_by_label.values(),
        key=lambda item: (
            1 if item.get("source") == "user_focus" else 0,
            ISSUE_PRIORITY.get(str(item.get("label")), 0),
            float(item.get("probability") or 0),
        ),
        reverse=True,
    )[:16]
