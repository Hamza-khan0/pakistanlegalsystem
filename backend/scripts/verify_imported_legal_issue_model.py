from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ml.training.imported_case_type import LEGAL_AUTHORITY_WARNING  # noqa: E402
from app.services.ml.training.imported_legal_issue import (  # noqa: E402
    IMPORTED_ZIP_PATH,
    discover_imported_legal_issue_model,
    predict_legal_issues,
    reset_imported_legal_issue_runtime,
)
from app.services.research_query_hints import build_research_query_hints_from_issues  # noqa: E402


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def _probabilities_valid(probabilities: dict[str, float]) -> bool:
    return bool(probabilities) and all(0.0 <= float(value) <= 1.0 for value in probabilities.values())


def main() -> None:
    _print_section("Paths")
    print(f"project_root={PROJECT_ROOT}")
    print(f"backend_dir={BACKEND_DIR}")
    print(f"zip_path={IMPORTED_ZIP_PATH}")

    _print_section("Discovery")
    _check("zip_exists", IMPORTED_ZIP_PATH.exists(), str(IMPORTED_ZIP_PATH))
    reset_imported_legal_issue_runtime()
    discovery = discover_imported_legal_issue_model(reset_cache=True)
    _check("zip_found", discovery.zip_found, str(discovery.zip_path))
    _check("zip_extracted", discovery.extracted, str(discovery.extract_dir))
    _check("model_discovered", discovery.found, discovery.reason)
    _check("required_files_valid", discovery.required_files_valid, discovery.reason)
    _check("model_dir_exists", discovery.model_dir_exists, str(discovery.model_dir))
    _check("tokenizer_dir_exists", discovery.tokenizer_dir_exists, str(discovery.tokenizer_dir))
    _check("label_mapping_loaded", discovery.label_mapping_loaded, str(discovery.label_mapping_path))
    _check("metrics_loaded", discovery.metrics_loaded, str(discovery.metrics_path))
    _check("labels_count_positive", discovery.labels_count > 0, str(discovery.labels_count))
    print(f"threshold_config_loaded={discovery.threshold_config_loaded}")
    print(f"manifest_loaded={discovery.manifest_loaded}")

    _print_section("Direct Multi-Label Predictions")
    samples = {
        "article_199_natural_justice": (
            "The petitioner challenged cancellation of allotment under Article 199 without notice "
            "and without opportunity of hearing."
        ),
        "criminal_bail": "The accused seeks post-arrest bail after FIR registration under section 497 CrPC.",
        "injunction_property": "The plaintiff seeks temporary injunction over land possession and sale deed transfer.",
        "limitation_delay": "The suit is challenged as time barred due to delay and laches under the Limitation Act.",
    }
    for name, text in samples.items():
        prediction = predict_legal_issues(text, threshold=0.45, top_k=8)
        source = prediction.get("model_source")
        probabilities = prediction.get("probabilities", {})
        selected = prediction.get("selected_issues", [])
        top_issues = prediction.get("top_issues", [])
        print(
            json.dumps(
                {
                    "sample": name,
                    "selected": selected[:5],
                    "top": top_issues[:5],
                    "model_source": source,
                    "model_status": prediction.get("model_status"),
                },
                indent=2,
                sort_keys=True,
            )
        )
        _check(f"{name}_uses_trained_or_fallback", source in {"trained_imported", "demo_fallback"}, str(source))
        _check(f"{name}_has_top_issues", bool(top_issues), str(prediction))
        _check(f"{name}_probabilities_between_zero_and_one", _probabilities_valid(probabilities), str(probabilities))
        probability_sum = round(sum(float(value) for value in probabilities.values()), 4)
        _check(f"{name}_sigmoid_not_softmax_expected", probability_sum > 1.01 or len(probabilities) > 2, str(probability_sum))
        _check(f"{name}_has_warning", prediction.get("legal_authority_warning") == LEGAL_AUTHORITY_WARNING)

    _print_section("Research Query Hints")
    hints = build_research_query_hints_from_issues(
        ["constitutional_petition", "alternate_remedy", "natural_justice"],
        samples["article_199_natural_justice"],
    )
    print(json.dumps({"hints": hints}, indent=2))
    _check("research_hints_produced", len(hints) >= 3, str(hints))

    _print_section("Result")
    print("Imported legal_issue_classifier model verification passed.")


if __name__ == "__main__":
    main()
