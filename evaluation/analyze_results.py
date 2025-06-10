#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Analysis script for batch evaluation results.

This script analyzes the JSON output from batch evaluations and generates
statistics and reports.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import csv


def load_results(results_file: str) -> Dict[str, Any]:
    """Load evaluation results from JSON file.
    
    Args:
        results_file: Path to the results JSON file
        
    Returns:
        Dictionary containing the results data
        
    Raises:
        FileNotFoundError: If results file doesn't exist
        ValueError: If JSON format is invalid
    """
    if not Path(results_file).exists():
        raise FileNotFoundError(f"Results file not found: {results_file}")
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def analyze_basic_stats(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze basic statistics from the results.
    
    Args:
        results_data: Dictionary containing evaluation results
        
    Returns:
        Dictionary containing basic statistics
    """
    metadata = results_data.get('metadata', {})
    results = results_data.get('results', [])
    
    stats = {
        'total_defects': metadata.get('total_defects', 0),
        'completed_defects': metadata.get('completed_defects', 0),
        'success_count': metadata.get('success_count', 0),
        'error_count': metadata.get('error_count', 0),
        'success_rate': 0.0,
        'completion_rate': 0.0
    }
    
    if stats['completed_defects'] > 0:
        stats['success_rate'] = stats['success_count'] / stats['completed_defects'] * 100
    
    if stats['total_defects'] > 0:
        stats['completion_rate'] = stats['completed_defects'] / stats['total_defects'] * 100
    
    # Analyze defect types
    defect_types = Counter()
    severities = Counter()
    categories = Counter()
    
    for result in results:
        if result.get('status') == 'success':
            defect = result.get('defect', {})
            defect_types[defect.get('id', 'unknown')] += 1
            severities[defect.get('severity', 'unknown')] += 1
            if 'category' in defect:
                categories[defect.get('category')] += 1
    
    stats['defect_types'] = dict(defect_types.most_common(10))
    stats['severities'] = dict(severities)
    stats['categories'] = dict(categories) if categories else {}
    
    return stats


def analyze_json_summaries(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze JSON summaries from successful analyses.
    
    Args:
        results_data: Dictionary containing evaluation results
        
    Returns:
        Dictionary containing JSON summary analysis
    """
    results = results_data.get('results', [])
    
    json_summaries = []
    summary_fields = defaultdict(Counter)
    
    for result in results:
        if result.get('status') == 'success' and result.get('json_summary'):
            json_summary = result['json_summary']
            json_summaries.append(json_summary)
            
            # Analyze fields in JSON summaries
            for key, value in json_summary.items():
                if isinstance(value, str):
                    summary_fields[key][value] += 1
                elif isinstance(value, (int, float)):
                    summary_fields[key]['numeric_values'] += 1
                elif isinstance(value, bool):
                    summary_fields[key][str(value)] += 1
    
    analysis = {
        'total_summaries': len(json_summaries),
        'field_analysis': {k: dict(v) for k, v in summary_fields.items()},
        'common_fields': list(summary_fields.keys())
    }
    
    return analysis


def analyze_errors(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze errors from failed analyses.
    
    Args:
        results_data: Dictionary containing evaluation results
        
    Returns:
        Dictionary containing error analysis
    """
    results = results_data.get('results', [])
    
    errors = []
    error_types = Counter()
    
    for result in results:
        if result.get('status') == 'error':
            error_msg = result.get('error', 'Unknown error')
            errors.append({
                'defect': result.get('defect', {}),
                'error': error_msg
            })
            
            # Categorize error types
            if 'timeout' in error_msg.lower():
                error_types['timeout'] += 1
            elif 'memory' in error_msg.lower():
                error_types['memory'] += 1
            elif 'network' in error_msg.lower():
                error_types['network'] += 1
            elif 'file' in error_msg.lower() or 'path' in error_msg.lower():
                error_types['file_access'] += 1
            else:
                error_types['other'] += 1
    
    return {
        'total_errors': len(errors),
        'error_types': dict(error_types),
        'sample_errors': errors[:5]  # First 5 errors as samples
    }


def generate_report(
    basic_stats: Dict[str, Any],
    json_analysis: Dict[str, Any],
    error_analysis: Dict[str, Any],
    output_file: Optional[str] = None
) -> str:
    """Generate a comprehensive report.
    
    Args:
        basic_stats: Basic statistics
        json_analysis: JSON summary analysis
        error_analysis: Error analysis
        output_file: Optional file to save the report
        
    Returns:
        Report content as string
    """
    report_lines = [
        "=" * 60,
        "BATCH EVALUATION ANALYSIS REPORT",
        "=" * 60,
        "",
        "BASIC STATISTICS:",
        f"  Total Defects: {basic_stats['total_defects']}",
        f"  Completed: {basic_stats['completed_defects']} ({basic_stats['completion_rate']:.1f}%)",
        f"  Successful: {basic_stats['success_count']} ({basic_stats['success_rate']:.1f}%)",
        f"  Failed: {basic_stats['error_count']}",
        "",
        "DEFECT SEVERITY DISTRIBUTION:",
    ]
    
    for severity, count in basic_stats['severities'].items():
        report_lines.append(f"  {severity}: {count}")
    
    report_lines.extend([
        "",
        "TOP DEFECT TYPES:",
    ])
    
    for defect_type, count in basic_stats['defect_types'].items():
        report_lines.append(f"  {defect_type}: {count}")
    
    if basic_stats['categories']:
        report_lines.extend([
            "",
            "DEFECT CATEGORIES:",
        ])
        for category, count in basic_stats['categories'].items():
            report_lines.append(f"  {category}: {count}")
    
    report_lines.extend([
        "",
        "JSON SUMMARY ANALYSIS:",
        f"  Total Summaries Generated: {json_analysis['total_summaries']}",
        f"  Common Fields: {', '.join(json_analysis['common_fields'][:10])}",
        "",
        "ERROR ANALYSIS:",
        f"  Total Errors: {error_analysis['total_errors']}",
    ])
    
    if error_analysis['error_types']:
        report_lines.append("  Error Types:")
        for error_type, count in error_analysis['error_types'].items():
            report_lines.append(f"    {error_type}: {count}")
    
    if error_analysis['sample_errors']:
        report_lines.extend([
            "",
            "SAMPLE ERRORS:",
        ])
        for i, error_info in enumerate(error_analysis['sample_errors'], 1):
            defect = error_info['defect']
            report_lines.append(f"  {i}. {defect.get('file', 'Unknown')}:{defect.get('line', '?')} - {error_info['error'][:100]}...")
    
    report_lines.append("=" * 60)
    
    report_content = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report saved to: {output_file}")
    
    return report_content


def export_csv_summary(results_data: Dict[str, Any], output_file: str) -> None:
    """Export a CSV summary of the results.
    
    Args:
        results_data: Dictionary containing evaluation results
        output_file: Path to save the CSV file
    """
    results = results_data.get('results', [])
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'row_number', 'file', 'line', 'severity', 'defect_id', 'summary',
            'status', 'has_json_summary', 'error_message'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            defect = result.get('defect', {})
            row = {
                'row_number': defect.get('row_number', ''),
                'file': defect.get('file', ''),
                'line': defect.get('line', ''),
                'severity': defect.get('severity', ''),
                'defect_id': defect.get('id', ''),
                'summary': defect.get('summary', '')[:100] + '...' if len(defect.get('summary', '')) > 100 else defect.get('summary', ''),
                'status': result.get('status', ''),
                'has_json_summary': 'Yes' if result.get('json_summary') else 'No',
                'error_message': result.get('error', '')[:100] + '...' if len(result.get('error', '')) > 100 else result.get('error', '')
            }
            writer.writerow(row)
    
    print(f"CSV summary exported to: {output_file}")


def main():
    """Main function for the analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze batch evaluation results"
    )
    
    parser.add_argument(
        "results_file",
        help="JSON file containing evaluation results"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file for the analysis report"
    )
    
    parser.add_argument(
        "--csv",
        help="Export CSV summary to specified file"
    )
    
    parser.add_argument(
        "--json-details",
        action="store_true",
        help="Show detailed JSON summary analysis"
    )
    
    args = parser.parse_args()
    
    try:
        # Load results
        print(f"Loading results from: {args.results_file}")
        results_data = load_results(args.results_file)
        
        # Perform analyses
        print("Analyzing basic statistics...")
        basic_stats = analyze_basic_stats(results_data)
        
        print("Analyzing JSON summaries...")
        json_analysis = analyze_json_summaries(results_data)
        
        print("Analyzing errors...")
        error_analysis = analyze_errors(results_data)
        
        # Generate and display report
        print("\nGenerating report...")
        report = generate_report(basic_stats, json_analysis, error_analysis, args.output)
        print(report)
        
        # Show detailed JSON analysis if requested
        if args.json_details and json_analysis['field_analysis']:
            print("\nDETAILED JSON FIELD ANALYSIS:")
            for field, values in json_analysis['field_analysis'].items():
                print(f"  {field}:")
                for value, count in values.items():
                    print(f"    {value}: {count}")
        
        # Export CSV if requested
        if args.csv:
            print(f"\nExporting CSV summary...")
            export_csv_summary(results_data, args.csv)
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 