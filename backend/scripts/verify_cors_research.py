from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ORIGIN = "http://localhost:3001"


def _request(
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    preflight_method: str | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Origin": ORIGIN,
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if method == "OPTIONS":
        headers["Access-Control-Request-Method"] = preflight_method or "POST"
        headers["Access-Control-Request-Headers"] = "content-type"
    request = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=180) as response:
            return response.status, response.read(), dict(response.headers.items())
    except HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers.items())


def _header(headers: dict[str, str], name: str) -> str:
    lowered = {key.lower(): value for key, value in headers.items()}
    return lowered.get(name.lower(), "")


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _print_result(method: str, path: str, status: int, headers: dict[str, str]) -> None:
    print(
        f"{method:7} {path:42} -> {status:3} | "
        f"allow-origin={_header(headers, 'access-control-allow-origin') or '-'} | "
        f"allow-methods={_header(headers, 'access-control-allow-methods') or '-'}"
    )


def _json_body(body: bytes) -> dict:
    try:
        return json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        return {}


def _body_preview(body: bytes, headers: dict[str, str], limit: int = 300) -> str:
    content_type = _header(headers, "content-type").lower()
    if "application/pdf" in content_type:
        return f"<PDF response: {len(body)} bytes>"
    return body[:limit].decode("utf-8", "replace")


def main() -> None:
    print("=== CORS Research Verification ===")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"origin={ORIGIN}")

    checks: list[tuple[str, str, dict | None, str | None]] = [
        ("OPTIONS", "/api/health", None, "GET"),
        ("GET", "/api/health", None, None),
        ("OPTIONS", "/api/research/health", None, "GET"),
        ("GET", "/api/research/health", None, None),
        ("OPTIONS", "/api/cases", None, "POST"),
        ("GET", "/api/cases", None, None),
    ]

    for method, path, payload, preflight in checks:
        status, body, headers = _request(method, path, payload=payload, preflight_method=preflight)
        _print_result(method, path, status, headers)
        _check(
            f"{method}_{path}_cors",
            _header(headers, "access-control-allow-origin") == ORIGIN,
            _body_preview(body, headers, 240),
        )

    create_payload = {
        "title": "CORS Verification Research Case",
        "facts": "The petitioner challenges cancellation of allotment without notice under Article 199.",
        "forum": "Lahore High Court",
        "clientName": "CORS Test Client",
        "opposingParty": "Development Authority",
        "reliefSought": "Set aside cancellation and restore allotment",
    }
    status, body, headers = _request("POST", "/api/cases", payload=create_payload)
    _print_result("POST", "/api/cases", status, headers)
    _check("POST_/api/cases_cors", _header(headers, "access-control-allow-origin") == ORIGIN)
    _check("case_created", status in {200, 201}, _body_preview(body, headers))
    case_id = _json_body(body).get("id")
    _check("case_id_present", isinstance(case_id, str) and bool(case_id), str(case_id))

    research_run_id: str | None = None
    for method, path, payload, preflight in [
        ("OPTIONS", f"/api/cases/{case_id}/runs", None, "GET"),
        ("GET", f"/api/cases/{case_id}/runs", None, None),
        ("OPTIONS", f"/api/cases/{case_id}/research-draft", None, "POST"),
        (
            "POST",
            f"/api/cases/{case_id}/research-draft",
            {
                "draftType": "auto",
                "useLiveWeb": False,
                "useLlm": False,
                "generateFullDraft": True,
                "generatePdf": True,
                "maxSources": 4,
                "maxLiveSources": 0,
            },
            None,
        ),
    ]:
        status, body, headers = _request(method, path, payload=payload, preflight_method=preflight)
        _print_result(method, path, status, headers)
        _check(
            f"{method}_{path}_cors",
            _header(headers, "access-control-allow-origin") == ORIGIN,
            _body_preview(body, headers),
        )
        if method != "OPTIONS":
            _check(f"{method}_{path}_status", status < 500, _body_preview(body, headers))
        if method == "POST" and path.endswith("/research-draft"):
            parsed = _json_body(body)
            if isinstance(parsed.get("runId"), str):
                research_run_id = parsed["runId"]

    _check("research_run_id_for_artifact_cors", bool(research_run_id), str(research_run_id))
    for method, path, payload, preflight in [
        ("OPTIONS", f"/api/research/runs/{research_run_id}/draft", None, "PATCH"),
        ("GET", f"/api/research/runs/{research_run_id}/draft", None, None),
        (
            "PATCH",
            f"/api/research/runs/{research_run_id}/draft",
            {"editedDraftMarkdown": "CORS edited draft text with lawyer verification note."},
            None,
        ),
        ("OPTIONS", f"/api/research/runs/{research_run_id}/pdf/regenerate", None, "POST"),
        (
            "POST",
            f"/api/research/runs/{research_run_id}/pdf/regenerate",
            {"useEditedDraft": True},
            None,
        ),
        ("GET", f"/api/research/runs/{research_run_id}/markdown", None, None),
        ("GET", f"/api/research/runs/{research_run_id}/pdf", None, None),
    ]:
        status, body, headers = _request(method, path, payload=payload, preflight_method=preflight)
        _print_result(method, path, status, headers)
        _check(
            f"{method}_{path}_cors",
            _header(headers, "access-control-allow-origin") == ORIGIN,
            _body_preview(body, headers),
        )
        if method != "OPTIONS":
            _check(f"{method}_{path}_status", status < 500, _body_preview(body, headers))

    print("[PASS] CORS headers are present for localhost:3001 browser requests.")


if __name__ == "__main__":
    try:
        main()
    except URLError as exc:
        print(f"[FAIL] backend_request_failed - {exc}")
        raise SystemExit(1) from exc
