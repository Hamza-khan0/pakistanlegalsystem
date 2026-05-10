from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
import logging
import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.models.enums import IntelligenceArtifactType
from app.services.llm.base import (
    CaseContext,
    ChamberGenerationProvider,
    DraftOutput,
    GroundingContext,
    IssueOutput,
    ResearchOutput,
    SummaryOutput,
)
from app.services.llm.prompts import LEGAL_CHAMBER_BRIEF, placeholder_authority


DATE_PATTERN = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b"
)

logger = logging.getLogger(__name__)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
PRIVACY_NOTICE = (
    "When external LLM or web search is enabled, selected case text, research queries, and retrieved source excerpts "
    "may be sent to the configured OpenAI API."
)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered


def truncate(value: str, *, limit: int = 1200) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def is_llm_available() -> bool:
    return bool(settings.llm_drafting_enabled and settings.openai_api_key.strip())


def get_llm_health() -> dict[str, Any]:
    enabled = bool(settings.llm_drafting_enabled)
    key_configured = bool(settings.openai_api_key.strip())
    sdk_available = importlib.util.find_spec("openai") is not None
    available = bool(enabled and key_configured)
    return {
        "enabled": enabled,
        "available": available,
        "provider": "openai" if key_configured else "none",
        "model": settings.openai_model,
        "responses_api": True,
        "openai_package_installed": sdk_available,
        "api_key_configured": key_configured,
        "reason": (
            "OpenAI LLM drafting is enabled."
            if available
            else "OPENAI_API_KEY is not configured or LLM_DRAFTING_ENABLED is false; deterministic fallback will be used."
        ),
        "privacy_notice": PRIVACY_NOTICE,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        raise


def _extract_response_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    chunks: list[str] = []
    for item in data.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _request_openai(payload: dict[str, Any], *, endpoint: str = OPENAI_RESPONSES_URL) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=max(30, settings.web_search_timeout_seconds)) as client:
        response = client.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def _responses_payload(
    prompt: str,
    *,
    system_prompt: str | None,
    temperature: float,
    max_output_tokens: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "instructions": system_prompt
        or (
            "You are an AI Legal Chambers assistant. Do not invent legal authorities, citations, courts, dates, "
            "or facts. Use only supplied sources as authorities."
        ),
        "input": prompt,
        "temperature": temperature,
    }
    if max_output_tokens:
        payload["max_output_tokens"] = max_output_tokens
    return payload


def _chat_payload(
    prompt: str,
    *,
    system_prompt: str | None,
    temperature: float,
    json_mode: bool,
    max_output_tokens: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
                or (
                    "You are an AI Legal Chambers assistant. Do not invent legal authorities, "
                    "citations, courts, dates, or facts. Use only supplied sources as authorities."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if max_output_tokens:
        payload["max_tokens"] = max_output_tokens
    return payload


def _call_openai_text(
    prompt: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    json_mode: bool = False,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    if not is_llm_available():
        return {
            "ok": False,
            "text": "",
            "json": None,
            "model": settings.openai_model,
            "provider": "openai",
            "error": "OPENAI_API_KEY is not configured or LLM_DRAFTING_ENABLED is false.",
            "duration_ms": 0,
        }

    last_error: Exception | None = None
    for attempt in range(2):
        started = time.perf_counter()
        try:
            data = _request_openai(
                _responses_payload(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
            )
            content = _extract_response_text(data)
            duration_ms = round((time.perf_counter() - started) * 1000)
            logger.info(
                "LLM_RESPONSES_SUCCESS model=%s json=%s duration_ms=%s attempt=%s",
                settings.openai_model,
                json_mode,
                duration_ms,
                attempt + 1,
            )
            return {
                "ok": True,
                "text": str(content or ""),
                "json": None,
                "model": settings.openai_model,
                "provider": "openai",
                "error": None,
                "duration_ms": duration_ms,
            }
        except Exception as exc:
            last_error = exc
            duration_ms = round((time.perf_counter() - started) * 1000)
            logger.warning(
                "LLM_RESPONSES_FAILED model=%s json=%s duration_ms=%s attempt=%s error=%s",
                settings.openai_model,
                json_mode,
                duration_ms,
                attempt + 1,
                type(exc).__name__,
            )
            if attempt == 0:
                time.sleep(0.5)

    # Compatibility fallback for older accounts/models where Responses parameters may not be enabled yet.
    started = time.perf_counter()
    try:
        data = _request_openai(
            _chat_payload(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                json_mode=json_mode,
                max_output_tokens=max_output_tokens,
            ),
            endpoint=OPENAI_CHAT_COMPLETIONS_URL,
        )
        content = data["choices"][0]["message"]["content"]
        duration_ms = round((time.perf_counter() - started) * 1000)
        logger.info(
            "LLM_CHAT_COMPAT_SUCCESS model=%s json=%s duration_ms=%s",
            settings.openai_model,
            json_mode,
            duration_ms,
        )
        return {
            "ok": True,
            "text": str(content or ""),
            "json": None,
            "model": settings.openai_model,
            "provider": "openai",
            "error": None,
            "duration_ms": duration_ms,
        }
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "text": "",
            "json": None,
            "model": settings.openai_model,
            "provider": "openai",
            "error": f"{type(last_error or exc).__name__}: {last_error or exc}",
            "duration_ms": duration_ms,
        }


def generate_text(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    return _call_openai_text(
        prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        json_mode=False,
        max_output_tokens=max_output_tokens,
    )


def generate_json(
    prompt: str,
    system_prompt: str | None = None,
    schema_name: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    schema_label = schema_name or "JSON"
    json_prompt = (
        f"Return valid JSON only for schema `{schema_label}`. "
        "Do not wrap it in Markdown.\n\n"
        f"{prompt}"
    )
    result = _call_openai_text(
        json_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        json_mode=True,
        max_output_tokens=max_output_tokens,
    )
    if not result["ok"]:
        return result

    content = str(result.get("text") or "")
    try:
        result["json"] = _extract_json_object(content)
        return result
    except Exception:
        repair_prompt = (
            f"Repair this into valid JSON only for schema `{schema_label}`. "
            "No Markdown, no commentary.\n\n"
            f"{content[:12000]}"
        )
        repaired = _call_openai_text(
            repair_prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            json_mode=True,
            max_output_tokens=max_output_tokens,
        )
        if not repaired["ok"]:
            return {
                **result,
                "ok": False,
                "json": None,
                "error": repaired.get("error") or "JSON repair failed.",
            }
        try:
            repaired["json"] = _extract_json_object(str(repaired.get("text") or ""))
            return repaired
        except Exception as exc:
            return {
                **repaired,
                "ok": False,
                "json": None,
                "error": f"JSON parse failed: {type(exc).__name__}",
            }


def extract_dates(source: str) -> list[str]:
    return dedupe(DATE_PATTERN.findall(source))[:6]


def matter_defaults(context: CaseContext) -> tuple[list[str], list[str], list[str]]:
    matter = context.matter_type.lower()
    maintainability: list[str] = []
    hooks = dedupe(context.linked_statutes)
    authority_leads = dedupe(context.precedents)

    if "constitutional" in matter or "article 199" in context.summary.lower():
        maintainability.extend(
            [
                "Expect an alternate remedy objection at threshold and be ready to justify constitutional intervention.",
                "Clarify the exact jurisdictional hook and the immediate prejudice requiring writ relief.",
            ]
        )
        hooks.extend(
            [
                "Constitution of Pakistan, Article 199",
                "Customs Act, 1969",
            ]
        )
        authority_leads.extend(
            [
                placeholder_authority("alternate remedy exception in urgent customs detention matter"),
                placeholder_authority("denial of hearing before adverse valuation or detention action"),
            ]
        )
    elif "service" in matter:
        maintainability.extend(
            [
                "Limitation and continuing cause need a clean documentary chain.",
                "Relief should match the service forum's approach to filled posts and consequential benefits.",
            ]
        )
        hooks.extend(
            [
                "Punjab Service Tribunals Act, 1974",
                "Punjab Civil Servants Act, 1974",
            ]
        )
        authority_leads.extend(
            [
                placeholder_authority("continuing cause in delayed service appeal"),
                placeholder_authority("condonation where repeated representations are pleaded"),
            ]
        )
    elif "revenue" in matter:
        maintainability.extend(
            [
                "Revision maintainability depends on the scope of interference with concurrent revenue findings.",
                "Notice, locus, and the underlying revenue record must be internally consistent.",
            ]
        )
        hooks.extend(["Punjab Land Revenue Act, 1967"])
        authority_leads.extend(
            [
                placeholder_authority("revision against mutation order where notice was defective"),
                placeholder_authority("revenue revision treatment of possession narrative"),
            ]
        )
    else:
        maintainability.extend(
            [
                "Be ready on jurisdiction and the adequacy of alternate internal remedies.",
                "Urgent interim relief will depend on a clean record showing irreparable prejudice.",
            ]
        )
        hooks.extend(
            [
                "Specific Relief Act, 1877",
                "Transfer of Property Act, 1882",
            ]
        )
        authority_leads.extend(
            [
                placeholder_authority("interim injunction threshold in allotment cancellation dispute"),
                placeholder_authority("civil maintainability where administrative action is challenged as void"),
            ]
        )

    return dedupe(maintainability), dedupe(hooks), dedupe(authority_leads)


def infer_missing_material(context: CaseContext) -> list[str]:
    known_types = {document.document_type.casefold() for document in context.documents}
    missing: list[str] = []

    if "order sheet" not in known_types:
        missing.append("No order sheet or court proceeding sheet is linked yet.")
    if "annexure" not in known_types:
        missing.append("Supporting annexures remain thin and may need a tighter documentary bundle.")
    if not context.documents:
        missing.append("No processed document set is currently available for extraction-backed review.")
    if not context.timeline:
        missing.append("Timeline entries are too thin to lock a complete procedural chronology.")
    if not context.notes:
        missing.append("No fresh internal note explains advocacy posture or client instructions.")

    missing.extend(context.risk_flags)
    return dedupe(missing)


def grounding_citations(grounding: GroundingContext | None) -> list[str]:
    if not grounding or not grounding.sources:
        return []
    return dedupe([source.citation_label for source in grounding.sources if source.citation_label])


def grounding_basis_lines(grounding: GroundingContext | None, *, limit: int = 3) -> list[str]:
    if not grounding or not grounding.sources:
        return []
    return [
        f"{source.citation_label}: {truncate(source.excerpt, limit=180)}"
        for source in grounding.sources[:limit]
    ]


def build_factual_summary(context: CaseContext) -> str:
    fact_lines = [fact.get("text", "").strip() for fact in context.facts_background if fact.get("text")]
    document_lines = [document.excerpt for document in context.documents if document.excerpt]
    sentences = [context.summary.strip(), *fact_lines[:2], *document_lines[:2]]
    joined = " ".join(sentence for sentence in sentences if sentence)
    return truncate(joined or "Source material is limited, so the factual summary remains provisional.")


def build_procedural_summary(context: CaseContext) -> str:
    timeline_bits = [
        f"{entry['date']}: {entry['title']}"
        for entry in context.timeline[:3]
        if entry.get("date") and entry.get("title")
    ]
    hearing = (
        f"The next listed hearing is {context.next_hearing_date}."
        if context.next_hearing_date
        else "No next hearing date is currently stored."
    )
    stage = f"The matter is presently at the stage: {context.filing_stage}."
    timeline_summary = (
        " Recent recorded procedural events include " + "; ".join(timeline_bits) + "."
        if timeline_bits
        else ""
    )
    return truncate(f"{stage} {hearing}{timeline_summary}")


def build_recommendations(context: CaseContext, missing_material: list[str]) -> list[str]:
    recommendations = list(context.procedural_alerts[:3])
    if context.next_hearing_date:
        recommendations.append(
            f"Lock the hearing bundle and oral-argument note before {context.next_hearing_date}."
        )
    if missing_material:
        recommendations.append(f"Prioritize curing the record gap: {missing_material[0]}")
    if context.documents:
        recommendations.append("Cross-check each generated point against the linked pleadings and annexures before filing.")
    else:
        recommendations.append("Upload and process the primary pleading before treating this output as more than a first-pass chamber note.")
    return dedupe(recommendations)[:5]


def determine_artifact_type(draft_type: str) -> IntelligenceArtifactType:
    normalized = draft_type.strip().casefold()
    if "objection" in normalized:
        return IntelligenceArtifactType.PRELIMINARY_OBJECTIONS
    if "petition" in normalized:
        return IntelligenceArtifactType.PETITION_SKELETON
    if "reply" in normalized:
        return IntelligenceArtifactType.REPLY_SKELETON
    if "hearing" in normalized:
        return IntelligenceArtifactType.HEARING_NOTE
    if "memo" in normalized:
        return IntelligenceArtifactType.CASE_MEMO
    if "strategy" in normalized:
        return IntelligenceArtifactType.STRATEGY_NOTE
    return IntelligenceArtifactType.DRAFT_OUTLINE


def build_draft_sections(
    context: CaseContext,
    *,
    draft_type: str,
    issues: list[str],
    missing_information: list[str],
) -> list[str]:
    normalized = draft_type.strip().casefold()
    if "objection" in normalized:
        return [
            "Preliminary submissions and chamber framing",
            "Maintainability and jurisdiction objections",
            "Record gaps and evidentiary reservations",
            "Reply to anticipated urgency or interim relief plea",
            "Prayer and without-prejudice reservations",
        ]
    if "petition" in normalized:
        return [
            "Jurisdiction and maintainability",
            "Facts and chronology",
            "Grounds",
            "Interim relief",
            "Prayer",
        ]
    if "reply" in normalized:
        return [
            "Introductory response",
            "Point-wise factual rebuttal",
            "Legal answer to maintainability objections",
            "Annexure and record clarification",
            "Prayer",
        ]
    if "hearing" in normalized:
        return [
            "Bench-facing issue list",
            "Chronology points to lead with",
            "Likely questions from the court",
            "Record gaps to manage carefully",
            "Immediate post-hearing follow-up",
        ]
    if "memo" in normalized:
        return [
            "Matter snapshot",
            "Live issues",
            "Procedural posture",
            "Risk and dependency note",
            "Recommended chamber next steps",
        ]
    if "strategy" in normalized:
        return [
            "Commercial or client objective",
            "Pressure points in the current record",
            "Pleadable themes",
            "Settlement / leverage note",
            "Immediate action plan",
        ]
    return [
        "Heading and chamber framing",
        "Facts and record position",
        "Issues to develop",
        "Draft argument buckets",
        "Prayer / next drafting step",
    ]


class LocalChamberProvider(ChamberGenerationProvider):
    provider_name = settings.llm_provider_label
    provider_brief = LEGAL_CHAMBER_BRIEF

    def generate_case_summary(
        self,
        context: CaseContext,
        *,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> SummaryOutput:
        maintainability, hooks, authority_leads = matter_defaults(context)
        important_dates = dedupe(
            [
                *( [context.next_hearing_date] if context.next_hearing_date else [] ),
                *[entry["date"] for entry in context.timeline if entry.get("date")],
                *extract_dates(context.source_excerpt),
            ]
        )[:6]
        missing_material = infer_missing_material(context)
        next_steps = build_recommendations(context, missing_material)
        key_parties = dedupe(
            [
                context.client_name,
                context.opposing_party,
                context.forum,
                *context.assigned_counsel,
            ]
        )
        citations = dedupe([*grounding_citations(grounding), *context.precedents, *hooks, *authority_leads])[:8]
        if instructions.strip():
            next_steps.insert(0, f"Apply the extra chamber instruction during review: {truncate(instructions, limit=180)}")
        procedural_summary = build_procedural_summary(context)
        if grounding and grounding.sources:
            next_steps.insert(0, f"Ground the note in {grounding.sources[0].citation_label}.")
            procedural_summary = (
                f"{procedural_summary} Legal basis consulted: "
                + "; ".join(source.citation_label for source in grounding.sources[:2])
            )

        return SummaryOutput(
            factual_summary=build_factual_summary(context),
            procedural_summary=f"{procedural_summary} {' '.join(maintainability[:1])}".strip(),
            key_parties=key_parties,
            important_dates=important_dates,
            relief_sought=dedupe(context.relief_sought),
            next_steps=next_steps,
            citations=citations,
            confidence_score=0.74 if context.documents else 0.61,
        )

    def generate_issue_spotting(
        self,
        context: CaseContext,
        *,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> IssueOutput:
        maintainability, hooks, authority_leads = matter_defaults(context)
        missing_information = infer_missing_material(context)
        if grounding and grounding.sources:
            maintainability.insert(
                0,
                f"Retrieved legal basis presently points to {grounding.sources[0].citation_label} as a live support provision.",
            )
        elif grounding and not grounding.sources:
            maintainability.insert(
                0,
                "No sufficiently relevant legal source was retrieved, so maintainability analysis remains only partially grounded.",
            )
        legal_issues = dedupe([*context.legal_issues, *maintainability[:2]])
        risk_flags = dedupe([*context.risk_flags, *missing_information[:3]])
        recommendations = build_recommendations(context, missing_information)
        if instructions.strip():
            recommendations.insert(0, f"Review through this extra lens: {truncate(instructions, limit=180)}")
        if grounding and grounding.sources:
            recommendations.insert(
                0,
                f"Use the retrieved basis from {grounding.sources[0].citation_label} when framing threshold objections.",
            )
        return IssueOutput(
            legal_issues=legal_issues[:6],
            maintainability_concerns=maintainability,
            missing_information=missing_information[:6],
            risk_flags=risk_flags[:6],
            recommendations=recommendations[:5],
            citations=dedupe([*grounding_citations(grounding), *context.precedents, *hooks, *authority_leads])[:8],
            confidence_score=0.7 if context.documents else 0.57,
        )

    def generate_draft_assistance(
        self,
        context: CaseContext,
        *,
        draft_type: str,
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> DraftOutput:
        issue_output = self.generate_issue_spotting(
            context,
            instructions=instructions,
            grounding=grounding,
        )
        artifact_type = determine_artifact_type(draft_type)
        sections = build_draft_sections(
            context,
            draft_type=draft_type,
            issues=issue_output.legal_issues,
            missing_information=issue_output.missing_information,
        )
        content_blocks = [
            f"{index}. {section}\n"
            f"   Chamber note: {self._section_note(section, context, issue_output)}"
            for index, section in enumerate(sections, start=1)
        ]
        if grounding and grounding.sources:
            content_blocks.append("Legal Basis\n- " + "\n- ".join(grounding_basis_lines(grounding)))
        elif grounding and not grounding.sources:
            content_blocks.append(
                "Legal Basis\n- No sufficiently relevant statutory or provision-level source was retrieved for this draft pass."
            )
        if instructions.strip():
            content_blocks.append(
                f"Additional chamber instruction:\n{truncate(instructions, limit=320)}"
            )
        title = f"{draft_type.strip() or 'Draft Outline'} - {context.case_number}"
        summary = truncate(
            f"AI-assisted first-pass {draft_type.lower() if draft_type else 'draft'} for {context.title}. "
            f"Focus remains on {', '.join(issue_output.legal_issues[:2]) or 'the live issues in the matter'}."
        )
        return DraftOutput(
            artifact_type=artifact_type,
            title=title,
            summary=summary,
            content="\n\n".join(content_blocks),
            citations=dedupe([*grounding_citations(grounding), *issue_output.citations])[:6],
            next_action=issue_output.recommendations[0] if issue_output.recommendations else "Review and tailor the draft against the actual record before external use.",
            confidence_score=0.68 if context.documents else 0.55,
        )

    def generate_research_note(
        self,
        context: CaseContext,
        *,
        issue: str = "",
        instructions: str = "",
        grounding: GroundingContext | None = None,
    ) -> ResearchOutput:
        maintainability, hooks, authority_leads = matter_defaults(context)
        issue_output = self.generate_issue_spotting(
            context,
            instructions=instructions,
            grounding=grounding,
        )
        selected_issue = issue.strip() or (
            issue_output.legal_issues[0]
            if issue_output.legal_issues
            else "Primary maintainability and merits issue"
        )
        analysis_direction = dedupe(
            [
                f"Anchor the note around: {selected_issue}",
                *maintainability[:2],
                "Separate verified facts from gaps that still depend on document retrieval or client confirmation.",
            ]
        )
        factual_dependencies = dedupe(
            [
                *issue_output.missing_information[:3],
                "Confirm the exact wording of the impugned action and the date of communication from the source record.",
            ]
        )
        next_steps = build_recommendations(context, issue_output.missing_information)
        citations = dedupe([*grounding_citations(grounding), *context.precedents, *authority_leads, *hooks])[:8]
        title = f"Research note - {selected_issue}"
        query = f"{selected_issue} in {context.matter_type.lower()} before {context.forum}"
        content = (
            f"Issue\n{selected_issue}\n\n"
            f"Analysis Direction\n- " + "\n- ".join(analysis_direction) + "\n\n"
            f"Retrieved Legal Basis\n- " + "\n- ".join(grounding_basis_lines(grounding) or ["No sufficiently relevant retrieved legal source was available."]) + "\n\n"
            f"Potential Authorities\n- " + "\n- ".join(citations) + "\n\n"
            f"Statutory Hooks\n- " + "\n- ".join(dedupe(hooks)) + "\n\n"
            f"Factual Dependencies\n- " + "\n- ".join(factual_dependencies) + "\n\n"
            f"Next Research Steps\n- " + "\n- ".join(next_steps[:4])
        )
        summary = truncate(
            f"AI-assisted research note for {context.title}. "
            f"Treat listed authorities as verified only where already in the record; placeholder leads remain clearly marked."
        )
        return ResearchOutput(
            title=title,
            query=query,
            summary=summary,
            content=content,
            citations=citations,
            source_type="AI Assisted Chamber Research",
            next_question=next_steps[0] if next_steps else "Verify the most useful authority against the live record.",
            analysis_direction=analysis_direction,
            statutory_hooks=dedupe(hooks),
            factual_dependencies=factual_dependencies,
            next_steps=next_steps[:5],
            confidence_score=0.66 if context.documents else 0.52,
        )

    def _section_note(self, section: str, context: CaseContext, issue_output: IssueOutput) -> str:
        lowered = section.casefold()
        if "jurisdiction" in lowered or "maintainability" in lowered:
            return truncate(
                "Keep the objection anchored to the forum, alternate remedy position, and any visible record gap "
                f"in {context.case_number}. Main chamber issue: {issue_output.legal_issues[0] if issue_output.legal_issues else 'maintainability remains provisional'}."
            )
        if "facts" in lowered or "chronology" in lowered:
            return truncate(build_factual_summary(context))
        if "risk" in lowered or "gap" in lowered:
            return truncate(issue_output.missing_information[0] if issue_output.missing_information else "Record gaps are currently limited in the extracted materials.")
        if "prayer" in lowered:
            return truncate(
                "Align the relief section with the stored relief sought and avoid expanding beyond the present documentary footing."
            )
        return truncate(
            f"Use the stored matter posture, current stage ({context.filing_stage}), and live issues ({', '.join(issue_output.legal_issues[:2])}) to develop this section."
        )


@lru_cache
def get_generation_provider() -> ChamberGenerationProvider:
    provider_name = settings.llm_provider.strip().casefold()
    if provider_name in {"local", "openai"}:
        # The newer Research & Draft pipeline uses the safe OpenAI provider above.
        # Legacy chamber/intelligence agents keep their deterministic local provider
        # so enabling OPENAI_API_KEY cannot crash older MVP workflows.
        return LocalChamberProvider()
    raise ValueError(f"Unsupported LLM provider '{settings.llm_provider}'.")
