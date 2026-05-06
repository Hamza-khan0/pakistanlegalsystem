from __future__ import annotations

from app.db.session import SessionLocal
from app.models.enums import MlModelFamily, MlTaskName
from app.services.ml.datasets.builder import build_ml_datasets
from app.services.ml.training.trainer import train_ml_model


DEFAULT_SUITE = [
    (MlTaskName.CASE_OUTCOME, MlModelFamily.BASELINE),
    (MlTaskName.CASE_OUTCOME, MlModelFamily.TRANSFORMER),
    (MlTaskName.MAINTAINABILITY, MlModelFamily.BASELINE),
    (MlTaskName.MAINTAINABILITY, MlModelFamily.HYBRID_MLP),
    (MlTaskName.RISK_SCORING, MlModelFamily.BASELINE),
    (MlTaskName.RISK_SCORING, MlModelFamily.HYBRID_MLP),
    (MlTaskName.CASE_TYPE, MlModelFamily.BASELINE),
    (MlTaskName.CASE_TYPE, MlModelFamily.TRANSFORMER),
]


def main() -> None:
    session = SessionLocal()
    try:
        datasets = {dataset.task_name: dataset for dataset in build_ml_datasets(session)}
        for task_name, family in DEFAULT_SUITE:
            model = train_ml_model(
                session,
                dataset=datasets[task_name],
                model_family=family,
            )
            print(
                f"{task_name.value} / {family.value}: {model.status.value} | "
                f"primaryMetric={model.metrics_json.get('primaryMetric', 0.0)} | id={model.id}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
