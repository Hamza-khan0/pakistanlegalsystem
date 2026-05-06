from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000"
WARNING = (
    "This model is experimental and trained on weak or dataset-derived labels. "
    "It is not legal advice and not legally authoritative."
)


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if payload is not None else {},
        method=method,
    )
    try:
        with urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def main() -> None:
    try:
        status, health = _request("GET", "/api/ml/models/legal-issues/health")
    except URLError as exc:
        print(f"[FAIL] backend_reachable - {exc}")
        raise SystemExit(1) from exc

    _check("health_status", status == 200, f"HTTP {status}")
    _check("health_task", health.get("task") == "legal_issue_classifier", str(health))
    _check("health_model_source", health.get("modelSource") in {"trained_imported", "demo_fallback"}, str(health))
    _check("health_warning", health.get("legalAuthorityWarning") == WARNING)
    print(json.dumps({"health": health}, indent=2, sort_keys=True))

    valid_text = (
        "The petitioner challenged cancellation of allotment under Article 199. The order was passed "
        "without notice and without opportunity of hearing, and the respondent raised alternate remedy."
    )
    status, prediction = _request(
        "POST",
        "/api/ml/predict/legal-issues",
        {"text": valid_text, "threshold": 0.45, "topK": 8, "includeProbabilities": True},
    )
    _check("prediction_status", status == 200, f"HTTP {status}")
    _check("prediction_task", prediction.get("task") == "legal_issue_classifier", str(prediction))
    _check("prediction_top_issues", bool(prediction.get("topIssues")), str(prediction))
    _check("prediction_source", prediction.get("modelSource") in {"trained_imported", "demo_fallback"}, str(prediction))
    _check("prediction_warning", prediction.get("legalAuthorityWarning") == WARNING)
    _check("prediction_threshold_override", abs(float(prediction.get("thresholdUsed", 0)) - 0.45) < 0.001)
    _check("prediction_top_k", len(prediction.get("topIssues", [])) <= 8, str(prediction.get("topIssues")))
    print(json.dumps({"prediction": prediction}, indent=2, sort_keys=True))

    status, empty_response = _request("POST", "/api/ml/predict/legal-issues", {"text": ""})
    _check("empty_text_validation", status == 422, f"HTTP {status} {empty_response}")

    long_text = "Article 199 constitutional petition alternate remedy natural justice notice. " * 900
    status, long_prediction = _request(
        "POST",
        "/api/ml/predict/legal-issues",
        {"text": long_text, "threshold": 0.4, "topK": 5},
    )
    _check("long_text_status", status == 200, f"HTTP {status}")
    _check("long_text_top_k", len(long_prediction.get("topIssues", [])) <= 5, str(long_prediction))
    _check("long_text_warning", long_prediction.get("legalAuthorityWarning") == WARNING)

    print("Legal issue endpoint verification passed.")


if __name__ == "__main__":
    main()
