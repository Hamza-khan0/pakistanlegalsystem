from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, settings
from app.models.tier1_document import Tier1Document
from app.services.tier1_data.file_discovery import discover_supported_files
from app.services.tier1_data.label_extractor import extract_labels_for_documents
from app.services.tier1_data.normalizer import NormalizedTier1Record, records_from_file
from app.services.tier1_data.paths import kaggle_config_dir, manual_import_dir, raw_dir


SOURCE_CONFIG_PATH = PROJECT_ROOT / "backend" / "app" / "seed" / "tier1_sources.json"
SAMPLE_IMPORT_PATH = PROJECT_ROOT / "backend" / "app" / "seed" / "tier1_manual_import"


def load_source_configs() -> list[dict[str, Any]]:
    if not SOURCE_CONFIG_PATH.exists():
        return []
    return json.loads(SOURCE_CONFIG_PATH.read_text(encoding="utf-8"))


def ensure_manual_sample_if_empty() -> bool:
    target = manual_import_dir()
    if discover_supported_files(target):
        return False
    if not SAMPLE_IMPORT_PATH.exists():
        return False
    for source_file in SAMPLE_IMPORT_PATH.iterdir():
        if source_file.is_file():
            shutil.copy2(source_file, target / source_file.name)
    return True


def _find_existing_document(db: Session, record: NormalizedTier1Record) -> Tier1Document | None:
    return db.scalar(
        select(Tier1Document).where(
            Tier1Document.source_type == record.source_type,
            Tier1Document.source_name == record.source_name,
            or_(
                Tier1Document.external_id == record.external_id,
                Tier1Document.file_path == record.file_path,
            ),
        )
    )


def _upsert_record(db: Session, record: NormalizedTier1Record) -> tuple[Tier1Document, bool]:
    document = _find_existing_document(db, record)
    created = document is None
    if document is None:
        document = Tier1Document(
            source_type=record.source_type,
            source_name=record.source_name,
            external_id=record.external_id,
        )
    document.file_path = record.file_path
    document.title = record.title
    document.raw_text = record.raw_text
    document.normalized_text = record.normalized_text
    document.language = record.language
    document.document_type = record.document_type
    document.court = record.court
    document.date = record.date
    document.citation = record.citation
    document.case_number = record.case_number
    document.parties = record.parties
    document.metadata_json = record.metadata
    document.import_status = "Imported"
    db.add(document)
    return document, created


def import_directory(
    db: Session,
    directory: str | Path,
    *,
    source_type: str,
    source_name: str,
) -> dict[str, Any]:
    files = discover_supported_files(directory)
    imported = 0
    updated = 0
    skipped = 0
    warnings: list[str] = []
    documents: list[Tier1Document] = []

    for file_path in files:
        records, file_warnings = records_from_file(
            file_path,
            source_type=source_type,
            source_name=source_name,
        )
        warnings.extend(file_warnings)
        if not records:
            skipped += 1
            continue
        for record in records:
            document, created = _upsert_record(db, record)
            documents.append(document)
            imported += 1 if created else 0
            updated += 0 if created else 1

    db.commit()
    for document in documents:
        db.refresh(document)
    label_count = extract_labels_for_documents(db, documents)
    return {
        "status": "success" if documents else "warning",
        "message": (
            f"Imported or updated {len(documents)} Tier 1 documents."
            if documents
            else "No supported Tier 1 documents were found."
        ),
        "sourceType": source_type,
        "sourceName": source_name,
        "importedCount": imported,
        "updatedCount": updated,
        "skippedCount": skipped,
        "labelCount": label_count,
        "warnings": warnings,
        "metadataJson": {
            "directory": str(directory),
            "fileCount": len(files),
            "languageCounts": dict(Counter(document.language for document in documents)),
        },
    }


def import_local(db: Session, *, include_seed_sample: bool = True) -> dict[str, Any]:
    seeded = ensure_manual_sample_if_empty() if include_seed_sample else False
    result = import_directory(
        db,
        manual_import_dir(),
        source_type="local",
        source_name="manual_import",
    )
    if seeded:
        result["warnings"] = [
            "Manual import folder was empty, so a small seeded Tier 1 sample was copied for verification.",
            *result.get("warnings", []),
        ]
        result["metadataJson"] = {**result.get("metadataJson", {}), "seedSampleUsed": True}
    return result


def _enabled_configs(source_type: str) -> list[dict[str, Any]]:
    return [
        item
        for item in load_source_configs()
        if item.get("enabled", True) and item.get("source_type") == source_type
    ]


def _write_kaggle_config() -> Path:
    config_dir = kaggle_config_dir()
    config_path = config_dir / "kaggle.json"
    config_path.write_text(
        json.dumps({"username": settings.kaggle_username, "key": settings.kaggle_key}),
        encoding="utf-8",
    )
    try:
        config_path.chmod(0o600)
    except OSError:
        pass
    return config_path


def import_kaggle(db: Session) -> dict[str, Any]:
    if not settings.kaggle_username or not settings.kaggle_key:
        return {
            "status": "warning",
            "message": "Kaggle credentials not configured",
            "sourceType": "kaggle",
            "sourceName": "configured_kaggle_sources",
            "importedCount": 0,
            "updatedCount": 0,
            "skippedCount": 0,
            "labelCount": 0,
            "warnings": ["Set KAGGLE_USERNAME and KAGGLE_KEY to enable Kaggle import."],
            "metadataJson": {},
        }

    configs = _enabled_configs("kaggle")
    if not configs:
        return {
            "status": "warning",
            "message": "No enabled Kaggle sources configured",
            "sourceType": "kaggle",
            "sourceName": "configured_kaggle_sources",
            "importedCount": 0,
            "updatedCount": 0,
            "skippedCount": 0,
            "labelCount": 0,
            "warnings": [],
            "metadataJson": {},
        }

    _write_kaggle_config()
    os.environ["KAGGLE_CONFIG_DIR"] = str(kaggle_config_dir())
    totals = Counter()
    warnings: list[str] = []
    for config in configs:
        slug = str(config.get("dataset_slug") or "")
        name = str(config.get("name") or slug.replace("/", "_"))
        output_dir = raw_dir() / "kaggle" / name
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "-m",
            "kaggle",
            "datasets",
            "download",
            "-d",
            slug,
            "-p",
            str(output_dir),
            "--unzip",
        ]
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=300)
        except Exception as exc:
            warnings.append(f"{name}: Kaggle download could not start: {exc}")
            continue
        if completed.returncode != 0:
            warnings.append(f"{name}: Kaggle download failed. Install kaggle package and verify dataset access.")
            continue
        result = import_directory(db, output_dir, source_type="kaggle", source_name=name)
        totals.update(
            {
                "imported": int(result["importedCount"]),
                "updated": int(result["updatedCount"]),
                "skipped": int(result["skippedCount"]),
                "labels": int(result["labelCount"]),
            }
        )
        warnings.extend(result.get("warnings", []))

    return {
        "status": "success" if totals["imported"] or totals["updated"] else "warning",
        "message": "Kaggle import completed without exposing credentials.",
        "sourceType": "kaggle",
        "sourceName": "configured_kaggle_sources",
        "importedCount": totals["imported"],
        "updatedCount": totals["updated"],
        "skippedCount": totals["skipped"],
        "labelCount": totals["labels"],
        "warnings": warnings,
        "metadataJson": {"sourceCount": len(configs)},
    }


def import_huggingface(db: Session) -> dict[str, Any]:
    if not settings.hf_token:
        return {
            "status": "warning",
            "message": "Hugging Face token not configured",
            "sourceType": "huggingface",
            "sourceName": "configured_huggingface_sources",
            "importedCount": 0,
            "updatedCount": 0,
            "skippedCount": 0,
            "labelCount": 0,
            "warnings": ["Set HF_TOKEN to enable Hugging Face import."],
            "metadataJson": {},
        }
    try:
        from datasets import load_dataset  # type: ignore
    except Exception:
        return {
            "status": "warning",
            "message": "Hugging Face datasets package is not installed",
            "sourceType": "huggingface",
            "sourceName": "configured_huggingface_sources",
            "importedCount": 0,
            "updatedCount": 0,
            "skippedCount": 0,
            "labelCount": 0,
            "warnings": ["Install the optional datasets package to enable HF import."],
            "metadataJson": {},
        }

    totals = Counter()
    warnings: list[str] = []
    for config in _enabled_configs("huggingface"):
        dataset_id = str(config.get("dataset_id") or "")
        name = str(config.get("name") or dataset_id.replace("/", "_"))
        output_dir = raw_dir() / "huggingface" / name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "hf_export.jsonl"
        try:
            dataset = load_dataset(dataset_id, token=settings.hf_token)
            with output_file.open("w", encoding="utf-8") as handle:
                for split_name, split in dataset.items():
                    for index, row in enumerate(split):
                        payload = dict(row)
                        payload.setdefault("id", f"{split_name}:{index}")
                        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as exc:
            warnings.append(f"{name}: Hugging Face import failed: {exc}")
            continue
        result = import_directory(db, output_dir, source_type="huggingface", source_name=name)
        totals.update(
            {
                "imported": int(result["importedCount"]),
                "updated": int(result["updatedCount"]),
                "skipped": int(result["skippedCount"]),
                "labels": int(result["labelCount"]),
            }
        )
        warnings.extend(result.get("warnings", []))

    return {
        "status": "success" if totals["imported"] or totals["updated"] else "warning",
        "message": "Hugging Face import completed.",
        "sourceType": "huggingface",
        "sourceName": "configured_huggingface_sources",
        "importedCount": totals["imported"],
        "updatedCount": totals["updated"],
        "skippedCount": totals["skipped"],
        "labelCount": totals["labels"],
        "warnings": warnings,
        "metadataJson": {},
    }
