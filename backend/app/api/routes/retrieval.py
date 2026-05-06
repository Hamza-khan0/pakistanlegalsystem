from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import ChamberTaskType, GroundingUsageType, RetrievalMode
from app.schemas.evaluation import RetrievalBenchmarkRunRead
from app.schemas.legal_sources import GroundingSourceRead
from app.schemas.retrieval import (
    EmbeddingIndexRead,
    RetrievalBuildRequest,
    RetrievalLeaderboardEntry,
    RetrievalLeaderboardRead,
    RetrievalSearchRead,
    RetrievalSearchRequest,
    RunGroundingDiagnosticsRead,
)
from app.services.evaluation.retrieval_benchmark import (
    get_retrieval_benchmark,
    list_retrieval_benchmarks,
    run_retrieval_benchmark,
)
from app.services.knowledge.hybrid_retrieval import (
    hybrid_search_legal_sources,
    retrieval_leaderboard_snapshot,
    semantic_search_legal_sources,
)
from app.services.knowledge.reranking import reranker_metadata
from app.services.knowledge.semantic_index import build_semantic_index, get_index_metadata
from app.services.runs import get_run_or_none
from app.services.serializers import serialize_embedding_index, serialize_grounding_link
from app.utils.http import not_found

router = APIRouter()


def _serialize_retrieved_source(source) -> GroundingSourceRead:
    return GroundingSourceRead(
        source_id=source.source_id,
        chunk_id=source.chunk_id,
        title=source.title,
        short_title=source.short_title,
        citation_label=source.citation_label,
        source_type=source.source_type,
        category=source.category,
        act_name=source.act_name,
        section_label=source.section_label,
        language=source.language,
        source_origin=source.source_origin,
        source_url=source.source_url,
        excerpt=source.excerpt,
        relevance_score=source.relevance_score,
        lexical_score=source.lexical_score,
        semantic_score=source.semantic_score,
        rerank_score=source.rerank_score,
        retrieval_mode=source.retrieval_mode,
        explanation=source.explanation,
        usage_type=GroundingUsageType.RETRIEVED,
    )


@router.post("/retrieval/index/build", response_model=EmbeddingIndexRead)
def build_index(
    payload: RetrievalBuildRequest = Body(default=RetrievalBuildRequest()),
    db: Session = Depends(get_db),
) -> EmbeddingIndexRead:
    metadata = build_semantic_index(db, model_name=payload.model_name)
    return serialize_embedding_index(metadata)


@router.get("/retrieval/index/status", response_model=EmbeddingIndexRead | None)
def get_index_status(db: Session = Depends(get_db)) -> EmbeddingIndexRead | None:
    metadata = get_index_metadata(db)
    if metadata is None:
        return None
    return serialize_embedding_index(metadata)


@router.post("/retrieval/search", response_model=RetrievalSearchRead)
def semantic_search(
    payload: RetrievalSearchRequest,
    db: Session = Depends(get_db),
) -> RetrievalSearchRead:
    task_type = ChamberTaskType(payload.task_type) if payload.task_type else ChamberTaskType.RESEARCH_MEMO
    bundle = semantic_search_legal_sources(
        db,
        query=payload.query,
        task_type=task_type,
        limit=payload.limit,
        language=payload.language,
    )
    return RetrievalSearchRead(
        query=bundle.query,
        mode=RetrievalMode.SEMANTIC,
        status=bundle.status,
        summary=bundle.summary,
        diagnostics={"taskType": task_type.value, "reranking": reranker_metadata()},
        sources=[_serialize_retrieved_source(source) for source in bundle.sources],
    )


@router.post("/retrieval/hybrid-search", response_model=RetrievalSearchRead)
def hybrid_search(
    payload: RetrievalSearchRequest,
    db: Session = Depends(get_db),
) -> RetrievalSearchRead:
    task_type = ChamberTaskType(payload.task_type) if payload.task_type else ChamberTaskType.RESEARCH_MEMO
    bundle = hybrid_search_legal_sources(
        db,
        query=payload.query,
        task_type=task_type,
        limit=payload.limit,
        language=payload.language,
    )
    return RetrievalSearchRead(
        query=bundle.query,
        mode=RetrievalMode.HYBRID,
        status=bundle.status,
        summary=bundle.summary,
        diagnostics={
            "taskType": task_type.value,
            "reranking": reranker_metadata(),
            "queryLanguage": payload.language,
        },
        sources=[_serialize_retrieved_source(source) for source in bundle.sources],
    )


@router.get("/retrieval/leaderboard", response_model=RetrievalLeaderboardRead)
def get_retrieval_leaderboard(db: Session = Depends(get_db)) -> RetrievalLeaderboardRead:
    snapshot = retrieval_leaderboard_snapshot(db)
    return RetrievalLeaderboardRead(
        generated_at=datetime.now(timezone.utc),
        entries=[
            RetrievalLeaderboardEntry(
                mode=item.mode,
                query=item.query,
                top_labels=item.top_labels,
                source_type_mix=item.source_type_mix,
                average_score=item.average_score,
                diagnostics=item.diagnostics,
            )
            for item in snapshot
        ],
    )


@router.post("/retrieval/evaluate", response_model=RetrievalLeaderboardRead)
def evaluate_retrieval(db: Session = Depends(get_db)) -> RetrievalLeaderboardRead:
    snapshot = retrieval_leaderboard_snapshot(db)
    return RetrievalLeaderboardRead(
        generated_at=datetime.now(timezone.utc),
        entries=[
            RetrievalLeaderboardEntry(
                mode=item.mode,
                query=item.query,
                top_labels=item.top_labels,
                source_type_mix=item.source_type_mix,
                average_score=item.average_score,
                diagnostics=item.diagnostics,
            )
            for item in snapshot
        ],
    )


@router.post("/retrieval/benchmarks/run", response_model=RetrievalBenchmarkRunRead, status_code=201)
def run_benchmark(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
) -> RetrievalBenchmarkRunRead:
    name = payload.get("name") if isinstance(payload, dict) else None
    top_k = int(payload.get("topK", 5)) if isinstance(payload, dict) else 5
    return RetrievalBenchmarkRunRead(**run_retrieval_benchmark(db, name=name, top_k=top_k))


@router.get("/retrieval/benchmarks", response_model=list[RetrievalBenchmarkRunRead])
def get_benchmarks() -> list[RetrievalBenchmarkRunRead]:
    return [RetrievalBenchmarkRunRead(**item) for item in list_retrieval_benchmarks()]


@router.get("/retrieval/benchmarks/{benchmark_id}", response_model=RetrievalBenchmarkRunRead)
def get_benchmark(benchmark_id: str) -> RetrievalBenchmarkRunRead:
    benchmark = get_retrieval_benchmark(benchmark_id)
    if benchmark is None:
        raise not_found("Retrieval benchmark not found.")
    return RetrievalBenchmarkRunRead(**benchmark)


@router.get("/runs/{run_id}/grounding/diagnostics", response_model=RunGroundingDiagnosticsRead)
def get_run_grounding_diagnostics(run_id: str, db: Session = Depends(get_db)) -> RunGroundingDiagnosticsRead:
    run = get_run_or_none(db, run_id)
    if not run:
        raise not_found("Run not found.")
    return RunGroundingDiagnosticsRead(
        run_id=run.id,
        retrieval_mode=str(run.metadata_json.get("retrievalMode") or "Lexical"),
        grounding_status=str(run.metadata_json.get("legalGroundingStatus") or "Retrieval not used"),
        diagnostics={
            "query": run.metadata_json.get("legalRetrievalQuery"),
            "mode": run.metadata_json.get("retrievalMode"),
            "weights": run.metadata_json.get("retrievalWeights", {}),
            "semanticIndex": run.metadata_json.get("semanticIndex", {}),
        },
        sources=[serialize_grounding_link(link) for link in run.grounding_links],
    )
