from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.core.config import settings
from app.models.enums import MlTaskName
from app.services.corpus.normalization import unique_tokens
from app.services.ml.registry import write_json
from app.services.ml.training.evaluation import classification_metrics, combine_split_metrics


def _split_rows(rows: list[dict[str, Any]], split_name: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split_name]


def _build_vocab(rows: list[dict[str, Any]], limit: int = 6000) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(unique_tokens(row["normalized_text"] or row["text"]))
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for token, _ in counter.most_common(limit - 2):
        vocab[token] = len(vocab)
    return vocab


def _categorical_maps(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    categories: dict[str, set[str]] = {
        "forum": set(),
        "matter_type": set(),
        "status": set(),
        "priority": set(),
        "filing_stage": set(),
        "source_view": set(),
    }
    for row in rows:
        for key in categories:
            categories[key].add(str(row["structured_features"].get(key, "")))
    return {
        key: {value: index for index, value in enumerate(sorted(values))}
        for key, values in categories.items()
    }


def _numeric_keys() -> list[str]:
    return [
        "tag_count",
        "issue_count",
        "risk_flag_count",
        "procedural_alert_count",
        "document_count",
        "note_count",
        "research_count",
        "draft_count",
        "artifact_count",
        "run_count",
        "grounded_artifact_count",
        "grounded_run_count",
        "grounding_link_count",
        "avg_document_ocr_confidence",
        "has_hearing_date",
        "text_length",
        "normalized_length",
    ]


def _encode_structured(
    row: dict[str, Any],
    *,
    category_maps: dict[str, dict[str, int]],
) -> list[float]:
    values: list[float] = []
    structured = row["structured_features"]
    for key, mapping in category_maps.items():
        one_hot = [0.0] * len(mapping)
        category_value = str(structured.get(key, ""))
        if category_value in mapping:
            one_hot[mapping[category_value]] = 1.0
        values.extend(one_hot)
    values.extend(float(structured.get(key, 0.0)) for key in _numeric_keys())
    return values


class HybridDataset(Dataset):
    def __init__(
        self,
        rows: list[dict[str, Any]],
        *,
        vocab: dict[str, int],
        category_maps: dict[str, dict[str, int]],
        label_to_id: dict[str, int],
    ) -> None:
        self.rows = rows
        self.vocab = vocab
        self.category_maps = category_maps
        self.label_to_id = label_to_id

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        tokens = unique_tokens(row["normalized_text"] or row["text"])
        token_ids = [self.vocab.get(token, 1) for token in tokens[:256]] or [0]
        return {
            "token_ids": torch.tensor(token_ids, dtype=torch.long),
            "structured": torch.tensor(
                _encode_structured(row, category_maps=self.category_maps),
                dtype=torch.float32,
            ),
            "label": torch.tensor(self.label_to_id[row["label"]], dtype=torch.long),
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    all_ids = torch.cat([item["token_ids"] for item in batch])
    offsets = []
    position = 0
    for item in batch:
        offsets.append(position)
        position += item["token_ids"].numel()
    return {
        "token_ids": all_ids,
        "offsets": torch.tensor(offsets, dtype=torch.long),
        "structured": torch.stack([item["structured"] for item in batch]),
        "labels": torch.stack([item["label"] for item in batch]),
    }


class HybridClassifier(nn.Module):
    def __init__(self, *, vocab_size: int, structured_dim: int, num_labels: int) -> None:
        super().__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, 64, mode="mean")
        self.structured = nn.Sequential(
            nn.Linear(structured_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 96),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(96, num_labels),
        )

    def forward(self, token_ids: torch.Tensor, offsets: torch.Tensor, structured: torch.Tensor) -> torch.Tensor:
        text_state = self.embedding(token_ids, offsets)
        structured_state = self.structured(structured)
        return self.classifier(torch.cat([text_state, structured_state], dim=1))


@dataclass(slots=True)
class HybridTrainingResult:
    metrics: dict[str, Any]
    label_schema: list[str]
    artifact_files: dict[str, str]
    summary: str


def _predict_rows(
    model: HybridClassifier,
    rows: list[dict[str, Any]],
    *,
    vocab: dict[str, int],
    category_maps: dict[str, dict[str, int]],
    label_schema: list[str],
) -> list[str]:
    if not rows:
        return []
    dataset = HybridDataset(rows, vocab=vocab, category_maps=category_maps, label_to_id={label: index for index, label in enumerate(label_schema)})
    loader = DataLoader(dataset, batch_size=8, shuffle=False, collate_fn=_collate)
    predictions: list[str] = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            logits = model(batch["token_ids"], batch["offsets"], batch["structured"])
            indices = torch.argmax(logits, dim=1).tolist()
            predictions.extend(label_schema[index] for index in indices)
    return predictions


def train_hybrid_model(
    *,
    task_name: MlTaskName,
    rows: list[dict[str, Any]],
    artifact_dir: Path,
) -> HybridTrainingResult:
    train_rows = _split_rows(rows, "train")
    validation_rows = _split_rows(rows, "validation")
    test_rows = _split_rows(rows, "test")
    label_schema = sorted({row["label"] for row in rows})
    label_to_id = {label: index for index, label in enumerate(label_schema)}
    vocab = _build_vocab(train_rows or rows)
    category_maps = _categorical_maps(rows)
    structured_dim = sum(len(mapping) for mapping in category_maps.values()) + len(_numeric_keys())

    model = HybridClassifier(
        vocab_size=len(vocab),
        structured_dim=structured_dim,
        num_labels=len(label_schema),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    dataset = HybridDataset(train_rows, vocab=vocab, category_maps=category_maps, label_to_id=label_to_id)
    loader = DataLoader(
        dataset,
        batch_size=settings.ml_hybrid_batch_size,
        shuffle=True,
        collate_fn=_collate,
    )
    model.train()
    for _ in range(settings.ml_hybrid_epochs):
        for batch in loader:
            optimizer.zero_grad()
            logits = model(batch["token_ids"], batch["offsets"], batch["structured"])
            loss = loss_fn(logits, batch["labels"])
            loss.backward()
            optimizer.step()

    train_predictions = _predict_rows(model, train_rows, vocab=vocab, category_maps=category_maps, label_schema=label_schema)
    validation_predictions = _predict_rows(model, validation_rows, vocab=vocab, category_maps=category_maps, label_schema=label_schema)
    test_predictions = _predict_rows(model, test_rows, vocab=vocab, category_maps=category_maps, label_schema=label_schema)
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

    model_path = artifact_dir / "hybrid_model.pt"
    torch.save(model.state_dict(), model_path)
    preprocessor_path = artifact_dir / "hybrid_preprocessor.json"
    write_json(
        preprocessor_path,
        {
            "taskName": task_name.value,
            "labelSchema": label_schema,
            "vocab": vocab,
            "categoryMaps": category_maps,
            "structuredDim": structured_dim,
            "languageCoverage": sorted({row.get("language", "Unknown") for row in rows}),
        },
    )
    return HybridTrainingResult(
        metrics=metrics,
        label_schema=label_schema,
        artifact_files={
            "model": str(model_path),
            "preprocessor": str(preprocessor_path),
        },
        summary="Hybrid PyTorch model trained with token embeddings plus structured legal-matter metadata.",
    )
