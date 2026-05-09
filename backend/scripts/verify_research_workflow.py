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
from app.services.research_workflow.research_draft_pipeline import run_research_draft_pipeline  # noqa: E402


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def main() -> None:
    print("=== Research Workflow Direct Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    with SessionLocal() as db:
        case = db.get(Case, "green-valley-dha") or db.query(Case).first()
        _check("seed_case_available", case is not None, "Run python -m app.seed.seed_data first.")
        request = ResearchWorkflowRequest(
            case_id=case.id,
            draft_type="auto",
            focus_issues=[],
            include_documents=True,
            include_prior_notes=True,
            include_timeline=True,
            max_sources=8,
            max_live_sources=4,
            generate_pdf=True,
            use_live_web=False,
            use_llm=False,
            generate_full_draft=True,
        )
        response = run_research_draft_pipeline(db, request)
        payload = response.model_dump(mode="json")

    _check("run_id_present", bool(payload.get("run_id")), str(payload.get("run_id")))
    _check("status_completed", payload.get("status") in {"completed", "completed_with_warnings"}, str(payload.get("status")))
    _check("detected_issues_present", bool(payload.get("detected_issues")), json.dumps(payload.get("detected_issues", [])[:3]))
    _check("query_plan_present", bool(payload.get("query_plan")), json.dumps(payload.get("query_plan", [])[:2]))
    _check("memo_present", bool(payload.get("research_memo")), "")
    _check("generated_draft_present", bool(payload.get("generated_draft")), "")
    _check("critic_report_present", bool(payload.get("critic_report")), "")
    _check("drafting_instructions_present", bool(payload.get("drafting_instructions")), "")
    _check("sources_by_origin_present", bool(payload.get("sources_by_origin")), str(payload.get("sources_by_origin")))
    _check("warning_present", payload.get("legal_authority_warning") == LEGAL_RESEARCH_WARNING, "")
    _check("privacy_notice_present", "OpenAI API" in str(payload.get("privacy_notice") or payload.get("provider_status")), "")

    markdown_path = payload.get("markdown_path")
    _check("markdown_generated", bool(markdown_path) and Path(markdown_path).exists(), str(markdown_path))
    pdf_path = payload.get("pdf_path")
    if pdf_path:
        _check("pdf_generated_if_reported", Path(pdf_path).exists(), str(pdf_path))
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    _check("no_fake_citation_placeholder", "abc v xyz" not in serialized, "")
    print(
        json.dumps(
            {
                "runId": payload.get("run_id"),
                "status": payload.get("status"),
                "issues": [item.get("label") for item in payload.get("detected_issues", [])[:5]],
                "sourceCount": len(payload.get("retrieved_sources", [])),
                "sourcesByOrigin": payload.get("sources_by_origin"),
                "llmUsedForDrafting": payload.get("llm_used_for_drafting"),
                "markdownPath": markdown_path,
                "pdfPath": pdf_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
