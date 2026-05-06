from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ml.training.imported_case_type import (  # noqa: E402
    IMPORTED_ZIP_PATH,
    LEGAL_AUTHORITY_WARNING,
    discover_imported_case_type_model,
    predict_case_type_text,
    reset_imported_case_type_runtime,
)


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _print_check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{(' - ' + detail) if detail else ''}")


def _require(ok: bool, name: str, detail: str = "") -> None:
    _print_check(name, ok, detail)
    if not ok:
        raise SystemExit(1)


def _probability_sum(probabilities: dict[str, float]) -> float:
    return round(sum(float(value) for value in probabilities.values()), 4)


def main() -> None:
    _print_section("Paths")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"zip_path={IMPORTED_ZIP_PATH}")

    _print_section("Discovery")
    _require(IMPORTED_ZIP_PATH.exists(), "zip_exists", str(IMPORTED_ZIP_PATH))
    reset_imported_case_type_runtime()
    discovery = discover_imported_case_type_model(reset_cache=True)
    _require(discovery.zip_found, "zip_found", str(discovery.zip_path))
    _require(discovery.extracted, "zip_extracted", str(discovery.extract_dir))
    _require(discovery.found, "model_discovered", discovery.reason)
    _require(discovery.required_files_valid, "required_files_valid", discovery.reason)
    _require(discovery.model_dir_exists, "model_dir_exists", str(discovery.model_dir))
    _require(discovery.tokenizer_dir_exists, "tokenizer_dir_exists", str(discovery.tokenizer_dir))
    _require(discovery.label_mapping_loaded, "label_mapping_loaded", str(discovery.label_mapping_path))
    _require(discovery.metrics_loaded, "metrics_loaded", str(discovery.metrics_path))
    _print_check("manifest_loaded", discovery.manifest_loaded, str(discovery.manifest_path or "not provided"))

    _print_section("Direct Predictions")
    samples = {
        "constitutional": "The petitioner filed a constitutional petition under Article 199 challenging an administrative order.",
        "criminal": "The accused seeks bail after an FIR and criminal conviction proceedings.",
        "civil": "The civil dispute concerns property, decree, possession, and injunction relief.",
    }
    for name, text in samples.items():
        prediction = predict_case_type_text(text)
        source = prediction.get("model_source")
        probabilities = prediction.get("probabilities", {})
        total = _probability_sum(probabilities)
        print(
            json.dumps(
                {
                    "sample": name,
                    "label": prediction.get("predicted_label"),
                    "confidence": prediction.get("confidence"),
                    "model_source": source,
                    "model_status": prediction.get("model_status"),
                    "probability_sum": total,
                },
                indent=2,
                sort_keys=True,
            )
        )
        _require(source == "trained_imported", f"{name}_uses_trained_model", str(source))
        _require(bool(prediction.get("predicted_label")), f"{name}_has_label")
        _require(prediction.get("legal_authority_warning") == LEGAL_AUTHORITY_WARNING, f"{name}_has_warning")
        _require(0.98 <= total <= 1.02, f"{name}_probabilities_sum_to_one", str(total))

    _print_section("Result")
    print("Imported case_type model verification passed.")


if __name__ == "__main__":
    main()
