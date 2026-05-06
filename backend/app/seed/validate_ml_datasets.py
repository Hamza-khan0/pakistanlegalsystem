from __future__ import annotations

from app.db.session import SessionLocal
from app.services.evaluation.dataset_readiness import evaluate_all_datasets
from app.services.ml.training.trainer import list_ml_datasets


def main() -> None:
    with SessionLocal() as db:
        results = evaluate_all_datasets(list_ml_datasets(db))
    for result in results:
        print(
            f"{result['taskName']}: {result['status']} "
            f"({result['totalExamples']} examples, warnings={len(result['warnings'])})"
        )


if __name__ == "__main__":
    main()
