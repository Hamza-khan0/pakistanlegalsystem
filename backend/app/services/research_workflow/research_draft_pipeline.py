from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ResearchRunStatus, ResearchStatus
from app.models.research import ResearchEntry
from app.models.research_run import ResearchRun
from app.schemas.research import (
    LEGAL_RESEARCH_WARNING,
    PDF_MODE_DRAFT_WITH_RESEARCH,
    ResearchWorkflowRequest,
    ResearchWorkflowResponse,
)
from app.services.research_workflow.case_context import assemble_case_context
from app.services.research_workflow.critic_agent import critic_review_research_memo
from app.services.research_workflow.drafting_agent import generate_full_legal_draft
from app.services.research_workflow.drafting_instructions import build_drafting_instructions
from app.services.research_workflow.draft_storage import normalize_generated_draft
from app.services.research_workflow.issue_detection import detect_research_issues
from app.services.research_workflow.legal_retrieval import retrieve_pakistani_legal_sources
from app.services.research_workflow.live_web_search import get_live_web_search_health
from app.services.research_workflow.query_planner import build_legal_research_query_plan
from app.services.research_workflow.research_agent import (
    generate_llm_structured_research_memo,
    generate_structured_research_memo,
)
from app.services.research_workflow.research_artifacts import write_research_artifacts
from app.services.llm.provider import PRIVACY_NOTICE, get_llm_health


def _summarize_context(context: dict[str, Any]) -> str:
    parts = [
        str(context.get("case_title") or ""),
        str(context.get("forum") or ""),
        str(context.get("stage") or ""),
        str(context.get("facts") or "")[:500],
    ]
    return " | ".join(part for part in parts if part.strip())[:1200]


def _status_value(status: ResearchRunStatus | str) -> str:
    return status.value if isinstance(status, ResearchRunStatus) else str(status)


def _response_payload(run: ResearchRun) -> dict[str, Any]:
    generated_draft = normalize_generated_draft(run.generated_draft_json)
    lawyer_review_checklist = []
    if generated_draft:
        lawyer_review_checklist.extend(generated_draft.get("lawyer_review_checklist", []))
    lawyer_review_checklist.extend((run.critic_report_json or {}).get("required_lawyer_checks", []))
    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "status": _status_value(run.status),
        "detected_issues": run.detected_issues_json or [],
        "query_plan": run.query_plan_json or [],
        "retrieved_sources": run.retrieved_sources_json or [],
        "research_memo": run.research_memo_json or {
            "legal_authority_warning": LEGAL_RESEARCH_WARNING,
        },
        "generated_draft": generated_draft,
        "critic_report": run.critic_report_json or {
            "passed": False,
            "severity": "medium",
            "unsupported_claims": [],
            "fake_or_unverified_citations": [],
            "weak_sources": [],
            "missing_authorities": [],
            "drafting_defects": [],
            "overclaiming_warnings": [],
            "drafting_risks": [],
            "required_lawyer_checks": [],
            "recommendation": "Research run has not completed.",
        },
        "drafting_instructions": run.drafting_instructions_json or {},
        "live_web_used": bool(run.live_web_used),
        "llm_used_for_research": bool(run.llm_used_for_research),
        "llm_used_for_drafting": bool(run.llm_used_for_drafting),
        "sources_by_origin": run.sources_by_origin_json or {},
        "lawyer_review_checklist": list(dict.fromkeys(lawyer_review_checklist)),
        "provider_status": run.provider_metadata_json or {},
        "pdf_path": run.pdf_path,
        "markdown_path": run.markdown_path,
        "legal_authority_warning": LEGAL_RESEARCH_WARNING,
        "privacy_notice": PRIVACY_NOTICE,
        "warnings": run.warnings_json or [],
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


def research_run_to_response(run: ResearchRun) -> ResearchWorkflowResponse:
    return ResearchWorkflowResponse(**_response_payload(run))


def research_run_summary(run: ResearchRun) -> dict[str, Any]:
    memo = run.research_memo_json or {}
    critic = run.critic_report_json or {}
    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "status": _status_value(run.status),
        "workflow_type": run.workflow_type,
        "detected_issue_count": len(run.detected_issues_json or []),
        "source_count": len(run.retrieved_sources_json or []),
        "critic_passed": bool(critic.get("passed")),
        "recommended_draft_type": str(memo.get("recommended_draft_type") or "research_memo"),
        "pdf_path": run.pdf_path,
        "markdown_path": run.markdown_path,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


def _sources_by_origin(sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "local_corpus": [],
        "live_web": [],
        "uploaded_documents": [],
        "fallback": [],
    }
    for source in sources:
        origin = str(source.get("source_origin") or "unknown")
        groups.setdefault(origin, []).append(source)
    return groups


def _provider_status(
    *,
    live_web_used: bool,
    llm_research_used: bool,
    llm_drafting_used: bool,
    retrieval_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    llm_health = get_llm_health()
    web_health = get_live_web_search_health()
    retrieval_status = retrieval_status or {}
    return {
        "localRetrievalAvailable": True,
        "localRetrievalUsed": True,
        "retrieval": retrieval_status,
        "liveWebSearch": web_health,
        "liveWebSearchEnabled": bool(web_health.get("enabled")),
        "liveWebSearchAvailable": bool(web_health.get("available")),
        "searchProvider": "openai",
        "openaiWebSearchUsed": live_web_used,
        "llm": llm_health,
        "llmEnabled": bool(llm_health.get("enabled")),
        "llmAvailable": bool(llm_health.get("available")),
        "llmModel": llm_health.get("model"),
        "externalSearchUsed": live_web_used,
        "externalLlmUsed": bool(llm_research_used or llm_drafting_used),
        "llmUsedForResearch": llm_research_used,
        "llmUsedForDrafting": llm_drafting_used,
        "pdfAvailable": True,
        "artifactDirWritable": True,
        "privacyNotice": PRIVACY_NOTICE,
    }


def get_research_run(db: Session, run_id: str) -> ResearchRun | None:
    return db.get(ResearchRun, run_id)


def list_case_research_runs(db: Session, case_id: str) -> list[ResearchRun]:
    return list(
        db.scalars(
            select(ResearchRun)
            .where(ResearchRun.case_id == case_id)
            .order_by(ResearchRun.created_at.desc())
        ).all()
    )


def regenerate_research_draft(
    db: Session,
    run: ResearchRun,
    *,
    draft_type: str,
    use_llm: bool = True,
) -> dict[str, Any]:
    context = assemble_case_context(
        db,
        run.case_id,
        {
            "include_documents": True,
            "include_prior_notes": True,
            "include_timeline": True,
        },
    )
    if context is None:
        raise ValueError("Case not found.")

    previous = normalize_generated_draft(run.generated_draft_json) or {}
    memo = run.research_memo_json or {"legal_authority_warning": LEGAL_RESEARCH_WARNING}
    sources = list(run.retrieved_sources_json or [])
    critic = run.critic_report_json or {}
    regenerated = generate_full_legal_draft(
        context,
        memo,
        critic,
        draft_type,
        sources,
        use_llm=use_llm,
    )
    if previous.get("final_draft_markdown"):
        regenerated["previous_draft_markdown"] = previous["final_draft_markdown"]
    if regenerated.get("_llm_warning"):
        run.warnings_json = list(dict.fromkeys([*(run.warnings_json or []), str(regenerated["_llm_warning"])]))

    regenerated = normalize_generated_draft(regenerated) or {}
    regenerated["edited_draft_markdown"] = None
    regenerated["final_draft_markdown"] = regenerated.get("draft_markdown") or ""
    regenerated["last_edited_at"] = None
    regenerated["pdf_stale"] = True
    run.generated_draft_json = regenerated
    run.llm_used_for_drafting = bool(regenerated.get("_llm_used"))
    run.critic_report_json = critic_review_research_memo(memo, sources, context, regenerated)
    db.commit()
    db.refresh(run)
    return regenerated


def regenerate_research_artifacts(
    db: Session,
    run: ResearchRun,
    *,
    generate_pdf: bool = True,
    use_edited_draft: bool = True,
    pdf_mode: str = PDF_MODE_DRAFT_WITH_RESEARCH,
) -> tuple[str, str | None, list[str]]:
    response_data = _response_payload(run)
    if not use_edited_draft and response_data.get("generated_draft"):
        draft = dict(response_data["generated_draft"])
        draft["final_draft_markdown"] = draft.get("draft_markdown") or ""
        response_data["generated_draft"] = draft
    markdown_path, pdf_path, artifact_warnings = write_research_artifacts(
        run.id,
        response_data,
        generate_pdf=generate_pdf,
        pdf_mode=pdf_mode,
    )
    run.markdown_path = markdown_path
    if pdf_path:
        run.pdf_path = pdf_path
    if artifact_warnings:
        existing = list(run.warnings_json or [])
        run.warnings_json = list(dict.fromkeys([*existing, *artifact_warnings]))
    db.commit()
    db.refresh(run)
    return markdown_path, pdf_path, artifact_warnings


def _create_research_entry(db: Session, run: ResearchRun) -> None:
    memo = run.research_memo_json or {}
    critic = run.critic_report_json or {}
    citations = [
        str(source.get("citation") or source.get("title"))
        for source in memo.get("source_list", [])
        if source.get("citation") or source.get("title")
    ][:12]
    summary_lines = [
        "AI research draft pipeline completed.",
        f"Issues: {', '.join(memo.get('legal_issues', [])[:8]) or 'None detected'}",
        f"Recommendation: {critic.get('recommendation') or 'Review required.'}",
        LEGAL_RESEARCH_WARNING,
    ]
    db.add(
        ResearchEntry(
            case_id=run.case_id,
            title=f"Research & Draft Pipeline - {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
            query="; ".join(item.get("query", "") for item in (run.query_plan_json or [])[:4]),
            summary="\n".join(summary_lines),
            citations=citations,
            source_type="AI Research Draft Pipeline",
            status=ResearchStatus.VERIFIED if critic.get("passed") else ResearchStatus.NEEDS_REVIEW,
            author="Research Agent",
            next_question="Lawyer should review research gaps, source relevance, and drafting cautions before filing.",
        )
    )


def run_research_draft_pipeline(
    db: Session,
    request: ResearchWorkflowRequest,
) -> ResearchWorkflowResponse:
    context = assemble_case_context(
        db,
        request.case_id,
        {
            "include_documents": request.include_documents,
            "include_prior_notes": request.include_prior_notes,
            "include_timeline": request.include_timeline,
        },
    )
    if context is None:
        raise ValueError("Case not found.")

    run = ResearchRun(
        case_id=request.case_id,
        status=ResearchRunStatus.RUNNING,
        workflow_type="research_draft_pipeline",
        input_summary=_summarize_context(context),
        warnings_json=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        warnings: list[str] = []
        if context.get("missing_context"):
            warnings.append("Limited case context was available.")

        issues = detect_research_issues(context, request.focus_issues)
        if not issues:
            warnings.append("No legal issue classifier signal was available; research proceeded from case context.")
        query_plan = build_legal_research_query_plan(context, issues)
        if not query_plan:
            warnings.append("No research query plan could be generated.")
        web_health = get_live_web_search_health()
        include_live_web = bool(request.use_live_web and web_health.get("available"))
        if request.use_live_web and not include_live_web:
            warnings.append(str(web_health.get("reason") or "Live web search unavailable; local corpus used."))
        retrieval_bundle = retrieve_pakistani_legal_sources(
            db,
            query_plan,
            max_sources=request.max_sources,
            include_live_web=include_live_web,
            use_openai_web_search=True,
            max_live_sources=request.max_live_sources,
        )
        sources = list(retrieval_bundle.get("sources", []))
        warnings.extend(str(item) for item in retrieval_bundle.get("retrieval_warnings", []))
        if not sources:
            warnings.append("No Pakistani legal sources were retrieved; memo marks this as a research gap.")
        source_groups = retrieval_bundle.get("sources_by_origin") or _sources_by_origin(sources)
        live_web_used = bool(source_groups.get("live_web"))
        if include_live_web and not live_web_used:
            warnings.append("Live web search was enabled, but no live web legal source was retained after ranking.")

        if request.use_llm:
            memo = generate_llm_structured_research_memo(context, issues, query_plan, sources)
        else:
            memo = generate_structured_research_memo(context, issues, query_plan, sources)
            memo["_llm_used"] = False
        llm_research_used = bool(memo.get("_llm_used"))
        if request.use_llm and not llm_research_used:
            llm_warning = memo.get("_llm_warning") or get_llm_health().get("reason")
            if llm_warning:
                warnings.append(str(llm_warning))

        preliminary_critic = critic_review_research_memo(memo, sources, context)
        generated_draft: dict[str, Any] | None = None
        llm_drafting_used = False
        if request.generate_full_draft:
            generated_draft = generate_full_legal_draft(
                context,
                memo,
                preliminary_critic,
                request.draft_type,
                sources,
                use_llm=request.use_llm,
            )
            llm_drafting_used = bool(generated_draft.get("_llm_used"))
            if request.use_llm and generated_draft.get("_llm_warning"):
                warnings.append(str(generated_draft["_llm_warning"]))
            generated_draft = normalize_generated_draft(generated_draft)

        critic_report = critic_review_research_memo(memo, sources, context, generated_draft)
        drafting = build_drafting_instructions(context, memo, critic_report, request.draft_type)

        run.detected_issues_json = issues
        run.query_plan_json = query_plan
        run.retrieved_sources_json = sources
        run.research_memo_json = memo
        run.generated_draft_json = generated_draft or {}
        run.critic_report_json = critic_report
        run.drafting_instructions_json = drafting
        run.sources_by_origin_json = source_groups
        run.live_web_used = live_web_used
        run.llm_used_for_research = llm_research_used
        run.llm_used_for_drafting = llm_drafting_used
        run.provider_metadata_json = _provider_status(
            live_web_used=live_web_used,
            llm_research_used=llm_research_used,
            llm_drafting_used=llm_drafting_used,
            retrieval_status=retrieval_bundle.get("provider_status", {}),
        )
        run.warnings_json = warnings
        run.completed_at = datetime.now(UTC)
        run.status = (
            ResearchRunStatus.COMPLETED
            if critic_report.get("passed") and not warnings and critic_report.get("severity") != "high"
            else ResearchRunStatus.COMPLETED_WITH_WARNINGS
        )

        response_data = _response_payload(run)
        markdown_path, pdf_path, artifact_warnings = write_research_artifacts(
            run.id,
            response_data,
            generate_pdf=request.generate_pdf,
            pdf_mode=request.pdf_mode,
        )
        run.markdown_path = markdown_path
        run.pdf_path = pdf_path
        run.warnings_json = warnings + artifact_warnings
        _create_research_entry(db, run)
        db.commit()
        db.refresh(run)
        return research_run_to_response(run)
    except Exception as exc:
        run.status = ResearchRunStatus.FAILED
        run.error_message = str(exc)
        run.completed_at = datetime.now(UTC)
        db.commit()
        raise
