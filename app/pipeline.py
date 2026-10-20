"""Decide → extract claim → search → judge → validate, with one retry."""

from dataclasses import dataclass, field
from pathlib import Path

from .decide import Decision, classify
from .judge import Judgement, Writer
from .search import Source, search
from .validate import validate

SKIP_KINDS = {"opinion", "personal", "not_a_claim"}


@dataclass
class Result:
    text: str | None
    image: str | None
    decision: Decision
    claim: str
    query: str
    sources: list[Source]
    judgement: Judgement
    retries: int
    errors: list[str] = field(default_factory=list)


def process(writer: Writer, text: str | None = None, image: Path | None = None) -> Result:
    client = writer.client
    decision = classify(client, text=text, image=image)
    extracted = writer.extract_claim(text, image)
    claim = extracted.claim
    query = extracted.search_query

    skip_search = decision.kind in SKIP_KINDS

    sources: list[Source] = [] if skip_search else (search(query) or search(claim))
    errors: list[str] = []
    judgement = None
    retries = 0

    for attempt in range(2):
        if skip_search:
            judgement = Judgement(
                verdict="not_checkable",
                explanation=_skip_reason(decision),
                cited_ids=[],
            )
            errors = []
            break

        judgement = writer.judge(claim, sources, errors or None)
        errors = validate(judgement, sources)
        if not errors:
            break
        retries = attempt + 1
        query = writer.rewrite_query(claim, query)
        sources = search(query) or search(claim)

    assert judgement is not None
    return Result(
        text=text,
        image=str(image) if image else None,
        decision=decision,
        claim=claim,
        query=query,
        sources=sources,
        judgement=judgement,
        retries=retries,
        errors=errors,
    )


def _skip_reason(decision: Decision) -> str:
    if decision.satirical > 0.75 or decision.kind == "satire":
        return "Looks like satire, a joke, or a meme, not a sincere public fact."
    if decision.kind == "opinion":
        return "This is an opinion, not a checkable fact."
    if decision.kind == "personal":
        return "This is a personal statement, not a public claim."
    return "There is no specific public fact here to check."
