from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
EDIT_MARKER = "TEST EDIT: This draft was edited and saved."
FORBIDDEN_PDF_DEBUG_MARKERS = (
    "retrieval: {",
    "liveWebSearch: {",
    "llm: {",
    "Draft type: research_memo",
)


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, bytes, dict[str, str], object | None]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if payload is not None else {}),
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=240) as response:
            body = response.read()
            parsed = _parse(body, response.headers.get("content-type", ""))
            print(f"{method:6} {path:58} -> {response.status}")
            return response.status, body, dict(response.headers.items()), parsed
    except HTTPError as exc:
        body = exc.read()
        parsed = _parse(body, exc.headers.get("content-type", ""))
        print(f"{method:6} {path:58} -> {exc.code}")
        return exc.code, body, dict(exc.headers.items()), parsed


def _parse(body: bytes, content_type: str) -> object | None:
    if "application/json" not in content_type:
        return None
    try:
        return json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        return None


def _dict(payload: object | None) -> dict:
    return payload if isinstance(payload, dict) else {}


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _extract_pdf_text(path: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        return ""
    text_parts: list[str] = []
    with fitz.open(path) as document:
        for page in document:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)


def main() -> None:
    print("=== Editable Draft Workflow Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"base_url={BASE_URL}")

    status, body, _, health_payload = _request("GET", "/api/research/health")
    _check("research_health_ok", status == 200, body[:300].decode("utf-8", "replace"))

    status, body, _, case_payload = _request(
        "POST",
        "/api/cases",
        {
            "title": "Editable Draft Verification Case",
            "facts": "The petitioner challenges cancellation of allotment without notice under Article 199.",
            "forum": "Lahore High Court",
            "clientName": "Editable Draft Client",
            "opposingParty": "Public Authority",
            "reliefSought": "Set aside cancellation and restore allotment.",
        },
    )
    case_id = _dict(case_payload).get("id")
    _check("case_created", status in {200, 201} and isinstance(case_id, str), body[:300].decode("utf-8", "replace"))

    status, body, _, run_payload = _request(
        "POST",
        f"/api/cases/{case_id}/research-draft",
        {
            "draftType": "auto",
            "useLiveWeb": False,
            "useLlm": False,
            "generateFullDraft": True,
            "generatePdf": True,
            "maxSources": 6,
            "maxLiveSources": 0,
        },
    )
    run = _dict(run_payload)
    run_id = run.get("runId")
    _check("research_run_created", status in {200, 201} and isinstance(run_id, str), body[:500].decode("utf-8", "replace"))
    draft = _dict(run.get("generatedDraft"))
    _check("draft_markdown_exists", bool(draft.get("draftMarkdown")), str(draft.keys()))
    draft_text = str(draft.get("draftMarkdown") or "")
    _check("draft_is_legal_document", "IN THE HIGH COURT" in draft_text and "PRAYER" in draft_text, draft_text[:300])

    status, body, _, draft_payload = _request("GET", f"/api/research/runs/{run_id}/draft")
    current_draft = _dict(draft_payload)
    _check("get_draft_ok", status == 200 and bool(current_draft.get("draftMarkdown")), body[:300].decode("utf-8", "replace"))

    edited_text = f"{current_draft['finalDraftMarkdown']}\n\n{EDIT_MARKER}\n"
    status, body, _, saved_payload = _request(
        "PATCH",
        f"/api/research/runs/{run_id}/draft",
        {"editedDraftMarkdown": edited_text, "editNote": "Verification edit."},
    )
    saved = _dict(saved_payload)
    _check("patch_draft_ok", status == 200 and EDIT_MARKER in str(saved), body[:300].decode("utf-8", "replace"))
    _check("final_draft_uses_edit", EDIT_MARKER in str(saved.get("finalDraftMarkdown", "")))

    status, body, _, pdf_payload = _request(
        "POST",
        f"/api/research/runs/{run_id}/pdf/regenerate",
        {"useEditedDraft": True, "pdfMode": "draft_with_research"},
    )
    pdf_result = _dict(pdf_payload)
    pdf_path = Path(str(pdf_result.get("pdfPath") or ""))
    _check("regenerate_pdf_ok", status == 200 and pdf_result.get("pdfGenerated") is True, body[:300].decode("utf-8", "replace"))
    _check("pdf_exists_on_disk", pdf_path.exists(), str(pdf_path))
    _check("pdf_size_gt_1kb", pdf_path.stat().st_size > 1024, str(pdf_path.stat().st_size if pdf_path.exists() else 0))
    _check("pdf_mode_reported", pdf_result.get("pdfMode") == "draft_with_research", str(pdf_result))

    pdf_text = _extract_pdf_text(pdf_path)
    if pdf_text:
        _check("pdf_contains_final_draft", "FINAL LEGAL DRAFT" in pdf_text and "PRAYER" in pdf_text, pdf_text[:500])
        for marker in FORBIDDEN_PDF_DEBUG_MARKERS:
            _check(f"pdf_no_debug_marker_{marker}", marker not in pdf_text, marker)

    status, markdown_body, _, _ = _request("GET", f"/api/research/runs/{run_id}/markdown")
    markdown_text = markdown_body.decode("utf-8", "replace")
    _check("markdown_contains_edit", status == 200 and EDIT_MARKER in markdown_text)
    _check("markdown_contains_final_draft", "FINAL LEGAL DRAFT" in markdown_text, markdown_text[:300])

    status, pdf_body, headers, _ = _request("GET", f"/api/research/runs/{run_id}/pdf")
    content_type = {key.lower(): value for key, value in headers.items()}.get("content-type", "")
    _check("pdf_endpoint_ok", status == 200 and "application/pdf" in content_type and pdf_body.startswith(b"%PDF"))

    print(
        json.dumps(
            {
                "caseId": case_id,
                "runId": run_id,
                "pdfPath": str(pdf_path),
                "pdfSizeBytes": pdf_path.stat().st_size,
                "openPdf": f"{BASE_URL}/api/research/runs/{run_id}/pdf",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except URLError as exc:
        print(f"[FAIL] backend_request_failed - {exc}")
        raise SystemExit(1) from exc
