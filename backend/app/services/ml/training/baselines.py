from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from scipy.sparse import hstack
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.models.enums import MlTaskName
from app.services.ml.training.evaluation import classification_metrics, combine_split_metrics


@dataclass(slots=True)
class BaselineTrainingResult:
    metrics: dict[str, Any]
    label_schema: list[str]
    artifact_files: dict[str, str]
    summary: str


def _split_rows(rows: list[dict[str, Any]], split_name: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split_name]


def _matrix_from_rows(
    rows: list[dict[str, Any]],
    text_vectorizer: TfidfVectorizer,
    struct_vectorizer: DictVectorizer,
    *,
    fit: bool,
):
    texts = [row["normalized_text"] or row["text"] for row in rows]
    structures = [row["structured_features"] for row in rows]
    if fit:
        text_matrix = text_vectorizer.fit_transform(texts)
        struct_matrix = struct_vectorizer.fit_transform(structures)
    else:
        text_matrix = text_vectorizer.transform(texts)
        struct_matrix = struct_vectorizer.transform(structures)
    return hstack([text_matrix, struct_matrix])


def train_baseline_model(
    *,
    task_name: MlTaskName,
    rows: list[dict[str, Any]],
    artifact_dir: Path,
) -> BaselineTrainingResult:
    train_rows = _split_rows(rows, "train")
    validation_rows = _split_rows(rows, "validation")
    test_rows = _split_rows(rows, "test")
    all_labels = sorted({row["label"] for row in rows})

    text_vectorizer = TfidfVectorizer(max_features=800, ngram_range=(1, 1))
    struct_vectorizer = DictVectorizer(sparse=True)

    train_matrix = _matrix_from_rows(train_rows, text_vectorizer, struct_vectorizer, fit=True)
    validation_matrix = _matrix_from_rows(validation_rows, text_vectorizer, struct_vectorizer, fit=False)
    test_matrix = _matrix_from_rows(test_rows, text_vectorizer, struct_vectorizer, fit=False)

    y_train = [row["label"] for row in train_rows]
    y_validation = [row["label"] for row in validation_rows]
    y_test = [row["label"] for row in test_rows]

    if task_name == MlTaskName.RISK_SCORING:
        classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            min_samples_leaf=1,
        )
        fit_matrix = train_matrix.toarray()
        validation_input = validation_matrix.toarray()
        test_input = test_matrix.toarray()
    else:
        classifier = LogisticRegression(
            max_iter=300,
            class_weight="balanced",
            random_state=42,
            solver="liblinear",
        )
        fit_matrix = train_matrix
        validation_input = validation_matrix
        test_input = test_matrix

    classifier.fit(fit_matrix, y_train)
    train_predictions = classifier.predict(fit_matrix).tolist()
    validation_predictions = classifier.predict(validation_input).tolist() if len(validation_rows) else []
    test_predictions = classifier.predict(test_input).tolist() if len(test_rows) else []

    metrics = combine_split_metrics(
        train_metrics=classification_metrics(
            y_train,
            train_predictions,
            all_labels,
            languages=[row.get("language", "Unknown") for row in train_rows],
        ),
        validation_metrics=classification_metrics(
            y_validation,
            validation_predictions,
            all_labels,
            languages=[row.get("language", "Unknown") for row in validation_rows],
        ),
        test_metrics=classification_metrics(
            y_test,
            test_predictions,
            all_labels,
            languages=[row.get("language", "Unknown") for row in test_rows],
        ),
        label_schema=all_labels,
    )

    model_path = artifact_dir / "baseline.joblib"
    joblib.dump(
        {
            "classifier": classifier,
            "text_vectorizer": text_vectorizer,
            "struct_vectorizer": struct_vectorizer,
            "label_schema": all_labels,
            "task_name": task_name.value,
            "language_coverage": sorted({row.get("language", "Unknown") for row in rows}),
        },
        model_path,
    )

    summary = (
        "Baseline model trained with TF-IDF text features and structured metadata. "
        f"Classifier: {'RandomForest' if task_name == MlTaskName.RISK_SCORING else 'LogisticRegression'}."
    )
    return BaselineTrainingResult(
        metrics=metrics,
        label_schema=all_labels,
        artifact_files={"model": str(model_path)},
        summary=summary,
    )
