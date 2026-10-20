"""Fast typed routing with the OpenAI Decisions API."""

from dataclasses import dataclass
from pathlib import Path
import base64
import mimetypes

from openai import OpenAI

MODEL = "gpt-6-luna"

QUESTIONS = [
    {
        "type": "choice",
        "name": "kind",
        "instructions": "What is this input, as a piece of information?",
        "choices": [
            {
                "value": "factual_claim",
                "description": "A sincere statement about the world that could be true or false",
            },
            {
                "value": "opinion",
                "description": "Taste, preference, or a value judgement, not a checkable fact",
            },
            {
                "value": "satire",
                "description": "Joke, parody, meme, or fake-news humour, not a sincere report",
            },
            {
                "value": "personal",
                "description": "A private story or feeling, not a public fact",
            },
            {
                "value": "not_a_claim",
                "description": "Greeting, question with no assertion, or unrelated text",
            },
        ],
    },
    {
        "type": "predicate",
        "name": "checkable",
        "instructions": "Wikipedia or a news source could confirm or deny this statement as true or false",
    },
    {
        "type": "predicate",
        "name": "satirical",
        "instructions": "The wording or image is parody, meme humour, or satirical news rather than a sincere claim",
    },
    {
        "type": "score",
        "name": "alarm",
        "instructions": "How alarmist or sensational is the wording?",
        "levels": [
            {"label": "Calm", "description": "Ordinary wording, no urgency."},
            {"label": "Emphatic", "description": "Strong language, but not panic."},
            {"label": "Alarmist", "description": "BREAKING, MUST READ, panic, conspiracy tone."},
        ],
    },
]


@dataclass
class Decision:
    kind: str
    kind_confidence: float
    checkable: float
    satirical: float
    alarm: float


def _image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    blob = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{blob}"


def _input(text: str | None, image: Path | None):
    if image is None:
        return text or ""
    parts = [
        {
            "type": "input_text",
            "text": text or "Read any headline, caption, or claim visible in this image.",
        },
        {"type": "input_image", "image_url": _image_data_url(image)},
    ]
    return [{"role": "user", "content": parts}]


def _named(decision) -> dict:
    return {answer.name: answer for answer in decision.answers}


def classify(client: OpenAI, text: str | None = None, image: Path | None = None) -> Decision:
    response = client.decisions.create(model=MODEL, input=_input(text, image), questions=QUESTIONS)
    answers = _named(response)
    kind = answers["kind"]
    return Decision(
        kind=str(kind.choice),
        kind_confidence=float(kind.confidence),
        checkable=float(answers["checkable"].probability),
        satirical=float(answers["satirical"].probability),
        alarm=float(answers["alarm"].score),
    )
