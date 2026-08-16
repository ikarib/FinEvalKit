"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .judge import calibrate_judge, load_judgments
from .pipeline import run_demo
from .v2_pipeline import run_v2_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fineval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the deterministic end-to-end evaluation")
    demo.add_argument("--output-dir", default="artifacts")
    v2_demo = subparsers.add_parser(
        "v2-demo", help="run filing, hybrid retrieval, calibration, and monitoring checks"
    )
    v2_demo.add_argument("--output-dir", default="artifacts")
    judge = subparsers.add_parser("calibrate-judge", help="compare judge labels to human gold")
    judge.add_argument("input")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        root = Path(__file__).resolve().parents[2]
        report = run_demo(root, args.output_dir)
        print(
            f"Wrote evaluation artifacts for {report['run']['case_count']} cases to {args.output_dir}"
        )
    elif args.command == "v2-demo":
        root = Path(__file__).resolve().parents[2]
        report = run_v2_demo(root, args.output_dir)
        accuracy = report["public_filing"]["table_evaluation"]["exact_accuracy"]
        print(f"Wrote v0.2 evaluation artifacts; filing-table accuracy={accuracy:.3f}")
    elif args.command == "calibrate-judge":
        report = calibrate_judge(load_judgments(args.input))
        print(f"Judge macro-F1={report['macro_f1']:.3f}; review={len(report['review_queue'])}")


if __name__ == "__main__":
    main()
