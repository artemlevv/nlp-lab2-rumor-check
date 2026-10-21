# nlp-lab2-rumor-check

Homework 2 for the NLP Systems course. A rumor checker for headlines, short claims, and screenshots.

The task is grounded fact checking. The system decides whether the input is even a checkable claim, looks up public sources, and returns `supported`, `refuted`, `insufficient`, or `not_checkable`.

## Architecture

1. **Routing (OpenAI Decisions API, `gpt-6-luna`).** One request classifies the input as a factual claim, opinion, satire, personal note, or not a claim. It also scores how checkable, satirical, and alarmist it is. Text and images are both valid input (`app/decide.py`).
2. **Claim extraction.** A regular LLM turns the text or screenshot into one sentence plus a search query (`app/judge.py`).
3. **Tool use.** Wikipedia (and DuckDuckGo if available) fetches short source snippets (`app/search.py`). Opinions and greetings skip search.
4. **Structured judgement + one retry.** The LLM returns JSON with a verdict and source ids. If a citation is fake or the text does not overlap the sources, the query is rewritten and search runs again (`app/validate.py`, `app/pipeline.py`).

## Running

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
```

```bash
.venv/bin/python main.py "The Eiffel Tower is in Berlin."
.venv/bin/python main.py --image data/samples/news_claim_1.jpg
.venv/bin/python eval.py
```

`eval.py` runs text cases plus one known failure: copies of the same rumour are treated as independent sources, so the system often returns `supported` instead of `insufficient`.
