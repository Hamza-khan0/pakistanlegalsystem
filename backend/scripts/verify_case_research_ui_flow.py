from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
FORBIDDEN_PDF_DEBUG_MARKERS = (
    "retrieval: {",
    "liveWebSearch: {",
    "llm: {",
    "Draft type: research_memo",
)


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, bytes, dict | list | None]:
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
            parsed = _parse_json(body, response.headers.get("content-type", ""))
            print(f"{method:6} {path:48} -> {response.status}")
            return response.status, body, parsed
    except HTTPError as exc:
        body = exc.read()
        parsed = _parse_json(body, exc.headers.get("content-type", ""))
        print(f"{method:6} {path:48} -> {exc.code}")
        return exc.code, body, parsed


def _parse_json(body: bytes, content_type: str) -> dict | list | None:
    if "application/json" not in content_type:
        return None
    try:
        return json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        return None


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _extract_pdf_text(path: str | None) -> str:
    if not path:
        return ""
    pdf_path = Path(path)
    if not pdf_path.exists():
        return ""
    try:
        import fitz  # type: ignore
    except Exception:
        return ""
    text_parts: list[str] = []
    with fitz.open(pdf_path) as document:
        for page in document:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)


def _as_dict(payload: object) -> dict:
    return payload if isinstance(payload, dict) else {}


def main() -> None:
    print("=== Case Research UI Flow Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")

    status, body, cases_payload = _request("GET", "/api/cases")
    _check("list_cases_ok", status == 200 and isinstance(cases_payload, list), body[:300].decode("utf-8", "replace"))

    create_payload = {
        "title": "UI Flow Verification - Article 199 Allotment Case",
        "facts": (
            "The petitioner says an allotment was cancelled by a public authority without notice, "
            "without opportunity of hearing, and despite payments being made. The respondent may raise "
            "alternate remedy and maintainability objections."
        ),
        "forum": "Lahore High Court",
        "clientName": "Verification Client",
        "opposingParty": "Public Authority",
        "caseType": "Constitutional Petition",
        "reliefSought": "Set aside cancellation and restore allotment",
        "status": "Active",
    }
    status, body, created_payload = _request("POST", "/api/cases", create_payload)
    created = _as_dict(created_payload)
    _check("create_case_ok", status in {200, 201}, body[:400].decode("utf-8", "replace"))
    case_id = created.get("id")
    _check("created_case_id_present", isinstance(case_id, str) and bool(case_id), str(case_id))
    _check("generated_or_supplied_case_number_present", bool(created.get("caseNumber")), str(created.get("caseNumber")))

    status, body, fetched_payload = _request("GET", f"/api/cases/{case_id}")
    fetched = _as_dict(fetched_payload)
    _check("fetch_case_ok", status == 200 and fetched.get("id") == case_id, body[:300].decode("utf-8", "replace"))
    _check("case_persisted_summary", "allotment" in str(fetched.get("summary", "")).lower(), str(fetched.get("summary", ""))[:180])

    run_request = {
        "draftType": "auto",
        "focusIssues": [],
        "includeDocuments": True,
        "includePriorNotes": True,
        "includeTimeline": True,
        "maxSources": 6,
        "maxLiveSources": 0,
        "generatePdf": True,
        "useLiveWeb": False,
        "useLlm": False,
        "generateFullDraft": True,
        "pdfMode": "draft_with_research",
    }
    status, body, run_payload = _request("POST", f"/api/cases/{case_id}/research-draft", run_request)
    run = _as_dict(run_payload)
    _check("research_draft_ok", status in {200, 201}, body[:500].decode("utf-8", "replace"))
    run_id = run.get("runId")
    _check("run_id_present", isinstance(run_id, str) and bool(run_id), str(run_id))
    _check("run_status_complete", run.get("status") in {"completed", "completed_with_warnings"}, str(run.get("status")))
    _check("memo_present", bool(run.get("researchMemo")), "")
    _check("generated_draft_present", bool(run.get("generatedDraft", {}).get("draftMarkdown")), "")
    draft = _as_dict(run.get("generatedDraft"))
    draft_text = str(draft.get("draftMarkdown") or "")
    _check("generated_draft_is_pleading", "IN THE HIGH COURT" in draft_text and "PRAYER" in draft_text, draft_text[:300])
    _check(
        "generated_draft_type_not_memo",
        draft.get("draftType") in {"writ_petition", "constitutional_petition"},
        str(draft.get("draftType")),
    )
    _check("critic_present", bool(run.get("criticReport")), "")
    _check("legal_warning_present", "not legal advice" in str(run).lower(), "")

    serialized = json.dumps(run, ensure_ascii=False).casefold()
    for fake in ("abc v xyz", "pld 0000 sc 000", "0000 scmr 000", "imaginary case"):
        _check(f"no_fake_placeholder_{fake}", fake not in serialized)

    status, body, runs_payload = _request("GET", f"/api/cases/{case_id}/research-runs")
    _check("case_research_runs_ok", status == 200 and isinstance(runs_payload, list), body[:300].decode("utf-8", "replace"))
    _check(
        "stored_run_listed",
        any(isinstance(item, dict) and item.get("runId") == run_id for item in (runs_payload or [])),
        json.dumps(runs_payload, ensure_ascii=False)[:500],
    )

    status, body, fetched_run_payload = _request("GET", f"/api/research/runs/{run_id}")
    fetched_run = _as_dict(fetched_run_payload)
    _check("fetch_research_run_ok", status == 200 and fetched_run.get("runId") == run_id, body[:300].decode("utf-8", "replace"))

    status, markdown_body, _ = _request("GET", f"/api/research/runs/{run_id}/markdown")
    markdown_text = markdown_body.decode("utf-8", "replace")
    _check(
        "markdown_available",
        status == 200
        and "AI Legal Chambers" in markdown_text
        and "Research & Draft Output" in markdown_text
        and "FINAL LEGAL DRAFT" in markdown_text,
        markdown_text[:300],
    )

    if run.get("pdfPath"):
        status, pdf_body, _ = _request("GET", f"/api/research/runs/{run_id}/pdf")
        _check("pdf_available_if_reported", status == 200 and pdf_body.startswith(b"%PDF"), str(status))
        pdf_text = _extract_pdf_text(str(run.get("pdfPath")))
        if pdf_text:
            _check("pdf_contains_final_draft", "FINAL LEGAL DRAFT" in pdf_text and "PRAYER" in pdf_text, pdf_text[:500])
            for marker in FORBIDDEN_PDF_DEBUG_MARKERS:
                _check(f"pdf_no_debug_marker_{marker}", marker not in pdf_text, marker)
    else:
        print("[INFO] pdf_not_reported - markdown remains available")

    print(
        json.dumps(
            {
                "caseId": case_id,
                "caseNumber": created.get("caseNumber"),
                "runId": run_id,
                "status": run.get("status"),
                "sourceCount": len(run.get("retrievedSources", [])),
                "markdownPath": run.get("markdownPath"),
                "pdfPath": run.get("pdfPath"),
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
