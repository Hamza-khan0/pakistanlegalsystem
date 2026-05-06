from __future__ import annotations

from statistics import mean
from typing import Any

from app.models.case import Case
from app.models.chamber_run import ChamberRun


def evaluate_run_quality(run: ChamberRun) -> dict[str, Any]:
    critic_step = next((step for step in run.steps if step.agent_name == "Critic Agent"), None)
    critic_structured = critic_step.structured_json if critic_step else {}
    unsupported = critic_structured.get("unsupportedAssumptions", [])
    critic_flags = critic_structured.get("structuralWeaknesses", [])
    procedural_dependencies = critic_structured.get("proceduralDependencies", [])
    memory_usage_count = len(run.metadata_json.get("memorySources", [])) if isinstance(run.metadata_json.get("memorySources"), list) else 0
    retrieved_sources = len(run.grounding_links)
    relied_sources = sum(1 for link in run.grounding_links if link.usage_type.value in {"Relied On", "Cited"})

    if retrieved_sources >= 4:
        grounding_strength = "strong"
    elif retrieved_sources >= 2:
        grounding_strength = "moderate"
    elif retrieved_sources == 1:
        grounding_strength = "partial"
    else:
        grounding_strength = "weak"

    recommendations: list[str] = []
    if not retrieved_sources:
        recommendations.append("Add stronger legal retrieval before relying on the chamber output externally.")
    if unsupported:
        recommendations.append("Review unsupported assumptions surfaced by the critic before using the output.")
    if procedural_dependencies:
        recommendations.append("Resolve procedural dependencies noted by the critic or procedural agent.")

    return {
        "runId": run.id,
        "caseId": run.case_id,
        "status": run.status.value,
        "retrievalMode": str(run.metadata_json.get("retrievalMode") or "Lexical"),
        "sourceCountRetrieved": retrieved_sources,
        "sourceCountReliedOn": relied_sources,
        "groundingStrength": grounding_strength,
        "criticFlags": critic_flags if isinstance(critic_flags, list) else [],
        "unsupportedClaimWarnings": unsupported if isinstance(unsupported, list) else [],
        "proceduralDependencies": procedural_dependencies if isinstance(procedural_dependencies, list) else [],
        "memoryUsageCount": memory_usage_count,
        "finalConfidenceScore": run.confidence_score,
        "recommendations": recommendations,
    }


def evaluate_case_quality(case: Case) -> dict[str, Any]:
    run_qualities = [evaluate_run_quality(run) for run in case.chamber_runs]
    if run_qualities:
        confidence_values = [
            quality["finalConfidenceScore"]
            for quality in run_qualities
            if isinstance(quality["finalConfidenceScore"], (float, int))
        ]
        average_confidence = mean(confidence_values) if confidence_values else None
        latest = sorted(case.chamber_runs, key=lambda run: run.started_at, reverse=True)[0]
        latest_quality = evaluate_run_quality(latest)
    else:
        average_confidence = None
        latest_quality = None

    all_warnings = []
    for quality in run_qualities:
        all_warnings.extend(quality["unsupportedClaimWarnings"])

    return {
        "caseId": case.id,
        "recentRunCount": len(run_qualities),
        "averageRunConfidence": round(float(average_confidence), 4) if average_confidence is not None else None,
        "latestRunQuality": latest_quality,
        "groundedRunCount": sum(1 for quality in run_qualities if quality["sourceCountRetrieved"] > 0),
        "criticalWarningCount": len(all_warnings),
        "qualityWarnings": all_warnings[:6],
    }
