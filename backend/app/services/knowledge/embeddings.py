from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from typing import Iterable

import numpy as np
import torch

from app.core.config import settings
from app.services.corpus.normalization import unique_tokens


FAST_EMBEDDING_DIMENSION = 128


@lru_cache(maxsize=1)
def _transformers_module():
    from app.services.ml.training.transformer_runtime import ensure_text_only_transformers_runtime

    ensure_text_only_transformers_runtime()
    from transformers import AutoModel, AutoTokenizer

    return AutoModel, AutoTokenizer


@lru_cache(maxsize=4)
def _load_embedding_stack(model_name: str):
    AutoModel, AutoTokenizer = _transformers_module()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    return tokenizer, model


def _mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    masked_embeddings = last_hidden_state * mask
    summed = masked_embeddings.sum(dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts


def embed_texts(
    texts: Iterable[str],
    *,
    model_name: str | None = None,
    batch_size: int | None = None,
) -> np.ndarray:
    items = [text if text and text.strip() else "legal chamber placeholder" for text in texts]
    if settings.semantic_query_mode.casefold() == "fast":
        return _fast_hash_embeddings(items)

    checkpoint = model_name or settings.ml_embedding_model_name
    tokenizer, model = _load_embedding_stack(checkpoint)
    if not items:
        hidden_size = int(getattr(model.config, "hidden_size", 768))
        return np.zeros((0, hidden_size), dtype=np.float32)

    effective_batch_size = batch_size or settings.semantic_index_batch_size
    vectors: list[np.ndarray] = []

    with torch.no_grad():
        for start in range(0, len(items), effective_batch_size):
            batch = items[start : start + effective_batch_size]
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=settings.ml_transformer_max_length,
                return_tensors="pt",
            )
            outputs = model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
            )
            pooled = _mean_pool(outputs.last_hidden_state, encoded["attention_mask"])
            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.append(normalized.cpu().numpy().astype(np.float32))

    return np.vstack(vectors)


def _fast_hash_embeddings(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, FAST_EMBEDDING_DIMENSION), dtype=np.float32)

    vectors = np.zeros((len(texts), FAST_EMBEDDING_DIMENSION), dtype=np.float32)
    for row_index, text in enumerate(texts):
        tokens = unique_tokens(text) or ["legal", "chamber"]
        for token in tokens:
            digest = sha256(token.encode("utf-8", errors="ignore")).digest()
            bucket = int.from_bytes(digest[:4], "big") % FAST_EMBEDDING_DIMENSION
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vectors[row_index, bucket] += sign
        norm = np.linalg.norm(vectors[row_index])
        if norm > 0:
            vectors[row_index] = vectors[row_index] / norm
    return vectors
