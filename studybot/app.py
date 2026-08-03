from __future__ import annotations

import argparse
from pathlib import Path
import logging
import sys

from .answering import Assistant

LOG_FILE = Path("studybot.log")
DEFAULT_KNOWLEDGE_ROOT = Path("assets") / "knowledge"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StudyBot - a local retrieval-backed assistant")
    parser.add_argument("question", nargs="*", help="Question to answer")
    parser.add_argument("--interactive", action="store_true", help="Prompt for a question in the terminal")
    parser.add_argument("--knowledge-root", default=str(DEFAULT_KNOWLEDGE_ROOT), help="Folder with .md or .txt knowledge files")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved passages to use")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handlers.append(file_handler)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    logger = logging.getLogger("studybot")
    assistant = Assistant(Path(args.knowledge_root))

    def print_answer(answer: object) -> None:
        print(answer.response)
        if answer.evidence:
            print()
            print("Evidence:")
            for sentence in answer.evidence:
                print(f"- {sentence}")

    if args.interactive:
        print("StudyBot is ready. Type a question or 'exit' to quit.")
        while True:
            try:
                question = input("Ask a question: ").strip()
            except EOFError:
                print()
                return 0

            if not question or question.lower() in {"exit", "quit"}:
                return 0

            try:
                answer = assistant.answer(question, top_k=args.top_k)
                logger.info("Answered question", extra={"question": question, "sources": answer.sources, "confidence": answer.confidence})
                print_answer(answer)
                print()
            except Exception as exc:
                logger.exception("Failed to answer question")
                print(f"Error: {exc}")
        return 0

    question = " ".join(args.question).strip()
    if not question:
        logger.warning("Empty question provided")
        print("Please enter a non-empty question.")
        return 1

    try:
        answer = assistant.answer(question, top_k=args.top_k)
        logger.info("Answered question", extra={"question": question, "sources": answer.sources, "confidence": answer.confidence})
    except Exception as exc:
        logger.exception("Failed to answer question")
        print(f"Error: {exc}")
        return 1

    print_answer(answer)
    return 0


def main() -> int:
    return run_cli()
