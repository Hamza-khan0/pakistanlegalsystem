from fastapi import APIRouter

from app.api.routes import (
    agent_logs,
    cases,
    corpus,
    crawl,
    dashboard,
    documents,
    drafts,
    evaluation,
    intelligence,
    legal_sources,
    ml,
    retrieval,
    notes,
    research,
    runs,
    tier1,
    timeline,
)

api_router = APIRouter()
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(crawl.router, tags=["crawl"])
api_router.include_router(corpus.router, tags=["corpus"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(timeline.router, tags=["timeline"])
api_router.include_router(notes.router, tags=["notes"])
api_router.include_router(research.router, tags=["research"])
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(agent_logs.router, tags=["agent-logs"])
api_router.include_router(intelligence.router, tags=["intelligence"])
api_router.include_router(runs.router, tags=["runs"])
api_router.include_router(legal_sources.router, tags=["legal-sources"])
api_router.include_router(retrieval.router, tags=["retrieval"])
api_router.include_router(ml.router, tags=["ml"])
api_router.include_router(evaluation.router, tags=["evaluation"])
api_router.include_router(tier1.router, tags=["tier1"])
