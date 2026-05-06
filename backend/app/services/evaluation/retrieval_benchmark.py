from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import ChamberTaskType
from app.services.knowledge.hybrid_retrieval import hybrid_search_legal_sources, semantic_search_legal_sources
from app.services.knowledge.retrieval import search_legal_sources
from app.services.knowledge.reranking import reranker_metadata
from app.services.ml.registry import benchmark_dir, benchmarks_root, read_json, write_json


def _queries_path() -> Path:
    return Path(__file__).resolve().parents[2] / "seed" / "benchmark_queries.json"


def load_benchmark_queries() -> list[dict[str, Any]]:
    path = _queries_path()
    if not path.exists():
        return []
    return read_json(path)


def _expected_metrics(result_labels: list[str], expected_labels: list[str]) -> tuple[int, float | None]:
    if not expected_labels:
        return 0, None
    matches = [index for index, label in enumerate(result_labels, start=1) if label in expected_labels]
    hit = 1 if matches else 0
    reciprocal_rank = round(1 / matches[0], 4) if matches else 0.0
    return hit, reciprocal_rank


def _run_mode(
    db: Session,
    *,
    query: str,
    task_type: ChamberTaskType,
    language: str | None,
    mode: str,
    top_k: int,
) -> dict[str, Any]:
    if mode == "Lexical":
        bundle = search_legal_sources(db, query=query, task_type=task_type, limit=top_k, language=language)
    elif mode == "Semantic":
        bundle = semantic_search_legal_sources(db, query=query, task_type=task_type, limit=top_k, language=language)
    else:
        bundle = hybrid_search_legal_sources(db, query=query, task_type=task_type, limit=top_k, language=language)

    results = [
        {
            "sourceId": source.source_id,
            "citationLabel": source.citation_label or source.title,
            "sourceType": source.source_type,
            "language": source.language,
            "score": source.relevance_score,
            "lexicalScore": source.lexical_score,
            "semanticScore": source.semantic_score,
            "rerankScore": source.rerank_score,
            "explanation": source.explanation,
        }
        for source in bundle.sources
    ]
    score_values = [float(source.relevance_score or 0.0) for source in bundle.sources]
    return {
        "status": bundle.status,
        "summary": bundle.summary,
        "results": results,
        "averageScore": round(sum(score_values) / len(score_values), 4) if score_values else 0.0,
        "sourceTypeMix": dict(Counter(item["sourceType"] for item in results)),
        "sourceLanguageMix": dict(Counter(item["language"] for item in results)),
    }


def run_retrieval_benchmark(
    db: Session,
    *,
    name: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    benchmark_id = uuid4().hex
    queries = load_benchmark_queries()
    results: list[dict[str, Any]] = []
    mode_metrics: dict[str, list[dict[str, float]]] = {"Lexical": [], "Semantic": [], "Hybrid": []}

    for query_record in queries:
        query = str(query_record.get("query") or "").strip()
        if not query:
            continue
        task_type = ChamberTaskType(str(query_record.get("taskType") or ChamberTaskType.RESEARCH_MEMO.value))
        expected_labels = [str(item) for item in query_record.get("expectedLabels", []) if str(item).strip()]
        language = str(query_record.get("language")).strip() if query_record.get("language") else None

        for mode in ("Lexical", "Semantic", "Hybrid"):
            mode_payload = _run_mode(
                db,
                query=query,
                task_type=task_type,
                language=language,
                mode=mode,
                top_k=top_k,
            )
            result_labels = [item["citationLabel"] for item in mode_payload["results"]]
            hit_at_k, reciprocal_rank = _expected_metrics(result_labels, expected_labels)
            recall = round(hit_at_k / max(len(expected_labels), 1), 4) if expected_labels else None
            metrics = {
                "hitAtK": hit_at_k,
                "recallAtK": recall,
                "mrr": reciprocal_rank,
                "averageScore": mode_payload["averageScore"],
                "heuristic": not bool(expected_labels),
            }
            mode_metrics[mode].append(
                {
                    "hitAtK": float(hit_at_k),
                    "mrr": float(reciprocal_rank or 0.0),
                    "averageScore": float(mode_payload["averageScore"]),
                }
            )
            results.append(
                {
                    "query": query,
                    "taskType": task_type.value,
                    "mode": mode,
                    "topK": top_k,
                    "expectedLabels": expected_labels,
                    "metricsJson": metrics,
                    "resultsJson": mode_payload["results"],
                    "diagnostics": {
                        "status": mode_payload["status"],
                        "summary": mode_payload["summary"],
                        "sourceTypeMix": mode_payload["sourceTypeMix"],
                        "sourceLanguageMix": mode_payload["sourceLanguageMix"],
                        "reranking": reranker_metadata(),
                    },
                }
            )

    aggregate = {}
    for mode, entries in mode_metrics.items():
        if entries:
            aggregate[mode] = {
                "averageHitAtK": round(sum(item["hitAtK"] for item in entries) / len(entries), 4),
                "averageMrr": round(sum(item["mrr"] for item in entries) / len(entries), 4),
                "averageScore": round(sum(item["averageScore"] for item in entries) / len(entries), 4),
            }
        else:
            aggregate[mode] = {"averageHitAtK": 0.0, "averageMrr": 0.0, "averageScore": 0.0}

    payload = {
        "id": benchmark_id,
        "name": name or "Phase 9 retrieval benchmark",
        "retrievalModesCompared": ["Lexical", "Semantic", "Hybrid"],
        "queryCount": len({item["query"] for item in results}),
        "metricsJson": {
            "aggregate": aggregate,
            "heuristicEvaluation": True,
            "reranking": reranker_metadata(),
        },
        "results": results,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    write_json(benchmark_dir(benchmark_id) / "benchmark.json", payload)
    return payload


def list_retrieval_benchmarks() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(benchmarks_root().glob("*/benchmark.json"), reverse=True):
        payload = read_json(path)
        runs.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "retrievalModesCompared": payload["retrievalModesCompared"],
                "queryCount": payload["queryCount"],
                "metricsJson": payload["metricsJson"],
                "createdAt": payload["createdAt"],
            }
        )
    return runs


def get_retrieval_benchmark(benchmark_id: str) -> dict[str, Any] | None:
    path = benchmark_dir(benchmark_id) / "benchmark.json"
    if not path.exists():
        return None
    return read_json(path)
