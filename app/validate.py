"""Citations must point at retrieved sources and overlap with them."""

import re

from .judge import Judgement
from .search import Source

OK_WITHOUT_SOURCES = {"not_checkable", "insufficient"}


def validate(judgement: Judgement, sources: list[Source]) -> list[str]:
    errors = []
    allowed = {source.id for source in sources}
    known = {label.lower() for label in ("supported", "refuted", "insufficient", "not_checkable")}

    if judgement.verdict.lower() not in known:
        errors.append(f"unknown verdict: {judgement.verdict}")
    if not judgement.explanation.strip():
        errors.append("explanation is empty")

    unknown = [cid for cid in judgement.cited_ids if cid not in allowed]
    if unknown:
        errors.append(f"unknown citations: {unknown}")

    label = judgement.verdict.lower()
    if label in {"supported", "refuted"}:
        if not judgement.cited_ids:
            errors.append("supported/refuted answers must cite a source")
        elif sources:
            cited = " ".join(s.text for s in sources if s.id in judgement.cited_ids)
            if _overlap(judgement.explanation, cited) < 2:
                errors.append("explanation does not overlap with the cited sources")

    if label not in OK_WITHOUT_SOURCES and not sources:
        errors.append("no sources were retrieved for a checkable claim")

    return errors


def _overlap(answer: str, source: str) -> int:
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are",
        "this", "that", "with", "from", "it", "as", "be", "not",
        "чи", "на", "у", "в", "і", "та", "це", "як", "про",
    }
    words = set(re.findall(r"[a-zа-яіїєґ0-9%]+", answer.lower())) - stop
    source_words = set(re.findall(r"[a-zа-яіїєґ0-9%]+", source.lower()))
    return len(words & source_words)
