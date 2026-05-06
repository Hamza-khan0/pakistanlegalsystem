from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_log import AgentRunLog
from app.models.case import Case
from app.models.chamber_run import ChamberRun
from app.models.chamber_run_step import ChamberRunStep
from app.models.draft import Draft
from app.models.enums import (
    AgentRunStatus,
    ChamberRunStatus,
    ChamberRunStepStatus,
    ChamberTaskType,
    DraftStatus,
    GroundingUsageType,
    IntelligenceArtifactType,
    IntelligenceStatus,
    ResearchStatus,
)
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.research import ResearchEntry
from app.services.agents import (
    run_critic_agent,
    run_drafting_agent,
    run_manager_agent,
    run_memory_agent,
    run_procedural_agent,
    run_research_agent,
)
from app.services.agents.base import mean_confidence
from app.services.grounding.provenance import persist_grounding_links
from app.services.intelligence.generation import build_case_context, create_artifact
from app.services.knowledge.hybrid_retrieval import retrieve_case_legal_grounding_hybrid
from app.services.knowledge.retrieval import retrieve_case_legal_grounding
from app.services.knowledge.semantic_index import get_index_metadata
from app.services.memory.case_memory import build_case_memory
from app.services.ml.training.inference import predict_imported_case_type_for_case
from app.services.orchestration.planner import build_workflow_plan
from app.services.orchestration.schemas import (
    AgentStepResult,
    FinalRunOutput,
    LegalGroundingBundle,
    LegalGroundingSource,
    WorkflowPlan,
)
from app.services.runs import get_run_or_none


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(cleaned)
    return ordered


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _final_artifact_type(task_type: ChamberTaskType) -> IntelligenceArtifactType:
    mapping = {
        ChamberTaskType.SUMMARY: IntelligenceArtifactType.CASE_MEMO,
        ChamberTaskType.ISSUE_SPOTTING: IntelligenceArtifactType.ISSUE_SPOTTING,
        ChamberTaskType.PRELIMINARY_OBJECTIONS: IntelligenceArtifactType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.HEARING_NOTES: IntelligenceArtifactType.HEARING_NOTE,
        ChamberTaskType.DRAFT_OUTLINE: IntelligenceArtifactType.DRAFT_OUTLINE,
        ChamberTaskType.DRAFT_REVIEW: IntelligenceArtifactType.STRATEGY_NOTE,
        ChamberTaskType.RESEARCH_MEMO: IntelligenceArtifactType.RESEARCH_NOTE,
        ChamberTaskType.PROCEDURAL_CHECK: IntelligenceArtifactType.PROCEDURAL_SUMMARY,
    }
    return mapping[task_type]


def _final_artifact_title(case: Case, plan: WorkflowPlan) -> str:
    title_map = {
        ChamberTaskType.SUMMARY: f"Critic-reviewed chamber summary - {case.case_number}",
        ChamberTaskType.ISSUE_SPOTTING: f"Critic-reviewed issue note - {case.case_number}",
        ChamberTaskType.PRELIMINARY_OBJECTIONS: f"Preliminary objections chamber note - {case.case_number}",
        ChamberTaskType.HEARING_NOTES: f"Hearing preparation note - {case.case_number}",
        ChamberTaskType.DRAFT_OUTLINE: f"Draft outline chamber note - {case.case_number}",
        ChamberTaskType.DRAFT_REVIEW: f"Draft review note - {case.case_number}",
        ChamberTaskType.RESEARCH_MEMO: f"Research memorandum - {case.case_number}",
        ChamberTaskType.PROCEDURAL_CHECK: f"Procedural chamber note - {case.case_number}",
    }
    return title_map[plan.task_type]


def _compose_final_output(
    *,
    case: Case,
    plan: WorkflowPlan,
    memory_summary: str,
    grounding: LegalGroundingBundle,
    step_results: list[AgentStepResult],
) -> FinalRunOutput:
    manager = next((step for step in step_results if step.agent_name == "Manager Agent"), None)
    memory = next((step for step in step_results if step.agent_name == "Memory Agent"), None)
    critic = next((step for step in step_results if step.agent_name == "Critic Agent"), None)
    primary = next(
        (
            step
            for step in reversed(step_results)
            if step.agent_name in {"Drafting Agent", "Research Agent", "Procedural Agent"}
        ),
        None,
    )

    final_summary = (
        critic.structured_output.get("revisedOutputSummary")
        if critic and isinstance(critic.structured_output.get("revisedOutputSummary"), str)
        else (primary.output_summary if primary else plan.objective)
    )
    cited_materials = _dedupe(
        [
            *[source.citation_label for source in grounding.sources if source.citation_label],
            *[citation for result in step_results for citation in result.citations],
        ]
    )
    suggested_improvements = (
        critic.structured_output.get("suggestedImprovements")
        if critic and isinstance(critic.structured_output.get("suggestedImprovements"), list)
        else []
    )
    next_action = (
        suggested_improvements[0]
        if suggested_improvements
        else "Review the chamber output against the live record before relying on it externally."
    )
    critic_review = critic.full_output if critic else "No critic review was recorded for this run."
    primary_output = primary.full_output if primary else "No substantive specialist output was captured."
    confidence_score = mean_confidence(step_results)

    structured_output = {
        "objective": plan.objective,
        "workflow": plan.workflow_name,
        "taskType": plan.task_type.value,
        "managerPlan": manager.structured_output if manager else {},
        "memorySummary": memory_summary,
        "stepSummaries": [
            {
                "agentName": result.agent_name,
                "taskLabel": result.task_label,
                "outputSummary": result.output_summary,
            }
            for result in step_results
        ],
        "criticReview": critic.structured_output if critic else {},
        "citations": cited_materials,
        "nextAction": next_action,
        "agentSequence": plan.agent_sequence,
        "legalGroundingStatus": grounding.status,
        "legalRetrievalQuery": grounding.query,
        "legalBasis": [
            {
                "sourceId": source.source_id,
                "chunkId": source.chunk_id,
                "citationLabel": source.citation_label,
                "title": source.title,
                "excerpt": source.excerpt,
                "relevanceScore": source.relevance_score,
                "lexicalScore": source.lexical_score,
                "semanticScore": source.semantic_score,
                "rerankScore": source.rerank_score,
                "retrievalMode": source.retrieval_mode,
                "explanation": source.explanation,
                "usageType": source.usage_type,
            }
            for source in grounding.sources
        ],
        "retrievalMode": grounding.retrieval_mode,
        "retrievalDiagnostics": grounding.diagnostics,
    }

    draft_payload: dict | None = None
    if plan.task_type in {
        ChamberTaskType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.HEARING_NOTES,
        ChamberTaskType.DRAFT_OUTLINE,
        ChamberTaskType.DRAFT_REVIEW,
    }:
        draft_payload = {
            "title": _final_artifact_title(case, plan),
            "draftType": plan.draft_type or "Draft outline",
            "status": DraftStatus.REVIEWING,
            "content": primary_output,
            "summary": final_summary,
            "owner": "Chamber Orchestrator",
        }

    research_payload: dict | None = None
    if plan.task_type == ChamberTaskType.RESEARCH_MEMO:
        research_payload = {
            "title": _final_artifact_title(case, plan),
            "query": plan.focus_issue or plan.objective,
            "summary": final_summary,
            "sourceType": "AI Assisted Chamber Research",
            "status": ResearchStatus.NEEDS_REVIEW,
            "author": "Chamber Orchestrator",
            "nextQuestion": next_action,
            "citations": cited_materials,
        }

    final_output = (
        "Objective\n"
        f"{plan.objective}\n\n"
        "Manager Plan\n"
        f"{manager.full_output if manager else 'No manager planning note was stored.'}\n\n"
        "Memory Used\n"
        f"{memory.full_output if memory else memory_summary}\n\n"
        "Legal Basis\n"
        + (
            "\n".join(
                f"- {source.citation_label}: {source.excerpt}"
                for source in grounding.sources[:4]
            )
            if grounding.sources
            else f"{grounding.status}. No retrieved legal source was attached to this run."
        )
        + "\n\n"
        "Primary Chamber Output\n"
        f"{primary_output}\n\n"
        "Critic Review\n"
        f"{critic_review}\n\n"
        "Final Reviewed Position\n"
        f"{final_summary}\n\n"
        "Recommended Next Action\n"
        f"{next_action}"
    )

    return FinalRunOutput(
        final_summary=final_summary,
        final_output=final_output,
        confidence_score=confidence_score,
        artifact_type=_final_artifact_type(plan.task_type),
        artifact_title=_final_artifact_title(case, plan),
        structured_output=structured_output,
        next_action=next_action,
        citations=cited_materials,
        draft_payload=draft_payload,
        research_payload=research_payload,
        grounding_status=grounding.status,
        grounding_query=grounding.query,
        grounding_sources=grounding.sources,
    )


def _create_run_step_records(db: Session, run: ChamberRun, plan: WorkflowPlan) -> list[ChamberRunStep]:
    steps: list[ChamberRunStep] = []
    for index, agent_name in enumerate(plan.agent_sequence, start=1):
        task_label = {
            "Manager Agent": "Task routing and chamber plan",
            "Memory Agent": "Matter continuity retrieval",
            "Research Agent": "Research and issue analysis",
            "Drafting Agent": "Drafting support",
            "Procedural Agent": "Procedural posture check",
            "Critic Agent": "Critic and reliability review",
        }.get(agent_name, "Chamber step")
        step = ChamberRunStep(
            run_id=run.id,
            step_order=index,
            agent_name=agent_name,
            task_label=task_label,
            status=ChamberRunStepStatus.PENDING,
        )
        db.add(step)
        steps.append(step)
    db.commit()
    return steps


def _save_step_result(
    db: Session,
    step: ChamberRunStep,
    result: AgentStepResult,
) -> None:
    step.task_label = result.task_label
    step.input_summary = result.input_summary
    step.output_summary = result.output_summary
    step.full_output = result.full_output
    step.structured_json = result.structured_output
    step.confidence_score = result.confidence_score
    step.source_artifact_ids = result.source_artifact_ids
    step.metadata_json = result.metadata_json
    if result.grounding_source_ids:
        step.metadata_json = {
            **step.metadata_json,
            "groundingSourceIds": result.grounding_source_ids,
        }
    step.status = ChamberRunStepStatus.COMPLETED
    step.completed_at = _now()
    db.add(step)
    db.commit()


def _dispatch_agent_step(
    *,
    agent_name: str,
    case: Case,
    case_context,
    plan: WorkflowPlan,
    memory,
    grounding,
    step_results: list[AgentStepResult],
) -> AgentStepResult:
    if agent_name == "Manager Agent":
        return run_manager_agent(case, case_context, plan, memory, grounding)
    if agent_name == "Memory Agent":
        return run_memory_agent(case, case_context, plan, memory, grounding)
    if agent_name == "Research Agent":
        return run_research_agent(case, case_context, plan, memory, grounding)
    if agent_name == "Drafting Agent":
        return run_drafting_agent(case, case_context, plan, memory, grounding, step_results)
    if agent_name == "Procedural Agent":
        return run_procedural_agent(case, case_context, plan, memory, grounding)
    if agent_name == "Critic Agent":
        return run_critic_agent(case, case_context, plan, memory, grounding, step_results)
    raise ValueError(f"Unsupported agent step '{agent_name}'.")


def _build_legal_grounding(
    db: Session,
    *,
    case: Case,
    plan: WorkflowPlan,
    instruction: str,
) -> LegalGroundingBundle:
    if not plan.requires_legal_retrieval:
        return LegalGroundingBundle(
            query="",
            status="Retrieval not used",
            summary="The selected workflow did not require legal retrieval for this pass.",
            retrieval_mode="Retrieval not used",
            diagnostics={},
            sources=[],
        )

    if plan.task_type in {
        ChamberTaskType.PRELIMINARY_OBJECTIONS,
        ChamberTaskType.ISSUE_SPOTTING,
        ChamberTaskType.HEARING_NOTES,
        ChamberTaskType.DRAFT_OUTLINE,
        ChamberTaskType.DRAFT_REVIEW,
        ChamberTaskType.RESEARCH_MEMO,
        ChamberTaskType.PROCEDURAL_CHECK,
    }:
        retrieved = retrieve_case_legal_grounding_hybrid(
            db,
            case=case,
            instruction=instruction,
            task_type=plan.task_type,
            focus_issue=plan.focus_issue,
            limit=6,
        )
        retrieval_mode = "Hybrid"
    else:
        retrieved = retrieve_case_legal_grounding(
            db,
            case=case,
            instruction=instruction,
            task_type=plan.task_type,
            focus_issue=plan.focus_issue,
            limit=6,
            required=True,
        )
        retrieval_mode = "Lexical"

    index_metadata = get_index_metadata(db)
    return LegalGroundingBundle(
        query=retrieved.query,
        status=retrieved.status,
        summary=retrieved.summary,
        retrieval_mode=retrieval_mode,
        diagnostics={
            "weights": (
                {"lexical": 0.65, "semantic": 0.35}
                if plan.task_type in {ChamberTaskType.PRELIMINARY_OBJECTIONS, ChamberTaskType.PROCEDURAL_CHECK}
                else (
                    {"lexical": 0.45, "semantic": 0.55}
                    if plan.task_type in {ChamberTaskType.RESEARCH_MEMO, ChamberTaskType.ISSUE_SPOTTING}
                    else {"lexical": 0.5, "semantic": 0.5}
                )
            )
            if retrieval_mode == "Hybrid"
            else {"lexical": 1.0, "semantic": 0.0},
            "semanticIndex": (
                {
                    "status": index_metadata.status.value,
                    "modelName": index_metadata.model_name,
                    "sourceCount": index_metadata.source_count,
                }
                if index_metadata
                else {}
            ),
        },
        sources=[
            LegalGroundingSource(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                title=source.title,
                short_title=source.short_title,
                citation_label=source.citation_label,
                source_type=source.source_type,
                category=source.category,
                act_name=source.act_name,
                section_label=source.section_label,
                excerpt=source.excerpt,
                relevance_score=source.relevance_score,
                lexical_score=source.lexical_score,
                semantic_score=source.semantic_score,
                rerank_score=source.rerank_score,
                retrieval_mode=source.retrieval_mode,
                explanation=source.explanation,
            )
            for source in retrieved.sources
        ],
    )


def _create_draft_from_run(
    db: Session,
    *,
    case_id: str,
    payload: dict,
) -> Draft:
    latest_version = (
        max(
            [draft.version for draft in db.scalars(select(Draft).where(Draft.case_id == case_id)).all()],
            default=0,
        )
        + 1
    )
    draft = Draft(
        case_id=case_id,
        title=payload["title"],
        draft_type=payload["draftType"],
        status=payload["status"],
        content=payload["content"],
        version=latest_version,
        owner=payload["owner"],
        summary=payload["summary"],
    )
    db.add(draft)
    db.flush()
    return draft


def _create_research_from_run(
    db: Session,
    *,
    case_id: str,
    payload: dict,
) -> ResearchEntry:
    entry = ResearchEntry(
        case_id=case_id,
        title=payload["title"],
        query=payload["query"],
        summary=payload["summary"],
        citations=payload["citations"],
        source_type=payload["sourceType"],
        status=payload["status"],
        author=payload["author"],
        next_question=payload["nextQuestion"],
    )
    db.add(entry)
    db.flush()
    return entry


def _create_agent_log(
    db: Session,
    *,
    case_id: str,
    run: ChamberRun,
    plan: WorkflowPlan,
    final_output: FinalRunOutput,
    artifact: IntelligenceArtifact,
) -> AgentRunLog:
    timestamp = _now()
    log = AgentRunLog(
        case_id=case_id,
        agent_name="Manager Agent",
        title=f"Chamber workflow completed for {plan.task_type.value}",
        task_type=plan.task_type.value,
        input_summary=run.user_instruction,
        output_summary=final_output.final_summary,
        status=AgentRunStatus.COMPLETED,
        confidence_score=final_output.confidence_score,
        citations=final_output.citations,
        next_action=final_output.next_action,
        started_at=run.started_at,
        completed_at=timestamp,
        metadata_json={
            "runId": run.id,
            "workflow": plan.workflow_name,
            "artifactId": artifact.id,
            "criticSummary": run.metadata_json.get("criticSummary", ""),
        },
    )
    db.add(log)
    db.flush()
    return log


def create_case_run(
    db: Session,
    *,
    case: Case,
    instruction: str,
    task_type: ChamberTaskType | None = None,
    selected_workflow: str | None = None,
) -> ChamberRun:
    plan = build_workflow_plan(
        case,
        instruction=instruction,
        task_type=task_type,
        selected_workflow=selected_workflow,
    )
    # Chamber runs should not cold-load a transformer before returning. If the
    # case_type model has already been used, the existing prediction is reused
    # in memory; explicit prediction endpoints still load the trained model.
    predict_imported_case_type_for_case(db, case=case, load_model=False)
    memory = build_case_memory(case, task_type=plan.task_type, instruction=instruction)
    grounding = _build_legal_grounding(
        db,
        case=case,
        plan=plan,
        instruction=instruction,
    )

    run = ChamberRun(
        case_id=case.id,
        task_type=plan.task_type,
        user_instruction=instruction,
        selected_workflow=plan.workflow_name,
        status=ChamberRunStatus.QUEUED,
        metadata_json={
            "memorySummary": memory.summary,
            "memorySources": [
                {
                    "sourceId": source.source_id,
                    "sourceType": source.source_type,
                    "title": source.title,
                    "detail": source.detail,
                    "excerpt": source.excerpt,
                }
                for source in memory.sources
            ],
            "agentSequence": plan.agent_sequence,
            "routingNotes": plan.routing_notes,
            "legalGroundingStatus": grounding.status,
            "legalRetrievalQuery": grounding.query,
            "retrievalMode": grounding.retrieval_mode,
            "retrievalWeights": grounding.diagnostics.get("weights", {}),
            "semanticIndex": grounding.diagnostics.get("semanticIndex", {}),
            "legalSources": [
                {
                    "sourceId": source.source_id,
                    "chunkId": source.chunk_id,
                    "title": source.title,
                    "citationLabel": source.citation_label,
                    "excerpt": source.excerpt,
                    "relevanceScore": source.relevance_score,
                    "lexicalScore": source.lexical_score,
                    "semanticScore": source.semantic_score,
                    "rerankScore": source.rerank_score,
                    "retrievalMode": source.retrieval_mode,
                    "explanation": source.explanation,
                }
                for source in grounding.sources
            ],
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if grounding.sources:
        persist_grounding_links(
            db,
            run=run,
            sources=grounding.sources,
            usage_type=GroundingUsageType.RETRIEVED,
        )
        db.commit()

    run.status = ChamberRunStatus.PLANNING
    db.add(run)
    db.commit()

    steps = _create_run_step_records(db, run, plan)
    case_context = build_case_context(db, case)
    step_results: list[AgentStepResult] = []
    active_step: ChamberRunStep | None = None

    try:
        run.status = ChamberRunStatus.RUNNING
        db.add(run)
        db.commit()

        for step in steps:
            active_step = step
            if step.agent_name == "Critic Agent":
                run.status = ChamberRunStatus.CRITIC_REVIEW
                db.add(run)
                db.commit()

            step.status = ChamberRunStepStatus.RUNNING
            db.add(step)
            db.commit()

            result = _dispatch_agent_step(
                agent_name=step.agent_name,
                case=case,
                case_context=case_context,
                plan=plan,
                memory=memory,
                grounding=grounding,
                step_results=step_results,
            )
            _save_step_result(db, step, result)
            step_results.append(result)

        final_output = _compose_final_output(
            case=case,
            plan=plan,
            memory_summary=memory.summary,
            grounding=grounding,
            step_results=step_results,
        )

        artifact = create_artifact(
            db,
            case_id=case.id,
            artifact_type=final_output.artifact_type,
            title=final_output.artifact_title,
            content=final_output.final_output,
            structured_json={
                **final_output.structured_output,
                "runId": run.id,
                "confidenceScore": final_output.confidence_score,
            },
            source="Chamber Orchestrator",
            status=IntelligenceStatus.NEEDS_REVIEW,
        )
        if grounding.sources:
            persist_grounding_links(
                db,
                artifact=artifact,
                sources=grounding.sources,
                usage_type=GroundingUsageType.RELIED_ON,
            )

        linked_draft: Draft | None = None
        if final_output.draft_payload:
            linked_draft = _create_draft_from_run(
                db,
                case_id=case.id,
                payload=final_output.draft_payload,
            )

        linked_research: ResearchEntry | None = None
        if final_output.research_payload:
            linked_research = _create_research_from_run(
                db,
                case_id=case.id,
                payload=final_output.research_payload,
            )

        critic_result = next((step for step in step_results if step.agent_name == "Critic Agent"), None)
        run.final_output = final_output.final_output
        run.final_summary = final_output.final_summary
        run.confidence_score = final_output.confidence_score
        run.status = ChamberRunStatus.COMPLETED
        run.completed_at = _now()
        run.metadata_json = {
            **run.metadata_json,
            "finalArtifactId": artifact.id,
            "linkedDraftId": linked_draft.id if linked_draft else None,
            "linkedResearchEntryId": linked_research.id if linked_research else None,
            "criticSummary": critic_result.output_summary if critic_result else "",
            "nextAction": final_output.next_action,
            "legalGroundingStatus": final_output.grounding_status,
            "legalRetrievalQuery": final_output.grounding_query,
            "retrievalMode": grounding.retrieval_mode,
            "retrievalWeights": grounding.diagnostics.get("weights", {}),
            "semanticIndex": grounding.diagnostics.get("semanticIndex", {}),
        }
        db.add(run)
        _create_agent_log(
            db,
            case_id=case.id,
            run=run,
            plan=plan,
            final_output=final_output,
            artifact=artifact,
        )
        db.commit()
    except Exception as exc:
        if active_step is not None:
            active_step.status = ChamberRunStepStatus.FAILED
            active_step.output_summary = str(exc)
            active_step.completed_at = _now()
            db.add(active_step)
        run.status = ChamberRunStatus.FAILED
        run.completed_at = _now()
        run.metadata_json = {
            **run.metadata_json,
            "error": str(exc),
        }
        db.add(run)
        db.commit()
        raise

    refreshed = get_run_or_none(db, run.id)
    return refreshed or run
