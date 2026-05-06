from __future__ import annotations

from collections import Counter

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.memory.retrieval import rank_memory_sources
from app.services.orchestration.schemas import CaseMemoryBundle


def build_case_memory(
    case: Case,
    *,
    task_type: ChamberTaskType,
    instruction: str,
) -> CaseMemoryBundle:
    sources = rank_memory_sources(
        case,
        task_type=task_type,
        instruction=instruction,
    )

    counts = Counter(source.source_type for source in sources)
    summary_parts = []
    if counts:
        summary_parts.append(
            ", ".join(f"{count} {source_type.lower()}" for source_type, count in counts.items())
        )

    if case.chamber_runs:
        summary_parts.append("prior chamber runs are available for continuity")
    if case.intelligence_artifacts:
        summary_parts.append("stored intelligence artifacts can be reused")
    if case.documents:
        summary_parts.append(
            f"{sum(1 for document in case.documents if document.extracted_text)} processed document previews are available"
        )

    summary = (
        "Case memory assembled from "
        + "; ".join(summary_parts)
        if summary_parts
        else "No substantial prior matter memory is available yet."
    )

    return CaseMemoryBundle(
        summary=summary,
        sources=sources,
        source_artifact_ids=[
            source.source_id for source in sources if source.source_type == "Intelligence Artifact"
        ],
        source_document_ids=[
            source.source_id for source in sources if source.source_type == "Document"
        ],
        source_run_ids=[
            source.source_id for source in sources if source.source_type == "Chamber Run"
        ],
    )
