from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def tier1_root() -> Path:
    path = Path(settings.tier1_data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def manual_import_dir() -> Path:
    path = tier1_root() / "manual_import"
    path.mkdir(parents=True, exist_ok=True)
    return path


def raw_dir() -> Path:
    path = Path(settings.tier1_raw_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir() -> Path:
    path = Path(settings.tier1_processed_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def label_audit_dir() -> Path:
    path = Path(settings.tier1_label_audit_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def training_export_dir() -> Path:
    path = Path(settings.training_export_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def kaggle_config_dir() -> Path:
    path = tier1_root() / ".kaggle"
    path.mkdir(parents=True, exist_ok=True)
    return path
