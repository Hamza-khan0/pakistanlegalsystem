from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.models.case import Case  # noqa: E402
from app.schemas.research import LEGAL_RESEARCH_WARNING, ResearchWorkflowRequest  # noqa: E402
from app.services.llm.provider import get_llm_health  # noqa: E402
from app.services.research_workflow.live_web_search import get_live_web_search_health  # noqa: E402
from app.services.research_workflow.research_draft_pipeline import run_research_draft_pipeline  # noqa: E402


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def main() -> None:
    print("=== Research Workflow LLM/Web Verification ===")
    web_health = get_live_web_search_health()
    llm_health = get_llm_health()
    print(json.dumps({"webHealth": web_health, "llmHealth": llm_health}, indent=2))

    with SessionLocal() as db:
        case = db.get(Case, "green-valley-dha") or db.query(Case).first()
        _check("seed_case_available", case is not None, "Run python -m app.seed.seed_data first.")
        response = run_research_draft_pipeline(
            db,
            ResearchWorkflowRequest(
                case_id=case.id,
                draft_type="auto",
                focus_issues=[],
                include_documents=True,
                include_prior_notes=True,
                include_timeline=True,
                max_sources=10,
                max_live_sources=5,
                generate_pdf=True,
                use_live_web=True,
                use_llm=True,
                generate_full_draft=True,
            ),
        )
        payload = response.model_dump(mode="json")

    _check("workflow_completed_safely", payload.get("status") in {"completed", "completed_with_warnings"}, payload.get("status", ""))
    _check("detected_issues", bool(payload.get("detected_issues")), "")
    _check("query_plan", bool(payload.get("query_plan")), "")
    _check("retrieved_sources", bool(payload.get("retrieved_sources")), "")
    _check("sources_by_origin", bool(payload.get("sources_by_origin")), str(payload.get("sources_by_origin")))
    _check("research_memo", bool(payload.get("research_memo")), "")
    _check("generated_draft", bool(payload.get("generated_draft")), "")
    _check("critic_report", bool(payload.get("critic_report")), "")
    _check("lawyer_checklist", bool(payload.get("lawyer_review_checklist")), "")
    _check("warning", payload.get("legal_authority_warning") == LEGAL_RESEARCH_WARNING, "")
    _check("markdown_artifact", bool(payload.get("markdown_path")) and Path(payload["markdown_path"]).exists(), str(payload.get("markdown_path")))
    if web_health.get("available"):
        _check(
            "live_web_used_or_warning",
            bool(payload.get("live_web_used")) or "live web" in json.dumps(payload.get("provider_status", {})).casefold(),
            json.dumps(payload.get("provider_status", {}))[:500],
        )
    if llm_health.get("available"):
        _check(
            "llm_used_or_warning",
            bool(payload.get("llm_used_for_drafting")) or "llm" in json.dumps(payload.get("provider_status", {})).casefold(),
            json.dumps(payload.get("provider_status", {}))[:500],
        )

    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    for fake in ["abc v xyz", "pld 0000 sc 000", "imaginary citation"]:
        _check(f"no_fake_{fake}", fake not in serialized, "")

    source_tokens = [
        str(token).casefold()
        for source in payload.get("retrieved_sources", [])
        for token in (source.get("id"), source.get("citation"), source.get("title"))
        if token
    ]
    for authority in (payload.get("generated_draft") or {}).get("authorities_used", []):
        normalized_authority = str(authority).casefold()
        _check(
            f"authority_grounded_{authority[:30]}",
            any(token in normalized_authority or normalized_authority in token for token in source_tokens)
            or not authority,
            str(authority),
        )

    print(
        json.dumps(
            {
                "runId": payload.get("run_id"),
                "status": payload.get("status"),
                "sourcesByOrigin": payload.get("sources_by_origin"),
                "liveWebUsed": payload.get("live_web_used"),
                "llmUsedForResearch": payload.get("llm_used_for_research"),
                "llmUsedForDrafting": payload.get("llm_used_for_drafting"),
                "markdownPath": payload.get("markdown_path"),
                "pdfPath": payload.get("pdf_path"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
