#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Simple evaluation runner for CppCheck CSV files.

This script provides a convenient interface to run batch evaluations with
pre-configured settings.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Main function for the evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Run batch evaluation on CppCheck CSV file"
    )
    
    parser.add_argument(
        "--csv",
        default="test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv",
        help="CSV file to process (default: test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv)"
    )
    
    parser.add_argument(
        "--output",
        default="results/evaluation_results.json",
        help="Output file (default: results/evaluation_results.json)"
    )
    
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index (default: 0)"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of defects to process (default: 10)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Calculate end index
    end_index = args.start + args.count
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build the command
    cmd = [
        sys.executable,
        "batch_evaluation.py",
        args.csv,
        "-o", args.output,
        "--start-index", str(args.start),
        "--end-index", str(end_index),
        "--max-concurrent", "1",
        "--max_plan_iterations", "1",
        "--max_step_num", "3",
        "--no-background-investigation"
    ]
    
    if args.debug:
        cmd.append("--debug")
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Processing defects {args.start} to {end_index-1} ({args.count} total)")
    print(f"Output will be saved to: {args.output}")
    print("-" * 50)
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print("Evaluation completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Evaluation failed with return code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Evaluation interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main() 