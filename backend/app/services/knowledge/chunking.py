from __future__ import annotations

from dataclasses import dataclass

from app.services.corpus.chunking import chunk_corpus_text


@dataclass(slots=True)
class ChunkedText:
    chunk_index: int
    heading: str
    text: str
    normalized_text: str
    token_count: int


def chunk_legal_source(
    *,
    content: str,
    heading: str,
    max_characters: int = 700,
) -> list[ChunkedText]:
    return [
        ChunkedText(
            chunk_index=chunk.chunk_index,
            heading=chunk.heading,
            text=chunk.text,
            normalized_text=chunk.normalized_text,
            token_count=chunk.token_count,
        )
        for chunk in chunk_corpus_text(
            content=content,
            heading=heading,
            max_characters=max_characters,
        )
    ]
