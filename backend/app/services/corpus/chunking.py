from __future__ import annotations

from dataclasses import dataclass

from app.services.corpus.normalization import detect_language, normalize_text, tokenize


@dataclass(slots=True)
class CorpusChunk:
    chunk_index: int
    heading: str
    text: str
    normalized_text: str
    token_count: int
    language: str


def chunk_corpus_text(
    *,
    content: str,
    heading: str,
    max_characters: int = 900,
) -> list[CorpusChunk]:
    paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [content.strip()]

    chunks: list[CorpusChunk] = []
    buffer: list[str] = []
    current_length = 0

    def flush(index: int) -> None:
        text = "\n\n".join(buffer).strip()
        if not text:
            return
        chunks.append(
            CorpusChunk(
                chunk_index=index,
                heading=heading,
                text=text,
                normalized_text=normalize_text(text),
                token_count=len(tokenize(text)),
                language=detect_language(text),
            )
        )

    chunk_index = 0
    for paragraph in paragraphs:
        if buffer and current_length + len(paragraph) > max_characters:
            flush(chunk_index)
            chunk_index += 1
            buffer = []
            current_length = 0

        buffer.append(paragraph)
        current_length += len(paragraph)

    flush(chunk_index)

    if chunks:
        return chunks

    text = content.strip()
    return [
        CorpusChunk(
            chunk_index=0,
            heading=heading,
            text=text,
            normalized_text=normalize_text(text),
            token_count=len(tokenize(text)),
            language=detect_language(text),
        )
    ]
