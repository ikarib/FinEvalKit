"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fineval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the deterministic end-to-end evaluation")
    demo.add_argument("--output-dir", default="artifacts")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        root = Path(__file__).resolve().parents[2]
        report = run_demo(root, args.output_dir)
        print(f"Wrote evaluation artifacts for {report['run']['case_count']} cases to {args.output_dir}")


if __name__ == "__main__":
    main()
