"""
One-Click End-to-End Orchestration Pipeline for Air Quality vs. Hospital Admission Analysis.
Usage:
    python run_pipeline.py --all           # Runs data generation, analytics, and reporting
    python run_pipeline.py --app           # Launches Streamlit dashboard
    python run_pipeline.py --report        # Generates comprehensive report (.docx & .md)
    python run_pipeline.py --test          # Runs pytest validation suite
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
APP_PATH = BASE_DIR / "app" / "app.py"

def main():
    parser = argparse.ArgumentParser(description="Air Quality vs. Hospital Admission Analysis Pipeline")
    parser.add_argument("--all", action="store_true", help="Run end-to-end pipeline (Data + Analytics + Reports)")
    parser.add_argument("--data", action="store_true", help="Generate 200k+ master dataset")
    parser.add_argument("--analytics", action="store_true", help="Run health impact metrics & lag statistical engine")
    parser.add_argument("--report", action="store_true", help="Generate Word (.docx) and Markdown reports")
    parser.add_argument("--app", action="store_true", help="Launch interactive Streamlit dashboard")
    parser.add_argument("--test", action="store_true", help="Run pytest verification suite")

    args = parser.parse_args()

    # Default if no arguments provided
    if not any(vars(args).values()):
        args.all = True

    if args.all or args.data:
        print("\n>>> Step 1: Generating 200,000+ Master Dataset...")
        subprocess.run([sys.executable, str(SRC_DIR / "generate_200k_dataset.py")], check=True)

    if args.all or args.analytics:
        print("\n>>> Step 2: Computing Health Impact Metrics & Lag Analysis...")
        subprocess.run([sys.executable, str(SRC_DIR / "metrics_and_stats.py")], check=True)

    if args.all or args.report:
        print("\n>>> Step 3: Generating Publication-Grade Word & Markdown Reports...")
        subprocess.run([sys.executable, str(SRC_DIR / "generate_report.py")], check=True)

    if args.test:
        print("\n>>> Running Automated Verification Test Suite...")
        subprocess.run(["pytest", "tests/test_pipeline.py", "-v"], check=True)

    if args.app:
        print("\n>>> Launching Streamlit Interactive Dashboard...")
        subprocess.run(["streamlit", "run", str(APP_PATH)])

if __name__ == "__main__":
    main()
