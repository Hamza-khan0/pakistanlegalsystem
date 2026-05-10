from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.research import PDF_MODE_DRAFT_WITH_RESEARCH, ResearchWorkflowRequest  # noqa: E402
from app.services import cases as case_service  # noqa: E402
from app.services.research_workflow.research_draft_pipeline import (  # noqa: E402
    get_research_run,
    regenerate_research_artifacts,
    run_research_draft_pipeline,
)


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _extract_pdf_text(path: Path) -> str:
    try:
        import fitz
    except Exception as exc:  # pragma: no cover - local diagnostic path
        raise RuntimeError("PyMuPDF/fitz is required for PDF text verification.") from exc
    with fitz.open(path) as document:
        return "\n".join(page.get_text("text") for page in document)


def main() -> None:
    print("=== Legal PDF Quality Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")

    with SessionLocal() as db:
        case = case_service.get_case_or_none(db, "green-valley-dha")
        _check("green_valley_case_available", case is not None, "Run python -m app.seed.seed_data first.")

        response = run_research_draft_pipeline(
            db,
            ResearchWorkflowRequest(
                case_id="green-valley-dha",
                draft_type="writ_petition",
                use_live_web=False,
                use_llm=False,
                generate_full_draft=True,
                generate_pdf=True,
                pdf_mode=PDF_MODE_DRAFT_WITH_RESEARCH,
                max_sources=8,
                max_live_sources=0,
            ),
        )
        payload = response.model_dump(by_alias=True)
        run_id = payload["runId"]
        draft = payload.get("generatedDraft") or {}
        draft_text = str(draft.get("draftMarkdown") or "")
        draft_type = str(draft.get("draftType") or "")

        _check("draft_type_writ", draft_type in {"writ_petition", "constitutional_petition"}, draft_type)
        for phrase in ["IN THE HIGH COURT", "CONSTITUTIONAL PETITION", "ARTICLE 199", "PRAYER", "VERIFICATION"]:
            _check(f"draft_contains_{phrase.lower().replace(' ', '_')}", phrase in draft_text.upper())

        run = get_research_run(db, run_id)
        _check("run_reloaded", run is not None, run_id)
        regenerate_research_artifacts(
            db,
            run,
            generate_pdf=True,
            use_edited_draft=True,
            pdf_mode=PDF_MODE_DRAFT_WITH_RESEARCH,
        )
        db.refresh(run)
        pdf_path = Path(str(run.pdf_path or ""))
        _check("pdf_exists", pdf_path.exists(), str(pdf_path))
        _check("pdf_size_gt_5kb", pdf_path.stat().st_size > 5 * 1024, str(pdf_path.stat().st_size))

        pdf_text = _extract_pdf_text(pdf_path)
        forbidden = [
            "retrieval: {",
            "liveWebSearch: {",
            "llm: {",
            "Draft type: research_memo",
            "'retrieval':",
            '"retrieval":',
        ]
        for phrase in forbidden:
            _check(f"pdf_excludes_{phrase}", phrase not in pdf_text)
        for phrase in ["FINAL LEGAL DRAFT", "CONSTITUTIONAL PETITION", "PRAYER", "Lawyer Review Checklist"]:
            _check(f"pdf_contains_{phrase.lower().replace(' ', '_')}", phrase in pdf_text)

        print(
            {
                "runId": run_id,
                "draftType": draft_type,
                "pdfPath": str(pdf_path),
                "pdfSizeBytes": pdf_path.stat().st_size,
            }
        )


if __name__ == "__main__":
    main()
