from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset

from app.services.ml.training.transformer_runtime import ensure_text_only_transformers_runtime

ensure_text_only_transformers_runtime()
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.core.config import settings
from app.models.enums import MlTaskName
from app.services.ml.registry import write_json
from app.services.ml.training.evaluation import classification_metrics, combine_split_metrics


def _split_rows(rows: list[dict[str, Any]], split_name: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split_name]


class TransformerRows(Dataset):
    def __init__(self, rows: list[dict[str, Any]], *, label_to_id: dict[str, int], tokenizer) -> None:
        self.rows = rows
        self.label_to_id = label_to_id
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.rows[index]
        encoded = self.tokenizer(
            row["text"],
            truncation=True,
            padding="max_length",
            max_length=settings.ml_transformer_max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.label_to_id[row["label"]], dtype=torch.long),
        }


@dataclass(slots=True)
class TransformerTrainingResult:
    metrics: dict[str, Any]
    label_schema: list[str]
    artifact_files: dict[str, str]
    summary: str


def _predict_rows(model, dataset: TransformerRows, label_schema: list[str]) -> list[str]:
    if len(dataset) == 0:
        return []
    loader = DataLoader(dataset, batch_size=settings.ml_transformer_batch_size, shuffle=False)
    outputs: list[str] = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            logits = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            ).logits
            predictions = torch.argmax(logits, dim=1).tolist()
            outputs.extend(label_schema[index] for index in predictions)
    return outputs


def train_transformer_model(
    *,
    task_name: MlTaskName,
    rows: list[dict[str, Any]],
    artifact_dir: Path,
    model_name: str | None = None,
) -> TransformerTrainingResult:
    checkpoint = model_name or settings.ml_transformer_model_name
    train_rows = _split_rows(rows, "train")
    validation_rows = _split_rows(rows, "validation")
    test_rows = _split_rows(rows, "test")
    label_schema = sorted({row["label"] for row in rows})
    label_to_id = {label: index for index, label in enumerate(label_schema)}

    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint,
        num_labels=len(label_schema),
        ignore_mismatched_sizes=True,
    )

    train_dataset = TransformerRows(train_rows, label_to_id=label_to_id, tokenizer=tokenizer)
    validation_dataset = TransformerRows(validation_rows, label_to_id=label_to_id, tokenizer=tokenizer)
    test_dataset = TransformerRows(test_rows, label_to_id=label_to_id, tokenizer=tokenizer)
    train_loader = DataLoader(
        train_dataset,
        batch_size=settings.ml_transformer_batch_size,
        shuffle=True,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    model.train()
    for _ in range(settings.ml_transformer_epochs):
        for batch in train_loader:
            optimizer.zero_grad()
            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                labels=batch["labels"],
            )
            outputs.loss.backward()
            optimizer.step()

    train_predictions = _predict_rows(model, train_dataset, label_schema)
    validation_predictions = _predict_rows(model, validation_dataset, label_schema)
    test_predictions = _predict_rows(model, test_dataset, label_schema)
    metrics = combine_split_metrics(
        train_metrics=classification_metrics(
            [row["label"] for row in train_rows],
            train_predictions,
            label_schema,
            languages=[row.get("language", "Unknown") for row in train_rows],
        ),
        validation_metrics=classification_metrics(
            [row["label"] for row in validation_rows],
            validation_predictions,
            label_schema,
            languages=[row.get("language", "Unknown") for row in validation_rows],
        ),
        test_metrics=classification_metrics(
            [row["label"] for row in test_rows],
            test_predictions,
            label_schema,
            languages=[row.get("language", "Unknown") for row in test_rows],
        ),
        label_schema=label_schema,
    )

    model.save_pretrained(artifact_dir)
    tokenizer.save_pretrained(artifact_dir)
    config_path = artifact_dir / "transformer_config.json"
    write_json(
        config_path,
        {
            "taskName": task_name.value,
            "checkpoint": checkpoint,
            "labelSchema": label_schema,
            "languageCoverage": sorted({row.get("language", "Unknown") for row in rows}),
        },
    )
    return TransformerTrainingResult(
        metrics=metrics,
        label_schema=label_schema,
        artifact_files={
            "model_dir": str(artifact_dir),
            "config": str(config_path),
        },
        summary=f"Multilingual transformer classifier trained from checkpoint `{checkpoint}`.",
    )
