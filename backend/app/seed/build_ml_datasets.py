from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ml.datasets.builder import build_ml_datasets


def main() -> None:
    session = SessionLocal()
    try:
        datasets = build_ml_datasets(session)
        for dataset in datasets:
            print(
                f"{dataset.task_name.value}: {dataset.record_count} records | "
                f"version={dataset.version} | id={dataset.id}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
