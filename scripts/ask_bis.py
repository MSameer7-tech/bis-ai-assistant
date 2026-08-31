#!/usr/bin/env python3
"""
Interactive CLI for asking questions against the BIS Knowledge Base via Phase 4 Grounded RAG.
Usage:
    python scripts/ask_bis.py --question "What is the minimum insulation resistance?"
    python scripts/ask_bis.py --question "What torque applies to GX53 cap?" --as-of 2018-01-01
    python scripts/ask_bis.py  # Launches interactive REPL
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


def interactive_repl(pipeline: RAGPipeline, formatter: AnswerFormatter):
    print("=" * 80)
    print("🤖 BIS AI TECHNICAL ASSISTANT - INTERACTIVE REPL")
    print("   Bureau of Indian Standards Grounded Intelligence")
    print("   Type your technical question, or 'exit' / 'quit' to exit.")
    print("   Type '--as-of YYYY-MM-DD <question>' to specify historical date.")
    print("=" * 80)

    while True:
        try:
            user_input = input("\nBIS-AI> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            as_of_date = None
            if user_input.startswith("--as-of"):
                parts = user_input.split(" ", 2)
                if len(parts) >= 3:
                    as_of_date = parts[1]
                    user_input = parts[2]

            print(f"\n🔍 Querying Knowledge Base (as of: {as_of_date or 'Current Effective'})...")
            answer = pipeline.answer_question(
                query=user_input,
                as_of_date=as_of_date
            )
            print(formatter.format_terminal_output(answer))
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="BIS AI Technical Assistant - Grounded Question Answering CLI"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=None,
        help="Technical question regarding Indian Standards (BIS). If omitted, starts interactive REPL."
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
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Launch interactive terminal REPL"
    )

    args = parser.parse_args()

    pipeline = RAGPipeline()
    formatter = AnswerFormatter()

    if not args.question or args.interactive:
        interactive_repl(pipeline, formatter)
    else:
        answer = pipeline.answer_question(
            query=args.question,
            top_k=args.top_k,
            as_of_date=args.as_of
        )
        if args.json:
            print(answer.model_dump_json(indent=2))
        else:
            print(formatter.format_terminal_output(answer))


if __name__ == "__main__":
    main()
