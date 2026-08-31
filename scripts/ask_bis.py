#!/usr/bin/env python3
"""
Interactive CLI for asking questions against the BIS Knowledge Base via Phase 4 Grounded RAG.
Usage:
    python scripts/ask_bis.py --question "What is the minimum insulation resistance?"
    python scripts/ask_bis.py --question "What torque applies to GX53 cap?" --as-of 2018-01-01
"""
import argparse
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.rag.pipeline import RAGPipeline
from ai.rag.answer import AnswerFormatter


def main():
    parser = argparse.ArgumentParser(
        description="BIS AI Technical Assistant - Grounded Question Answering CLI"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        required=True,
        help="Technical question regarding Indian Standards (BIS)"
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Optional historical applicability date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top retrieved evidence chunks (default: 5)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw structured JSON RAGAnswer"
    )

    args = parser.parse_args()

    pipeline = RAGPipeline()
    answer = pipeline.answer_question(
        query=args.question,
        top_k=args.top_k,
        as_of_date=args.as_of
    )

    if args.json:
        print(answer.model_dump_json(indent=2))
    else:
        formatter = AnswerFormatter()
        print(formatter.format_terminal_output(answer))


if __name__ == "__main__":
    main()
