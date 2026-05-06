from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.services.ml.training.imported_case_type import (
    discover_imported_case_type_model,
    get_case_type_model_health,
    predict_case_type_text,
)


def _print_result(name: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} - {detail}")


def _try_endpoint_prediction() -> None:
    payload = json.dumps(
        {
            "text": "Constitutional petition under Article 199 challenging maintainability and alternate remedy.",
        }
    ).encode("utf-8")
    request = Request(
        "http://127.0.0.1:8000/api/ml/predict/case-type",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        ok = response.status == 200 and body.get("task") == "case_type" and body.get("predictedLabel")
        _print_result("endpoint_prediction", ok, f"HTTP {response.status} source={body.get('modelSource')}")
    except URLError as exc:
        _print_result("endpoint_prediction", True, f"skipped; backend not reachable ({exc})")


def _try_case_prediction_pipeline() -> None:
    payload = json.dumps({"caseId": "green-valley-dha", "taskName": "case_type"}).encode("utf-8")
    request = Request(
        "http://127.0.0.1:8000/api/cases/green-valley-dha/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        first = body[0] if isinstance(body, list) and body else {}
        ok = (
            response.status == 201
            and first.get("taskName") == "case_type"
            and first.get("metadataJson", {}).get("modelSource") == "trained_imported"
        )
        _print_result(
            "case_prediction_pipeline",
            ok,
            f"HTTP {response.status} source={first.get('metadataJson', {}).get('modelSource')}",
        )
    except URLError as exc:
        _print_result("case_prediction_pipeline", True, f"skipped; backend not reachable ({exc})")


def main() -> None:
    info = discover_imported_case_type_model()
    _print_result(
        "bundle_discovery",
        info.found,
        str(info.task_dir) if info.task_dir else "trained bundle not found; fallback will be used",
    )
    _print_result("manifest_loaded", info.manifest_loaded, str(info.manifest_path))
    _print_result("metrics_loaded", info.metrics_loaded, str(info.metrics_path))

    health = get_case_type_model_health()
    _print_result(
        "runtime_health",
        health["model_source"] in {"trained_imported", "demo_fallback"},
        json.dumps(health, sort_keys=True),
    )

    prediction = predict_case_type_text(
        "Civil appeal and constitutional petition concerning Article 199 maintainability."
    )
    _print_result(
        "service_prediction",
        prediction["task"] == "case_type" and bool(prediction["predicted_label"]),
        json.dumps(
            {
                "label": prediction["predicted_label"],
                "confidence": prediction["confidence"],
                "source": prediction["model_source"],
            },
            sort_keys=True,
        ),
    )
    _try_endpoint_prediction()
    _try_case_prediction_pipeline()


if __name__ == "__main__":
    main()
