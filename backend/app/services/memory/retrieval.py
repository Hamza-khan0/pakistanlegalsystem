from __future__ import annotations

from app.models.case import Case
from app.models.enums import ChamberTaskType
from app.services.orchestration.schemas import MemorySource


def _matches_any(text: str, keywords: list[str]) -> bool:
    lowered = text.casefold()
    return any(keyword in lowered for keyword in keywords)


def _keyword_pack(task_type: ChamberTaskType, instruction: str) -> list[str]:
    base = instruction.casefold()
    keywords: list[str] = []

    if task_type == ChamberTaskType.RESEARCH_MEMO:
        keywords.extend(["research", "authority", "precedent", "statute", "maintainability"])
    elif task_type == ChamberTaskType.PRELIMINARY_OBJECTIONS:
        keywords.extend(["objection", "maintainability", "jurisdiction", "alternate remedy"])
    elif task_type == ChamberTaskType.HEARING_NOTES:
        keywords.extend(["hearing", "bench", "urgency", "oral", "procedure"])
    elif task_type == ChamberTaskType.PROCEDURAL_CHECK:
        keywords.extend(["procedure", "deadline", "filing", "hearing", "maintainability"])
    elif task_type == ChamberTaskType.DRAFT_REVIEW:
        keywords.extend(["draft", "review", "revise", "memo"])
    elif task_type == ChamberTaskType.DRAFT_OUTLINE:
        keywords.extend(["draft", "petition", "reply", "objections", "memo"])
    elif task_type == ChamberTaskType.ISSUE_SPOTTING:
        keywords.extend(["issue", "risk", "maintainability", "missing"])
    else:
        keywords.extend(["summary", "facts", "procedure", "relief"])

    keywords.extend([token for token in base.split() if len(token) > 5][:6])
    return list(dict.fromkeys(keywords))


def rank_memory_sources(
    case: Case,
    *,
    task_type: ChamberTaskType,
    instruction: str,
) -> list[MemorySource]:
    keywords = _keyword_pack(task_type, instruction)
    ranked: list[tuple[int, MemorySource]] = []

    for artifact in sorted(case.intelligence_artifacts, key=lambda item: item.updated_at, reverse=True):
        haystack = " ".join([artifact.title, artifact.content, str(artifact.structured_json)])
        score = 4 if _matches_any(haystack, keywords) else 2
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=artifact.id,
                    source_type="Intelligence Artifact",
                    title=artifact.title,
                    detail=artifact.artifact_type.value,
                    excerpt=artifact.content[:240],
                ),
            )
        )

    for entry in sorted(case.research_entries, key=lambda item: item.updated_at, reverse=True):
        haystack = " ".join([entry.title, entry.summary, entry.query, " ".join(entry.citations)])
        score = 4 if _matches_any(haystack, keywords) else 2
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=entry.id,
                    source_type="Research Entry",
                    title=entry.title,
                    detail=entry.source_type,
                    excerpt=entry.summary[:240],
                ),
            )
        )

    for draft in sorted(case.drafts, key=lambda item: item.updated_at, reverse=True):
        haystack = " ".join([draft.title, draft.summary, draft.content])
        score = 4 if _matches_any(haystack, keywords) else 2
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=draft.id,
                    source_type="Draft",
                    title=draft.title,
                    detail=f"{draft.draft_type} · v{draft.version}",
                    excerpt=(draft.summary or draft.content)[:240],
                ),
            )
        )

    for note in sorted(case.notes, key=lambda item: item.updated_at, reverse=True):
        haystack = " ".join([note.title, note.content])
        score = 3 if _matches_any(haystack, keywords) else 1
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=note.id,
                    source_type="Note",
                    title=note.title,
                    detail=note.note_type.value,
                    excerpt=note.content[:220],
                ),
            )
        )

    latest_predictions_by_task = {}
    for prediction in sorted(case.predictions, key=lambda item: item.created_at, reverse=True):
        latest_predictions_by_task.setdefault(prediction.task_name, prediction)

    for prediction in latest_predictions_by_task.values():
        model_name = prediction.model.name if prediction.model else "Prediction model"
        haystack = " ".join(
            [
                prediction.task_name.value,
                prediction.predicted_label,
                model_name,
                str(prediction.probabilities_json),
            ]
        )
        score = 4 if _matches_any(haystack, keywords) else 2
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=prediction.id,
                    source_type="Prediction",
                    title=f"{prediction.task_name.value}: {prediction.predicted_label}",
                    detail=f"{model_name} · confidence {prediction.confidence:.2f}",
                    excerpt=prediction.warning_text[:220],
                ),
            )
        )

    for document in sorted(case.documents, key=lambda item: item.upload_date, reverse=True):
        excerpt = (document.extracted_text or document.extracted_text_preview or document.summary)[:240]
        haystack = " ".join([document.name, document.summary, excerpt, " ".join(document.tags)])
        score = 5 if _matches_any(haystack, keywords) else 2
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=document.id,
                    source_type="Document",
                    title=document.name,
                    detail=document.document_type.value,
                    excerpt=excerpt,
                ),
            )
        )

    for run in sorted(case.chamber_runs, key=lambda item: item.started_at, reverse=True):
        haystack = " ".join([run.user_instruction, run.final_summary, run.selected_workflow])
        score = 4 if _matches_any(haystack, keywords) else 1
        ranked.append(
            (
                score,
                MemorySource(
                    source_id=run.id,
                    source_type="Chamber Run",
                    title=run.user_instruction[:90],
                    detail=run.selected_workflow,
                    excerpt=run.final_summary[:240],
                ),
            )
        )

    ranked.sort(key=lambda item: (item[0], item[1].title), reverse=True)
    seen: set[tuple[str, str]] = set()
    ordered: list[MemorySource] = []
    for _, source in ranked:
        key = (source.source_type, source.source_id)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(source)
        if len(ordered) >= 10:
            break

    return ordered
