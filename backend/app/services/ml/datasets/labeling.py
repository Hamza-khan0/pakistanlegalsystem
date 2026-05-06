from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.models.enums import MlTaskName


@dataclass(slots=True)
class LabelInfo:
    label: str
    label_source: str
    confidence: float


def _labels_path() -> Path:
    return Path(settings.crawl_seed_dir).parent / "ml_labels.json"


def load_seed_labels() -> dict[str, dict[str, str]]:
    path = _labels_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_case_label(case_id: str, task_name: MlTaskName) -> LabelInfo | None:
    labels = load_seed_labels().get(case_id)
    if not labels:
        return None
    raw_label = labels.get(task_name.value)
    if not raw_label:
        return None
    return LabelInfo(
        label=raw_label,
        label_source=str(labels.get("label_source") or "manual_seed"),
        confidence=0.92,
    )
