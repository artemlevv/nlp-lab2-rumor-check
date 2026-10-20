"""Check a rumor, headline, or screenshot against public sources."""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from app.judge import Writer
from app.pipeline import process


def _print(result) -> None:
    d = result.decision
    j = result.judgement
    print(f"Input: {result.image or result.text}")
    print(f"Claim: {result.claim}")
    print(
        f"   Decisions: kind={d.kind} ({d.kind_confidence:.2f}), "
        f"checkable={d.checkable:.2f}, satirical={d.satirical:.2f}, alarm={d.alarm:.2f}"
    )
    if result.sources:
        print("   Sources:")
        for source in result.sources:
            print(f"     {source.id} [{source.origin}] {source.title} — {source.url}")
    else:
        print("   Sources: none")
    print(f"   Verdict: {j.verdict}")
    print(f"   Why: {j.explanation}")
    if j.cited_ids:
        print(f"   Citations: {', '.join(j.cited_ids)}")
    if result.retries or result.errors:
        print(f"   Retry={result.retries}, errors={result.errors or 'none'}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", help="headline or claim")
    parser.add_argument("--image", type=Path, help="screenshot or photo of a claim")
    parser.add_argument("-i", "--interactive", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    writer = Writer()

    if args.interactive:
        print("Rumor checker. Empty line to quit. Prefix a path with image: to send a screenshot.")
        while True:
            line = input("> ").strip()
            if not line:
                break
            if line.startswith("image:"):
                _print(process(writer, image=Path(line.removeprefix("image:").strip())))
            else:
                _print(process(writer, text=line))
        return

    if not args.text and not args.image:
        parser.error("pass a claim, --image, or --interactive")

    _print(process(writer, text=args.text, image=args.image))


if __name__ == "__main__":
    main()
