"""Extract a claim and judge it against retrieved sources."""

from pathlib import Path
import json
import mimetypes
import base64
import os

from openai import OpenAI
from pydantic import BaseModel, Field


VerdictLabel = str


class ExtractedClaim(BaseModel):
    claim: str
    search_query: str


class Judgement(BaseModel):
    verdict: str
    explanation: str
    cited_ids: list[str] = Field(default_factory=list)


EXTRACT_PROMPT = (
    "Extract the single main public claim from the user input. "
    "Return JSON with keys claim (one sentence) and search_query "
    "(4-8 words: the main entities, no clickbait, no BREAKING)."
)

JUDGE_PROMPT = (
    "You are a careful fact checker. Use only the numbered sources. "
    "verdict must be one of: supported, refuted, insufficient, not_checkable. "
    "Cite source ids like S1. If sources do not actually settle the claim, "
    "use insufficient. If the input is satire, opinion, or not a fact, use not_checkable. "
    "Reply in the same language as the claim. Return JSON with verdict, explanation, cited_ids."
)


class Writer:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def extract_claim(self, text: str | None, image: Path | None) -> ExtractedClaim:
        user = _user_content(text, image)
        raw = self._json(EXTRACT_PROMPT, user)
        return ExtractedClaim.model_validate(raw)

    def judge(self, claim: str, sources: list, errors: list[str] | None = None) -> Judgement:
        blocks = ["(no sources)"] if not sources else [
            f"[{s.id}] {s.title}\n{s.url}\n{s.text}" for s in sources
        ]
        user = f"Claim:\n{claim}\n\nSources:\n" + "\n\n".join(blocks)
        if errors:
            user += "\n\nPrevious JSON failed checks:\n- " + "\n- ".join(errors)
            user += "\nFix it. Cite only ids from the sources above."
        raw = self._json(JUDGE_PROMPT, user)
        return Judgement.model_validate(raw)

    def rewrite_query(self, claim: str, previous: str) -> str:
        raw = self._json(
            "Suggest a better web/Wikipedia search query. Return JSON with key search_query.",
            f"Claim: {claim}\nPrevious query: {previous}",
        )
        return str(raw.get("search_query") or previous)

    def _json(self, system: str, user) -> dict:
        completion = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(completion.choices[0].message.content)


def _user_content(text: str | None, image: Path | None):
    if image is None:
        return text or ""
    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    b64 = base64.b64encode(image.read_bytes()).decode("ascii")
    parts = []
    if text:
        parts.append({"type": "text", "text": text})
    parts.append({"type": "text", "text": "Extract the visible headline or claim from this image."})
    parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts
