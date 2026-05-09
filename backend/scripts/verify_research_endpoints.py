from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

BASE_URL = "http://127.0.0.1:8000"


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, bytes, dict | None]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if payload is not None else {},
        method=method,
    )
    try:
        with urlopen(request, timeout=180) as response:
            body = response.read()
            print(f"{method} {path} -> {response.status}")
            parsed = None
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                parsed = json.loads(body.decode("utf-8")) if body else {}
            return response.status, body, parsed
    except HTTPError as exc:
        body = exc.read()
        print(f"{method} {path} -> {exc.code}")
        try:
            parsed = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body.decode("utf-8", "replace")}
        return exc.code, body, parsed


def main() -> None:
    print("=== Research Endpoint Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    health_status, health_body, health_payload = _request("GET", "/api/research/health")
    _check("health_ok", health_status == 200, health_body[:300].decode("utf-8", "replace"))
    health_payload = health_payload or {}
    _check("workflow_available", bool(health_payload.get("workflowAvailable")), json.dumps(health_payload, indent=2)[:500])

    payload = {
        "caseId": "green-valley-dha",
        "draftType": "auto",
        "focusIssues": [],
        "includeDocuments": True,
        "includePriorNotes": True,
        "includeTimeline": True,
        "maxSources": 8,
        "maxLiveSources": 4,
        "generatePdf": True,
        "useLiveWeb": True,
        "useLlm": True,
        "generateFullDraft": True,
    }
    created_status, created_body, created_payload = _request("POST", "/api/research/runs", payload=payload)
    _check("create_run_ok", created_status in {200, 201}, created_body[:500].decode("utf-8", "replace"))
    created_payload = created_payload or {}
    run_id = created_payload.get("runId")
    _check("run_id_present", bool(run_id), json.dumps(created_payload, indent=2)[:500])
    _check("response_contains_memo", bool(created_payload.get("researchMemo")), "")
    _check("response_contains_generated_draft", bool(created_payload.get("generatedDraft")), "")
    _check("response_contains_critic", bool(created_payload.get("criticReport")), "")
    _check("response_contains_provider_status", bool(created_payload.get("providerStatus")), "")
    _check("response_contains_sources_by_origin", bool(created_payload.get("sourcesByOrigin")), str(created_payload.get("sourcesByOrigin")))
    _check("response_contains_privacy_notice", "OpenAI API" in str(created_payload.get("privacyNotice") or created_payload.get("providerStatus")), "")

    fetched_status, fetched_body, _ = _request("GET", f"/api/research/runs/{run_id}")
    _check("fetch_run_ok", fetched_status == 200, fetched_body[:300].decode("utf-8", "replace"))

    listed_status, listed_body, listed_payload = _request("GET", "/api/research/cases/green-valley-dha/runs")
    _check(
        "list_case_runs_ok",
        listed_status == 200 and isinstance(listed_payload, list),
        listed_body[:300].decode("utf-8", "replace"),
    )

    markdown_status, markdown_body, _ = _request("GET", f"/api/research/runs/{run_id}/markdown")
    markdown_text = markdown_body.decode("utf-8", "replace")
    _check(
        "markdown_ok",
        markdown_status == 200
        and "AI Legal Chambers Research & Draft Output" in markdown_text
        and "Generated Draft" in markdown_text,
        markdown_text[:300],
    )

    if created_payload.get("pdfPath"):
        pdf_status, pdf_body, _ = _request("GET", f"/api/research/runs/{run_id}/pdf")
        _check("pdf_ok", pdf_status == 200 and pdf_body.startswith(b"%PDF"), str(pdf_status))
    else:
        print("[INFO] pdf_not_reported - skipping PDF download check")

    print(
        json.dumps(
            {
                "runId": run_id,
                "status": created_payload.get("status"),
                "sourceCount": len(created_payload.get("retrievedSources", [])),
                "sourcesByOrigin": created_payload.get("sourcesByOrigin"),
                "warnings": created_payload.get("warnings"),
                "liveWebUsed": created_payload.get("liveWebUsed"),
                "llmUsedForDrafting": created_payload.get("llmUsedForDrafting"),
                "pdfPath": created_payload.get("pdfPath"),
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
