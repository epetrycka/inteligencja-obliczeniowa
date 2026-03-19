import argparse
from pathlib import Path

from .experiments import print_summary, run_experiments


def parse_args():
    parser = argparse.ArgumentParser(description="Run Nim/Nimby experiments for lab_01.")
    parser.add_argument(
        "--out",
        default="lab_01/results.json",
        help="Output JSON path (default: lab_01/results.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    out_path = Path(args.out)
    results = run_experiments(out_path)
    print_summary(results)
    print(f"\nSaved results to: {out_path}")
