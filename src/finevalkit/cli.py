"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .judge import calibrate_judge, load_judgments
from .observability import log_benchmark_to_wandb
from .pipeline import run_demo
from .retrieval_benchmark import run_embedding_benchmark
from .v2_pipeline import run_v2_demo
from .v3_pipeline import run_v3_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fineval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the deterministic end-to-end evaluation")
    demo.add_argument("--output-dir", default="artifacts")
    v2_demo = subparsers.add_parser(
        "v2-demo", help="run filing, hybrid retrieval, calibration, and monitoring checks"
    )
    v2_demo.add_argument("--output-dir", default="artifacts")
    v3_demo = subparsers.add_parser(
        "v3-demo", help="run real OCR, IFRS/XBRL, and ISO 20022 evaluations"
    )
    v3_demo.add_argument("--output-dir", default="artifacts-v3")
    benchmark = subparsers.add_parser(
        "embedding-benchmark", help="benchmark a Hugging Face embedding model"
    )
    benchmark.add_argument("--dataset-dir", default="data/retrieval_benchmark")
    benchmark.add_argument("--output", default="benchmarks/results/minilm_retrieval.json")
    benchmark.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    benchmark.add_argument("--revision")
    wandb_run = subparsers.add_parser(
        "wandb-run", help="log benchmark metrics to W&B online or offline"
    )
    wandb_run.add_argument("--report", default="benchmarks/results/minilm_retrieval.json")
    wandb_run.add_argument("--summary", default="benchmarks/results/wandb_run.json")
    wandb_run.add_argument("--project", default="finevalkit")
    wandb_run.add_argument("--entity")
    wandb_run.add_argument("--mode", choices=("online", "offline", "disabled"), default="offline")
    wandb_run.add_argument("--output-dir", default="artifacts/wandb")
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
    elif args.command == "v3-demo":
        root = Path(__file__).resolve().parents[2]
        report = run_v3_demo(root, args.output_dir)
        print(
            "Wrote v0.3 evaluation artifacts; "
            f"OCR WER={report['ocr']['word_error_rate']:.3f}; "
            f"IFRS table accuracy={report['ifrs_xbrl']['table_evaluation']['exact_accuracy']:.3f}"
        )
    elif args.command == "embedding-benchmark":
        report = run_embedding_benchmark(
            args.dataset_dir,
            args.output,
            model_name=args.model_name,
            model_revision=args.revision,
        )
        dense = report["results"]["dense"]
        print(f"Wrote embedding benchmark; dense MRR={dense['mean_reciprocal_rank']:.3f}")
    elif args.command == "wandb-run":
        summary = log_benchmark_to_wandb(
            args.report,
            args.summary,
            project=args.project,
            mode=args.mode,
            entity=args.entity,
            directory=args.output_dir,
        )
        print(f"Completed W&B {summary['mode']} run {summary['run_id']}")
    elif args.command == "calibrate-judge":
        report = calibrate_judge(load_judgments(args.input))
        print(f"Judge macro-F1={report['macro_f1']:.3f}; review={len(report['review_queue'])}")


if __name__ == "__main__":
    main()
