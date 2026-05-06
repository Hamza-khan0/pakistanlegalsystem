from __future__ import annotations

import json
import sys
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
        with urlopen(request, timeout=60) as response:
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
        status, health = _request("GET", "/api/ml/models/case-type/health")
    except URLError as exc:
        print(f"[FAIL] backend_reachable - {exc}")
        raise SystemExit(1) from exc

    _check("health_status", status == 200, f"HTTP {status}")
    _check("health_task", health.get("task") == "case_type", str(health))
    _check("health_model_source", health.get("modelSource") in {"trained_imported", "demo_fallback"}, str(health))
    _check("health_warning", health.get("legalAuthorityWarning") == WARNING)
    print(json.dumps({"health": health}, indent=2, sort_keys=True))

    valid_text = (
        "The petitioner filed a constitutional petition under Article 199 challenging an administrative "
        "order passed by a public authority."
    )
    status, prediction = _request("POST", "/api/ml/predict/case-type", {"text": valid_text})
    _check("prediction_status", status == 200, f"HTTP {status}")
    _check("prediction_task", prediction.get("task") == "case_type", str(prediction))
    _check("prediction_label", bool(prediction.get("predictedLabel")), str(prediction))
    _check("prediction_source", prediction.get("modelSource") in {"trained_imported", "demo_fallback"}, str(prediction))
    _check("prediction_warning", prediction.get("legalAuthorityWarning") == WARNING)
    print(json.dumps({"prediction": prediction}, indent=2, sort_keys=True))

    status, empty_response = _request("POST", "/api/ml/predict/case-type", {"text": ""})
    _check("empty_text_validation", status == 422, f"HTTP {status} {empty_response}")

    long_text = "Article 199 constitutional petition alternate remedy. " * 600
    status, long_prediction = _request("POST", "/api/ml/predict/case-type", {"text": long_text})
    _check("long_text_status", status == 200, f"HTTP {status}")
    _check("long_text_label", bool(long_prediction.get("predictedLabel")), str(long_prediction))

    print("Case type endpoint verification passed.")


if __name__ == "__main__":
    main()
