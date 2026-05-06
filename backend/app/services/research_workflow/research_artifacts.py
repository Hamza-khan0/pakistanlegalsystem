from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT


ARTIFACT_ROOT = Path(PROJECT_ROOT) / "backend" / "generated" / "research_runs"


def _line_items(title: str, values: list[Any]) -> list[str]:
    lines = [f"## {title}", ""]
    if not values:
        lines.extend(["- Not available.", ""])
        return lines
    for value in values:
        if isinstance(value, dict):
            text = value.get("title") or value.get("query") or value.get("label") or str(value)
            extra = value.get("citation") or value.get("section") or value.get("sourceType") or ""
            lines.append(f"- {text}{f' | {extra}' if extra else ''}")
        else:
            lines.append(f"- {value}")
    lines.append("")
    return lines


def render_research_markdown(response_data: dict[str, Any]) -> str:
    memo = response_data.get("research_memo") or {}
    generated_draft = response_data.get("generated_draft") or {}
    critic = response_data.get("critic_report") or {}
    drafting = response_data.get("drafting_instructions") or {}
    provider_status = response_data.get("provider_status") or {}
    lines = [
        "# AI Legal Chambers Research & Draft Output",
        "",
        f"Run ID: {response_data.get('run_id')}",
        f"Case ID: {response_data.get('case_id')}",
        f"Status: {response_data.get('status')}",
        "",
        f"> {response_data.get('legal_authority_warning') or memo.get('legal_authority_warning') or ''}",
        "",
    ]
    lines.extend(_line_items("Detected Issues", response_data.get("detected_issues", [])))
    lines.extend(_line_items("Research Query Plan", response_data.get("query_plan", [])))
    lines.extend(_line_items("Sources Used", memo.get("source_list", [])))
    lines.extend(_line_items("Factual Basis", memo.get("factual_basis", [])))
    lines.extend(_line_items("Legal Issues", memo.get("legal_issues", [])))
    lines.extend(_line_items("Applicable Statutes", memo.get("applicable_statutes", [])))
    lines.extend(_line_items("Relevant Case Law", memo.get("relevant_case_law", [])))
    lines.extend(_line_items("Procedural Position", memo.get("procedural_position", [])))
    lines.extend(_line_items("Arguments For Client", memo.get("arguments_for_client", [])))
    lines.extend(_line_items("Arguments Against Client", memo.get("arguments_against_client", [])))
    lines.extend(_line_items("Research Gaps", memo.get("research_gaps", [])))
    if generated_draft:
        lines.extend(["## Generated Draft", ""])
        lines.append(f"Draft type: {generated_draft.get('draft_type') or generated_draft.get('draftType')}")
        lines.append("")
        lines.append(str(generated_draft.get("draft_markdown") or generated_draft.get("draftMarkdown") or ""))
        lines.append("")
    lines.extend(["## Drafting Instructions", ""])
    lines.append(f"- Recommended draft type: {drafting.get('selected_draft_type') or memo.get('recommended_draft_type')}")
    for item in drafting.get("core_issues_to_plead", []):
        lines.append(f"- Core issue: {item}")
    for item in drafting.get("risks_to_address", []):
        lines.append(f"- Risk to address: {item}")
    lines.append("")
    lines.extend(["## Critic Review", ""])
    lines.append(f"- Passed: {critic.get('passed')}")
    lines.append(f"- Recommendation: {critic.get('recommendation')}")
    for key, title in [
        ("unsupported_claims", "Unsupported claims"),
        ("fake_or_unverified_citations", "Fake or unverified citations"),
        ("weak_sources", "Weak sources"),
        ("missing_authorities", "Missing authorities"),
        ("drafting_defects", "Drafting defects"),
        ("overclaiming_warnings", "Overclaiming warnings"),
        ("drafting_risks", "Drafting risks"),
        ("required_lawyer_checks", "Required lawyer checks"),
    ]:
        for item in critic.get(key, []):
            lines.append(f"- {title}: {item}")
    lines.append("")
    lines.extend(_line_items("Lawyer Review Checklist", response_data.get("lawyer_review_checklist", [])))
    lines.extend(["## Provider Trace", ""])
    for key, value in provider_status.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
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
    # Keep these ids referenced for reader sanity and to avoid over-aggressive linters.
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


def write_research_artifacts(
    run_id: str,
    response_data: dict[str, Any],
    *,
    generate_pdf: bool = True,
) -> tuple[str, str | None, list[str]]:
    run_dir = ARTIFACT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    markdown = render_research_markdown(response_data)
    markdown_path = run_dir / "research_memo.md"
    markdown_path.write_text(markdown, encoding="utf-8")

    warnings: list[str] = []
    pdf_path: str | None = None
    if generate_pdf:
        try:
            pdf_file = run_dir / "research_memo.pdf"
            _write_basic_pdf(pdf_file, markdown)
            pdf_path = str(pdf_file)
        except Exception as exc:
            warnings.append(f"PDF generation failed; markdown artifact is available. {exc}")

    return str(markdown_path), pdf_path, warnings
