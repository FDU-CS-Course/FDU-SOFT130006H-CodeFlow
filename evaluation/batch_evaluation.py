#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Batch evaluation script for processing CppCheck defect reports.

This script processes a CSV file containing CppCheck defect reports and runs
evaluation using the DeerFlow analysis workflow.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Add the project root to sys.path to import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflow import run_cppcheck_analysis_async


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug: If True, enables debug level logging
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'evaluation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def parse_cppcheck_csv(csv_path: str) -> List[Dict[str, str]]:
    """Parse CppCheck CSV file and extract defect records.
    
    Args:
        csv_path: Path to the CSV file containing CppCheck defect reports
        
    Returns:
        List of dictionaries containing defect information
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    defects = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate required columns
            required_columns = {'File', 'Line', 'Severity', 'Id', 'Summary'}
            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(f"CSV must contain columns: {required_columns}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                try:
                    # Clean and validate the data
                    file_path = row['File'].strip()
                    line_str = row['Line'].strip()
                    severity = row['Severity'].strip()
                    defect_id = row['Id'].strip()
                    summary = row['Summary'].strip()
                    
                    # Skip empty rows
                    if not all([file_path, line_str, severity, defect_id, summary]):
                        logging.warning(f"Skipping row {row_num}: Missing required fields")
                        continue
                    
                    # Validate line number
                    try:
                        line_num = int(line_str)
                        if line_num <= 0:
                            raise ValueError("Line number must be positive")
                    except ValueError as e:
                        logging.error(f"Invalid line number at row {row_num}: {line_str} - {e}")
                        continue
                    
                    # Create defect record
                    defect = {
                        'file': file_path,
                        'line': line_num,
                        'severity': severity,
                        'id': defect_id,
                        'summary': summary,
                        'row_number': row_num
                    }
                    
                    # Add optional fields if available
                    if 'Category' in row and row['Category'].strip():
                        defect['category'] = row['Category'].strip()
                    if 'Ours' in row and row['Ours'].strip():
                        defect['ours'] = row['Ours'].strip()
                    if 'Baseline' in row and row['Baseline'].strip():
                        defect['baseline'] = row['Baseline'].strip()
                    
                    defects.append(defect)
                    
                except Exception as e:
                    logging.error(f"Error processing row {row_num}: {e}")
                    continue
                    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    
    logging.info(f"Successfully parsed {len(defects)} defects from {csv_path}")
    return defects


async def analyze_single_defect(
    defect: Dict[str, Any],
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = False
) -> Dict[str, Any]:
    """Analyze a single defect using the DeerFlow workflow.
    
    Args:
        defect: Dictionary containing defect information
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        logging.info(f"Analyzing defect: {defect['file']}:{defect['line']} - {defect['id']}")
        
        # Prepare CppCheck data for the workflow
        cppcheck_data = {
            'file': defect['file'],
            'line': defect['line'],
            'severity': defect['severity'],
            'id': defect['id'],
            'summary': defect['summary']
        }
        
        # Run the analysis workflow
        result = await run_cppcheck_analysis_async(
            cppcheck_data=cppcheck_data,
            debug=debug,
            max_plan_iterations=max_plan_iterations,
            max_step_num=max_step_num,
            enable_background_investigation=enable_background_investigation,
        )
        
        # Extract analysis content from the result
        analysis_content = ""
        if result and "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                analysis_content = final_message.content
            elif isinstance(final_message, dict) and "content" in final_message:
                analysis_content = final_message["content"]
        
        # Try to extract JSON summary from the content
        json_summary = None
        if analysis_content:
            try:
                import re
                json_match = re.search(r'```json\s*({.*?})\s*```', analysis_content, re.DOTALL)
                if json_match:
                    json_summary = json.loads(json_match.group(1))
            except Exception as e:
                logging.warning(f"Could not extract JSON summary for defect {defect['row_number']}: {e}")
        
        # Prepare the result
        analysis_result = {
            'defect': defect,
            'status': 'success',
            'analysis_content': analysis_content,
            'json_summary': json_summary,
            'raw_result': result
        }
        
        logging.info(f"Successfully analyzed defect at row {defect['row_number']}")
        return analysis_result
        
    except Exception as e:
        logging.error(f"Error analyzing defect at row {defect['row_number']}: {e}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        
        return {
            'defect': defect,
            'status': 'error',
            'error': str(e),
            'analysis_content': None,
            'json_summary': None,
            'raw_result': None
        }


async def batch_analyze_defects(
    defects: List[Dict[str, Any]],
    output_file: str,
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = False,
    max_concurrent: int = 1,
    start_index: int = 0,
    end_index: Optional[int] = None
) -> None:
    """Batch analyze defects and save results.
    
    Args:
        defects: List of defect dictionaries to analyze
        output_file: Path to save the analysis results
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning
        max_concurrent: Maximum number of concurrent analyses
        start_index: Index to start processing from (0-based)
        end_index: Index to stop processing at (exclusive, None for end)
    """
    # Slice the defects list based on start and end indices
    if end_index is None:
        end_index = len(defects)
    
    defects_to_process = defects[start_index:end_index]
    total_defects = len(defects_to_process)
    
    logging.info(f"Processing {total_defects} defects (indices {start_index} to {end_index-1})")
    
    results = []
    completed = 0
    
    # Process defects with controlled concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_with_semaphore(defect: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await analyze_single_defect(
                defect=defect,
                debug=debug,
                max_plan_iterations=max_plan_iterations,
                max_step_num=max_step_num,
                enable_background_investigation=enable_background_investigation
            )
    
    # Create tasks for all defects
    tasks = [analyze_with_semaphore(defect) for defect in defects_to_process]
    
    # Process tasks and collect results
    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            results.append(result)
            completed += 1
            
            # Log progress
            logging.info(f"Progress: {completed}/{total_defects} defects completed ({completed/total_defects*100:.1f}%)")
            
            # Save intermediate results every 10 defects
            if completed % 10 == 0 or completed == total_defects:
                save_results(results, output_file, completed, total_defects)
                
        except Exception as e:
            logging.error(f"Task failed: {e}")
            completed += 1
    
    # Final save
    save_results(results, output_file, completed, total_defects)
    logging.info(f"Batch analysis completed. Results saved to {output_file}")


def save_results(
    results: List[Dict[str, Any]], 
    output_file: str, 
    completed: int, 
    total: int
) -> None:
    """Save analysis results to a JSON file.
    
    Args:
        results: List of analysis results
        output_file: Path to save the results
        completed: Number of completed analyses
        total: Total number of defects
    """
    try:
        # Prepare metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_defects': total,
            'completed_defects': completed,
            'success_count': sum(1 for r in results if r['status'] == 'success'),
            'error_count': sum(1 for r in results if r['status'] == 'error'),
        }
        
        # Create the final output structure
        output_data = {
            'metadata': metadata,
            'results': results
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
        logging.info(f"Saved {len(results)} results to {output_file}")
        
    except Exception as e:
        logging.error(f"Error saving results: {e}")


def main():
    """Main function for the batch evaluation script."""
    parser = argparse.ArgumentParser(
        description="Batch evaluation of CppCheck defect reports using DeerFlow"
    )
    
    # Required arguments
    parser.add_argument(
        "csv_file",
        default="evaluation/test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv",
        help="Path to the CSV file containing CppCheck defect reports"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="evaluation_results.json",
        help="Output file for analysis results (default: evaluation_results.json)"
    )
    
    # Analysis parameters
    parser.add_argument(
        "--max_plan_iterations",
        type=int,
        default=1,
        help="Maximum number of plan iterations (default: 1)"
    )
    
    parser.add_argument(
        "--max_step_num",
        type=int,
        default=3,
        help="Maximum number of steps in a plan (default: 3)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--no-background-investigation",
        action="store_false",
        dest="enable_background_investigation",
        help="Disable background investigation before planning"
    )
    
    # Batch processing parameters
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=1,
        help="Maximum number of concurrent analyses (default: 1)"
    )
    
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Index to start processing from (0-based, default: 0)"
    )
    
    parser.add_argument(
        "--end-index",
        type=int,
        help="Index to stop processing at (exclusive, default: process all)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    try:
        # Parse the CSV file
        logging.info(f"Parsing CSV file: {args.csv_file}")
        defects = parse_cppcheck_csv(args.csv_file)
        
        if not defects:
            logging.error("No valid defects found in CSV file")
            sys.exit(1)
        
        # Validate indices
        if args.start_index < 0 or args.start_index >= len(defects):
            logging.error(f"Invalid start index: {args.start_index} (must be 0-{len(defects)-1})")
            sys.exit(1)
        
        if args.end_index is not None:
            if args.end_index <= args.start_index or args.end_index > len(defects):
                logging.error(f"Invalid end index: {args.end_index} (must be {args.start_index+1}-{len(defects)})")
                sys.exit(1)
        
        # Run batch analysis
        logging.info("Starting batch analysis...")
        asyncio.run(batch_analyze_defects(
            defects=defects,
            output_file=args.output,
            debug=args.debug,
            max_plan_iterations=args.max_plan_iterations,
            max_step_num=args.max_step_num,
            enable_background_investigation=args.enable_background_investigation,
            max_concurrent=args.max_concurrent,
            start_index=args.start_index,
            end_index=args.end_index
        ))
        
        logging.info("Batch evaluation completed successfully!")
        
    except KeyboardInterrupt:
        logging.info("Batch evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Batch evaluation failed: {e}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()