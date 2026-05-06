from __future__ import annotations

import re
import unicodedata


ENGLISH_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
MULTILINGUAL_TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u0600-\u06ff]+")
URDU_CHAR_PATTERN = re.compile(r"[\u0600-\u06ff]")
LATIN_CHAR_PATTERN = re.compile(r"[A-Za-z]")
WHITESPACE_PATTERN = re.compile(r"\s+")

ENGLISH_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "under",
    "with",
}

URDU_STOPWORDS = {
    "اور",
    "ہے",
    "ہیں",
    "کی",
    "کے",
    "کو",
    "میں",
    "نے",
    "پر",
    "سے",
    "یہ",
    "وہ",
}

URDU_NORMALIZATION_MAP = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ہ",
        "ۀ": "ہ",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
        "ئ": "ی",
        "ۀ": "ہ",
    }
)


def clean_unicode_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    normalized = normalized.replace("\u200c", " ").replace("\u200f", " ").replace("\ufeff", " ")
    normalized = normalized.translate(URDU_NORMALIZATION_MAP)
    return WHITESPACE_PATTERN.sub(" ", normalized).strip()


def detect_language(value: str) -> str:
    cleaned = clean_unicode_text(value)
    if not cleaned:
        return "Unknown"

    urdu_count = len(URDU_CHAR_PATTERN.findall(cleaned))
    latin_count = len(LATIN_CHAR_PATTERN.findall(cleaned))

    if urdu_count and latin_count:
        urdu_ratio = urdu_count / max(urdu_count + latin_count, 1)
        if 0.3 <= urdu_ratio <= 0.7:
            return "Mixed"
        return "Urdu" if urdu_ratio > 0.5 else "English"
    if urdu_count:
        return "Urdu"
    if latin_count:
        return "English"
    return "Unknown"


def normalize_english_text(value: str) -> str:
    cleaned = clean_unicode_text(value).casefold()
    return " ".join(ENGLISH_TOKEN_PATTERN.findall(cleaned))


def normalize_urdu_text(value: str) -> str:
    cleaned = clean_unicode_text(value)
    return " ".join(
        token
        for token in MULTILINGUAL_TOKEN_PATTERN.findall(cleaned)
        if URDU_CHAR_PATTERN.search(token)
    )


def normalize_text(value: str) -> str:
    cleaned = clean_unicode_text(value)
    tokens: list[str] = []
    for token in MULTILINGUAL_TOKEN_PATTERN.findall(cleaned.casefold()):
        if URDU_CHAR_PATTERN.search(token):
            tokens.append(clean_unicode_text(token))
        else:
            tokens.append(token)
    return " ".join(token for token in tokens if token)


def tokenize(value: str) -> list[str]:
    cleaned = clean_unicode_text(value)
    tokens: list[str] = []
    for token in MULTILINGUAL_TOKEN_PATTERN.findall(cleaned.casefold()):
        if URDU_CHAR_PATTERN.search(token):
            normalized_token = clean_unicode_text(token)
            if normalized_token in URDU_STOPWORDS or len(normalized_token) <= 1:
                continue
            tokens.append(normalized_token)
        else:
            if token in ENGLISH_STOPWORDS or len(token) <= 2:
                continue
            tokens.append(token)
    return tokens


def unique_tokens(value: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokenize(value):
        if token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered
