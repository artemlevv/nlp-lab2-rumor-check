"""Run the rumor cases and print a small score table."""

import json
from pathlib import Path

from dotenv import load_dotenv

from app.judge import Writer
from app.pipeline import process

CASES_PATH = Path("data/eval_cases.json")


def _passed(case: dict, result) -> bool:
    return result.judgement.verdict.lower() == case["expected_verdict"]


def main() -> None:
    load_dotenv()
    writer = Writer()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    scored = 0
    known_failures = []
    print(f"{'id':<22} {'expect':<16} {'got':<16} result")
    for case in cases:
        image = Path(case["image"]) if case.get("image") else None
        result = process(writer, text=case.get("text"), image=image)
        ok = _passed(case, result)
        if case.get("expect_fail"):
            known_failures.append((case, result, ok))
            mark = "expected fail" if not ok else "unexpected pass"
        else:
            scored += ok
            mark = "pass" if ok else "fail"
        print(
            f"{case['id']:<22} {case['expected_verdict']:<16} "
            f"{result.judgement.verdict:<16} {mark}"
        )

    n = sum(1 for c in cases if not c.get("expect_fail"))
    print(f"\nScore: {scored}/{n} regular cases")
    print("Known limitation: reprinted copies of the same rumour are treated as independent sources.")
    for case, result, ok in known_failures:
        print(f"- {case['id']}: {case['notes']}")
        print(f"  kind={result.decision.kind} verdict={result.judgement.verdict}")
        print(f"  {result.judgement.explanation}")


if __name__ == "__main__":
    main()
