from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT
from app.schemas.research import (
    LEGAL_RESEARCH_WARNING,
    PDF_MODE_DRAFT_ONLY,
    PDF_MODE_DRAFT_WITH_RESEARCH,
    PDF_MODE_FULL_TRACE,
    PDF_MODES,
)
from app.services.research_workflow.draft_storage import normalize_generated_draft


ARTIFACT_ROOT = Path(PROJECT_ROOT) / "backend" / "generated" / "research_runs"


def _line_items(title: str, values: list[Any], *, limit: int = 12) -> list[str]:
    lines = [f"## {title}", ""]
    if not values:
        lines.extend(["- Not available.", ""])
        return lines
    for value in values[:limit]:
        if isinstance(value, dict):
            text = value.get("title") or value.get("query") or value.get("label") or str(value)
            extra = value.get("citation") or value.get("section") or value.get("sourceType") or ""
            lines.append(f"- {text}{f' | {extra}' if extra else ''}")
        else:
            lines.append(f"- {value}")
    lines.append("")
    return lines


def _case_title(response_data: dict[str, Any]) -> str:
    memo = response_data.get("research_memo") or {}
    for item in memo.get("factual_basis", []):
        text = str(item)
        if text.startswith("Case:"):
            return text.replace("Case:", "", 1).strip()
    return str(response_data.get("case_id") or "Legal matter")


def _compact_provider_status(response_data: dict[str, Any]) -> list[str]:
    provider = response_data.get("provider_status") or {}
    return [
        f"- Local corpus: {'Used' if provider.get('localRetrievalUsed', True) else 'Not used'}",
        f"- Live web: {'Used' if response_data.get('live_web_used') else 'Not used / unavailable'}",
        f"- LLM research: {'Used' if response_data.get('llm_used_for_research') else 'Fallback / not used'}",
        f"- LLM drafting: {'Used' if response_data.get('llm_used_for_drafting') else 'Fallback / not used'}",
        f"- Generated at: {response_data.get('completed_at') or response_data.get('created_at') or 'Not recorded'}",
    ]


def _clean_source_title(source: dict[str, Any]) -> str:
    title = str(source.get("title") or "Untitled source").strip()
    citation = str(source.get("citation") or "").strip()
    source_type = str(source.get("source_type") or source.get("sourceType") or "").strip()
    source_text = " ".join([title, citation, str(source.get("excerpt") or "")]).casefold()
    if "demo" in source_text:
        title = f"{title} (DEMO ONLY - verify before use)"
    parts = [title]
    if citation:
        parts.append(citation)
    if source_type:
        parts.append(source_type)
    return " | ".join(parts)


def _source_lines(response_data: dict[str, Any], *, limit: int = 16) -> list[str]:
    sources_by_origin = response_data.get("sources_by_origin") or {}
    sources = response_data.get("retrieved_sources") or []
    grouped = sources_by_origin if isinstance(sources_by_origin, dict) and sources_by_origin else {"all": sources}
    lines: list[str] = []
    for origin, values in grouped.items():
        if not isinstance(values, list) or not values:
            continue
        lines.append(f"### {str(origin).replace('_', ' ').title()}")
        lines.append("")
        for source in values[:limit]:
            if not isinstance(source, dict):
                continue
            source_type = str(source.get("source_type") or source.get("sourceType") or "").casefold()
            title_url = " ".join([str(source.get("title") or ""), str(source.get("url") or "")]).casefold()
            if source_type == "unknown" and not (source.get("citation") or source.get("statute") or source.get("section")):
                continue
            if any(marker in title_url for marker in ("judge profile", "/judge", "biography", "cause-list", "cause_list")):
                continue
            confidence = source.get("confidence")
            url = str(source.get("url") or "").split("?", 1)[0]
            url_note = f" URL: {url}" if url and len(url) < 140 else ""
            confidence_note = f" Confidence: {confidence}" if confidence not in (None, "") else ""
            lines.append(f"- {_clean_source_title(source)}.{confidence_note}{url_note}")
        lines.append("")
    return lines or ["- No sources were retained for the client-facing packet.", ""]


def _research_summary_lines(memo: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, title in [
        ("factual_basis", "Factual Basis"),
        ("legal_issues", "Legal Issues"),
        ("arguments_for_client", "Arguments Supporting Client"),
        ("arguments_against_client", "Risks / Arguments Against Client"),
        ("research_gaps", "Research Gaps"),
    ]:
        values = [str(item) for item in memo.get(key, []) if str(item).strip()]
        if not values:
            continue
        lines.append(f"### {title}")
        lines.append("")
        for item in values[:8]:
            lines.append(f"- {item}")
        lines.append("")
    return lines or ["- Research summary was not available.", ""]


def _critic_lines(critic: dict[str, Any]) -> list[str]:
    lines = [
        f"- Status: {'Passed' if critic.get('passed') else 'Needs Lawyer Review'}",
        f"- Severity: {critic.get('severity') or 'medium'}",
        f"- Recommendation: {critic.get('recommendation') or 'Review required.'}",
        "",
    ]
    grouped = [
        ("fake_or_unverified_citations", "Unverified or weak citations"),
        ("weak_sources", "Weak sources"),
        ("missing_authorities", "Missing authorities"),
        ("drafting_defects", "Drafting defects"),
        ("drafting_risks", "Drafting risks"),
        ("required_lawyer_checks", "Required lawyer checks"),
    ]
    for key, title in grouped:
        items = [str(item) for item in critic.get(key, []) if str(item).strip()]
        if not items:
            continue
        lines.append(f"### {title}")
        lines.append("")
        for index, item in enumerate(items[:8], start=1):
            lines.append(f"{index}. {item}")
        lines.append("")
    return lines


def _full_trace_lines(response_data: dict[str, Any]) -> list[str]:
    safe_trace = {
        "providerStatus": response_data.get("provider_status") or {},
        "warnings": response_data.get("warnings") or [],
        "queryPlan": response_data.get("query_plan") or [],
        "detectedIssues": response_data.get("detected_issues") or [],
    }
    return ["## Developer Full Trace", "", "```json", str(safe_trace), "```", ""]


def render_research_markdown(
    response_data: dict[str, Any],
    *,
    pdf_mode: str = PDF_MODE_DRAFT_WITH_RESEARCH,
) -> str:
    if pdf_mode not in PDF_MODES:
        pdf_mode = PDF_MODE_DRAFT_WITH_RESEARCH

    memo = response_data.get("research_memo") or {}
    generated_draft = normalize_generated_draft(response_data.get("generated_draft") or {}) or {}
    critic = response_data.get("critic_report") or {}
    privacy_notice = response_data.get("privacy_notice") or ""
    final_draft = str(generated_draft.get("final_draft_markdown") or generated_draft.get("draft_markdown") or "")
    draft_type = str(generated_draft.get("draft_type") or "research_memo")

    lines = [
        "# AI Legal Chambers",
        "# Research & Draft Output",
        "",
        f"Document Type: {draft_type.replace('_', ' ').title()}",
        f"Case: {_case_title(response_data)}",
        f"Run ID: {response_data.get('run_id') or 'Not recorded'}",
        f"Generated: {response_data.get('completed_at') or response_data.get('created_at') or 'Not recorded'}",
        "",
        "## Legal Warning",
        "",
        f"> {response_data.get('legal_authority_warning') or memo.get('legal_authority_warning') or LEGAL_RESEARCH_WARNING}",
        "",
        "## Case Details",
        "",
        f"- Case ID: {response_data.get('case_id')}",
        f"- Run status: {response_data.get('status')}",
        f"- Draft status: {'Edited draft' if generated_draft.get('edited_draft_markdown') else 'Original generated draft'}",
        f"- Last edited: {generated_draft.get('last_edited_at') or 'Not edited'}",
        "",
        "## Provider Summary",
        "",
        *_compact_provider_status(response_data),
        "",
        "---",
        "",
        "# FINAL LEGAL DRAFT - LAWYER REVIEW REQUIRED",
        "",
        final_draft or "No final legal draft was generated for this run.",
        "",
    ]

    checklist = list(
        dict.fromkeys(
            list(generated_draft.get("lawyer_review_checklist") or [])
            + list(response_data.get("lawyer_review_checklist") or [])
        )
    )
    lines.extend(_line_items("Lawyer Review Checklist", checklist, limit=12))

    if pdf_mode in {PDF_MODE_DRAFT_WITH_RESEARCH, PDF_MODE_FULL_TRACE}:
        lines.extend(["---", "", "# ANNEXURE A - Research Summary", ""])
        lines.extend(_research_summary_lines(memo))
        lines.extend(["# ANNEXURE B - Authorities / Sources Considered", ""])
        lines.extend(_source_lines(response_data))
        lines.extend(["# ANNEXURE C - Critic Warnings", ""])
        lines.extend(_critic_lines(critic))

    if pdf_mode == PDF_MODE_FULL_TRACE:
        lines.extend(_full_trace_lines(response_data))
        if privacy_notice:
            lines.extend(["## Privacy Notice", "", f"> {privacy_notice}", ""])

    return "\n".join(lines).strip() + "\n"


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_basic_pdf(path: Path, text: str) -> None:
    wrapped: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(raw_line, width=92) or [""])

    pages = [wrapped[index : index + 48] for index in range(0, len(wrapped), 48)] or [[]]
    objects: list[bytes] = []

    def add_object(payload: str) -> int:
        objects.append(payload.encode("latin-1", "replace"))
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object("PLACEHOLDER")
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []
    content_ids: list[int] = []
    for page_lines in pages:
        commands = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
        for line in page_lines:
            commands.append(f"({_pdf_escape(line)}) Tj")
            commands.append("T*")
        commands.append("ET")
        stream = "\n".join(commands)
        content_id = add_object(f"<< /Length {len(stream.encode('latin-1', 'replace'))} >>\nstream\n{stream}\nendstream")
        content_ids.append(content_id)
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids "
        f"[{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] >>"
    ).encode("latin-1")
    _ = (catalog_id, content_ids)

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(payload)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(output)


def _write_reportlab_pdf(path: Path, text: str) -> None:
    from html import escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "LegalPacketTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        textColor=colors.HexColor("#111827"),
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "LegalPacketHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#111827"),
        spaceBefore=11,
        spaceAfter=6,
    )
    subheading_style = ParagraphStyle(
        "LegalPacketSubheading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "LegalPacketBody",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceAfter=5,
    )
    warning_style = ParagraphStyle(
        "LegalPacketWarning",
        parent=body_style,
        fontName="Helvetica",
        leftIndent=6,
        rightIndent=6,
        borderColor=colors.HexColor("#d97706"),
        borderWidth=0.5,
        borderPadding=7,
        textColor=colors.HexColor("#78350f"),
        backColor=colors.HexColor("#fffbeb"),
        spaceAfter=10,
    )

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="AI Legal Chambers Research & Draft Output",
    )

    story: list[Any] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue
        if line == "---":
            story.append(PageBreak())
            continue
        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), title_style))
            continue
        if line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), heading_style))
            continue
        if line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), subheading_style))
            continue
        if line.startswith("> "):
            story.append(Paragraph(escape(line[2:]), warning_style))
            continue
        story.append(Paragraph(escape(line), body_style))

    def _page_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(22 * mm, 10 * mm, "AI Legal Chambers - lawyer review required")
        canvas.drawRightString(188 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)


def write_research_pdf(path: Path, markdown: str) -> None:
    try:
        _write_reportlab_pdf(path, markdown)
    except Exception:
        _write_basic_pdf(path, markdown)


def write_research_artifacts(
    run_id: str,
    response_data: dict[str, Any],
    *,
    generate_pdf: bool = True,
    pdf_mode: str = PDF_MODE_DRAFT_WITH_RESEARCH,
) -> tuple[str, str | None, list[str]]:
    if pdf_mode not in PDF_MODES:
        pdf_mode = PDF_MODE_DRAFT_WITH_RESEARCH

    run_dir = ARTIFACT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    markdown = render_research_markdown(response_data, pdf_mode=pdf_mode)
    markdown_path = run_dir / "research_memo.md"
    markdown_path.write_text(markdown, encoding="utf-8")

    warnings: list[str] = []
    pdf_path: str | None = None
    if generate_pdf:
        try:
            pdf_file = run_dir / "research_output.pdf"
            write_research_pdf(pdf_file, markdown)
            pdf_path = str(pdf_file)
        except Exception as exc:
            warnings.append(f"PDF generation failed; markdown artifact is available. {exc}")

    return str(markdown_path), pdf_path, warnings
