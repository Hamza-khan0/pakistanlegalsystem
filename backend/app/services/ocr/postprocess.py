from __future__ import annotations

import re


MULTISPACE_PATTERN = re.compile(r"[ \t]+")
MULTIBREAK_PATTERN = re.compile(r"\n{3,}")


def clean_extracted_text(value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [MULTISPACE_PATTERN.sub(" ", line).strip() for line in text.split("\n")]
    compact = "\n".join(line for line in lines if line)
    return MULTIBREAK_PATTERN.sub("\n\n", compact).strip()
