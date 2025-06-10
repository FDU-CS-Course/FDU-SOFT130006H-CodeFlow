#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Simple Baseline Accuracy Evaluation Script

This script evaluates the accuracy, F1 score, and recall between the 'baseline' 
and 'severity' columns in the CppCheck CSV file. It maps 'warning' and 'error' 
from severity to 'bug' for comparison with baseline.

The script automatically filters out records where the baseline is marked as 
'false_positive' before performing the analysis.

This version uses only standard Python libraries.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter, defaultdict


def load_csv_data(csv_path: str) -> List[Dict[str, str]]:
    """Load CSV data into a list of dictionaries.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of dictionaries containing the CSV data
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate required columns exist
            required_columns = {'Severity', 'Baseline'}
            if not required_columns.issubset(set(reader.fieldnames)):
                raise ValueError(f"CSV must contain columns: {required_columns}")
            
            for row in reader:
                # Strip whitespace from values, handle non-string types
                cleaned_row = {}
                for k, v in row.items():
                    if v is None:
                        cleaned_row[k] = ''
                    elif isinstance(v, str):
                        cleaned_row[k] = v.strip()
                    else:
                        cleaned_row[k] = str(v).strip()
                data.append(cleaned_row)
        
        print(f"Successfully loaded {len(data)} records from {csv_path}")
        return data
        
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")


def map_severity_to_baseline_categories(severity: str) -> str:
    """Map severity values to baseline categories.
    
    According to the specification:
    - 'warning' and 'error' in severity map to 'bug' in baseline
    - Other values remain as-is
    
    Args:
        severity: Original severity value
        
    Returns:
        Mapped baseline category
    """
    if severity is None:
        severity = ''
    elif not isinstance(severity, str):
        severity = str(severity)
    
    severity = severity.lower().strip()
    
    if severity in ['warning', 'error']:
        return 'bug'
    elif severity == 'style':
        return 'style'
    elif severity == 'information':
        return 'information'
    else:
        # Handle any other cases
        return severity


def clean_baseline_category(baseline: str) -> str:
    """Clean and normalize baseline category values.
    
    Args:
        baseline: Original baseline value
        
    Returns:
        Cleaned baseline category
    """
    if baseline is None:
        baseline = ''
    elif not isinstance(baseline, str):
        baseline = str(baseline)
    
    baseline = baseline.lower().strip()
    
    # Handle empty or nan values
    if baseline in ['', 'nan', 'none']:
        return 'unknown'
    
    return baseline


def calculate_metrics_manual(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """Calculate classification metrics manually.
    
    Args:
        y_true: True labels (mapped severity)
        y_pred: Predicted labels (baseline)
        
    Returns:
        Dictionary containing various metrics
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    # Overall accuracy
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    accuracy = correct / len(y_true) if len(y_true) > 0 else 0.0
    
    # Get unique labels
    labels = sorted(set(y_true + y_pred))
    
    # Calculate per-class metrics
    metrics_per_class = {}
    for label in labels:
        # True positives, false positives, false negatives
        tp = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred == label)
        fp = sum(1 for true, pred in zip(y_true, y_pred) if true != label and pred == label)
        fn = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred != label)
        
        # Precision, Recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics_per_class[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': sum(1 for true in y_true if true == label)
        }
    
    # Macro averages
    precision_macro = sum(m['precision'] for m in metrics_per_class.values()) / len(labels) if labels else 0.0
    recall_macro = sum(m['recall'] for m in metrics_per_class.values()) / len(labels) if labels else 0.0
    f1_macro = sum(m['f1'] for m in metrics_per_class.values()) / len(labels) if labels else 0.0
    
    # Weighted averages
    total_support = sum(m['support'] for m in metrics_per_class.values())
    if total_support > 0:
        precision_weighted = sum(m['precision'] * m['support'] for m in metrics_per_class.values()) / total_support
        recall_weighted = sum(m['recall'] * m['support'] for m in metrics_per_class.values()) / total_support
        f1_weighted = sum(m['f1'] * m['support'] for m in metrics_per_class.values()) / total_support
    else:
        precision_weighted = recall_weighted = f1_weighted = 0.0
    
    return {
        'accuracy': accuracy,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'precision_weighted': precision_weighted,
        'recall_weighted': recall_weighted,
        'f1_weighted': f1_weighted,
        'per_class_metrics': metrics_per_class,
        'labels': labels
    }


def create_confusion_matrix(y_true: List[str], y_pred: List[str]) -> Dict[str, Dict[str, int]]:
    """Create confusion matrix.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        Dictionary representing confusion matrix
    """
    labels = sorted(set(y_true + y_pred))
    matrix = {}
    
    for true_label in labels:
        matrix[true_label] = {}
        for pred_label in labels:
            matrix[true_label][pred_label] = 0
    
    for true, pred in zip(y_true, y_pred):
        matrix[true][pred] += 1
    
    return matrix


def calculate_agreement_rate(data: List[Dict[str, str]]) -> Dict[str, any]:
    """Calculate the agreement rate between mapped severity and baseline.
    
    Args:
        data: List of data records
        
    Returns:
        Dictionary containing agreement statistics
    """
    total_records = len(data)
    matches = 0
    
    # Calculate agreement by original severity type
    severity_stats = defaultdict(lambda: {'matches': 0, 'total': 0})
    
    for record in data:
        mapped_severity = record['mapped_severity']
        cleaned_baseline = record['cleaned_baseline']
        original_severity = record['Severity']
        
        if mapped_severity == cleaned_baseline:
            matches += 1
            severity_stats[original_severity]['matches'] += 1
        
        severity_stats[original_severity]['total'] += 1
    
    # Calculate rates
    severity_agreement = {}
    for severity, stats in severity_stats.items():
        severity_agreement[severity] = {
            'matches': stats['matches'],
            'total': stats['total'],
            'rate': stats['matches'] / stats['total'] if stats['total'] > 0 else 0.0
        }
    
    return {
        'overall_agreement_rate': matches / total_records if total_records > 0 else 0.0,
        'total_matches': matches,
        'total_records': total_records,
        'by_severity': severity_agreement
    }


def analyze_distributions(data: List[Dict[str, str]]) -> Dict[str, Counter]:
    """Analyze category distributions.
    
    Args:
        data: List of data records
        
    Returns:
        Dictionary containing distribution counters
    """
    severity_original = Counter(record['Severity'] for record in data)
    severity_mapped = Counter(record['mapped_severity'] for record in data)
    baseline_cleaned = Counter(record['cleaned_baseline'] for record in data)
    
    return {
        'severity_original': severity_original,
        'severity_mapped': severity_mapped,
        'baseline_cleaned': baseline_cleaned
    }


def print_detailed_analysis(data: List[Dict[str, str]], metrics: Dict[str, any], 
                          distributions: Dict[str, Counter], 
                          confusion_matrix: Dict[str, Dict[str, int]],
                          agreement: Dict[str, any]) -> None:
    """Print detailed analysis results.
    
    Args:
        data: List of data records
        metrics: Calculated metrics
        distributions: Category distributions
        confusion_matrix: Confusion matrix
        agreement: Agreement rate analysis
    """
    print("=" * 80)
    print("BASELINE vs SEVERITY EVALUATION ANALYSIS")
    print("=" * 80)
    
    total_records = len(data)
    
    print(f"\nDATASET OVERVIEW:")
    print(f"  Total Records: {total_records}")
    print(f"  Overall Agreement Rate: {agreement['overall_agreement_rate']:.4f} ({agreement['total_matches']}/{agreement['total_records']})")
    
    print(f"\nSEVERITY DISTRIBUTION (Original):")
    for severity, count in distributions['severity_original'].most_common():
        percentage = count / total_records * 100
        print(f"  {severity}: {count} ({percentage:.1f}%)")
    
    print(f"\nMAPPED SEVERITY DISTRIBUTION:")
    for severity, count in sorted(distributions['severity_mapped'].items()):
        percentage = count / total_records * 100
        print(f"  {severity}: {count} ({percentage:.1f}%)")
    
    print(f"\nBASELINE DISTRIBUTION:")
    for baseline, count in sorted(distributions['baseline_cleaned'].items()):
        percentage = count / total_records * 100
        print(f"  {baseline}: {count} ({percentage:.1f}%)")
    
    print(f"\nCLASSIFICATION METRICS:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Precision (Macro): {metrics['precision_macro']:.4f}")
    print(f"  Recall (Macro): {metrics['recall_macro']:.4f}")
    print(f"  F1 Score (Macro): {metrics['f1_macro']:.4f}")
    print(f"  Precision (Weighted): {metrics['precision_weighted']:.4f}")
    print(f"  Recall (Weighted): {metrics['recall_weighted']:.4f}")
    print(f"  F1 Score (Weighted): {metrics['f1_weighted']:.4f}")
    
    print(f"\nAGREEMENT BY ORIGINAL SEVERITY:")
    for severity, stats in agreement['by_severity'].items():
        print(f"  {severity}: {stats['matches']}/{stats['total']} ({stats['rate']:.4f})")
    
    print(f"\nCONFUSION MATRIX:")
    labels = metrics['labels']
    print(f"  {'':>15}", end="")
    for label in labels:
        print(f"{label:>15}", end="")
    print()
    
    for true_label in labels:
        print(f"  {true_label:>15}", end="")
        for pred_label in labels:
            count = confusion_matrix.get(true_label, {}).get(pred_label, 0)
            print(f"{count:>15}", end="")
        print()
    
    print(f"\nPER-CLASS DETAILED METRICS:")
    for label in labels:
        if label in metrics['per_class_metrics']:
            class_metrics = metrics['per_class_metrics'][label]
            print(f"  {label}:")
            print(f"    Precision: {class_metrics['precision']:.4f}")
            print(f"    Recall: {class_metrics['recall']:.4f}")
            print(f"    F1-Score: {class_metrics['f1']:.4f}")
            print(f"    Support: {class_metrics['support']}")


def save_results_to_file(output_file: str, data: List[Dict[str, str]], 
                        metrics: Dict[str, any], distributions: Dict[str, Counter],
                        confusion_matrix: Dict[str, Dict[str, int]], 
                        agreement: Dict[str, any]) -> None:
    """Save analysis results to a file.
    
    Args:
        output_file: Path to save the results
        data: List of data records
        metrics: Calculated metrics
        distributions: Category distributions
        confusion_matrix: Confusion matrix
        agreement: Agreement rate analysis
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BASELINE vs SEVERITY EVALUATION ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"DATASET OVERVIEW:\n")
        f.write(f"  Total Records: {len(data)}\n")
        f.write(f"  Overall Agreement Rate: {agreement['overall_agreement_rate']:.4f} ({agreement['total_matches']}/{agreement['total_records']})\n\n")
        
        f.write(f"CLASSIFICATION METRICS:\n")
        f.write(f"  Accuracy: {metrics['accuracy']:.4f}\n")
        f.write(f"  Precision (Macro): {metrics['precision_macro']:.4f}\n")
        f.write(f"  Recall (Macro): {metrics['recall_macro']:.4f}\n")
        f.write(f"  F1 Score (Macro): {metrics['f1_macro']:.4f}\n")
        f.write(f"  Precision (Weighted): {metrics['precision_weighted']:.4f}\n")
        f.write(f"  Recall (Weighted): {metrics['recall_weighted']:.4f}\n")
        f.write(f"  F1 Score (Weighted): {metrics['f1_weighted']:.4f}\n\n")
        
        f.write(f"CATEGORY DISTRIBUTIONS:\n")
        f.write(f"  Original Severity: {dict(distributions['severity_original'])}\n")
        f.write(f"  Mapped Severity: {dict(distributions['severity_mapped'])}\n")
        f.write(f"  Baseline: {dict(distributions['baseline_cleaned'])}\n\n")
        
        f.write(f"AGREEMENT BY SEVERITY:\n")
        for severity, stats in agreement['by_severity'].items():
            f.write(f"  {severity}: {stats['matches']}/{stats['total']} ({stats['rate']:.4f})\n")
        f.write("\n")
        
        f.write(f"CONFUSION MATRIX:\n")
        for true_label in metrics['labels']:
            f.write(f"{true_label}: {confusion_matrix.get(true_label, {})}\n")


def main():
    """Main function for the baseline accuracy evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate baseline vs severity agreement in CppCheck CSV data"
    )
    
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="marked_data.csv",
        help="Path to the CSV file containing CppCheck data (default: libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file to save detailed results"
    )
    
    parser.add_argument(
        "--csv-output",
        help="Save processed data with mapped categories to CSV file"
    )
    
    args = parser.parse_args()
    
    try:
        # Load the data
        print(f"Loading data from: {args.csv_file}")
        data = load_csv_data(args.csv_file)
        
        # Apply mappings
        print("Applying category mappings...")
        for record in data:
            record['mapped_severity'] = map_severity_to_baseline_categories(record['Severity'])
            record['cleaned_baseline'] = clean_baseline_category(record['Baseline'])
        
        # Show baseline value distribution before filtering
        baseline_dist_before = Counter(record['cleaned_baseline'] for record in data)
        print(f"Baseline value distribution before filtering:")
        for baseline, count in baseline_dist_before.most_common():
            print(f"  '{baseline}': {count}")
        
        # Ask user if they want to filter out unknown baseline values
        print(f"\nFound {baseline_dist_before.get('unknown', 0)} records with unknown baseline values.")
        
        # Filter out false_positive records from baseline before analysis
        original_len = len(data)
        data_filtered = []
        false_positive_count = 0
        
        for record in data:
            original_baseline = record.get('Baseline', '').lower().strip()
            if original_baseline == 'false_positive':
                false_positive_count += 1
            else:
                data_filtered.append(record)
        
        data = data_filtered
        
        print(f"\nFiltered out {false_positive_count} records marked as 'false_positive' in baseline.")
        print(f"Remaining records for analysis: {len(data)} (was {original_len})")
        
        if len(data) == 0:
            print("No valid records found after filtering. Exiting.")
            sys.exit(1)
        
        # Update distributions after filtering
        baseline_dist_after = Counter(record['cleaned_baseline'] for record in data)
        print(f"\nBaseline value distribution after filtering:")
        for baseline, count in baseline_dist_after.most_common():
            print(f"  '{baseline}': {count}")
        
        # For now, let's include unknown values in the analysis instead of filtering them out
        # We can treat 'unknown' as a separate category for comparison
        print("\nIncluding all remaining records in analysis (treating 'unknown' as a separate category)...")
        
        # Prepare data for metrics calculation
        y_true = [record['mapped_severity'] for record in data]
        y_pred = [record['cleaned_baseline'] for record in data]
        
        # Calculate metrics
        print("Calculating metrics...")
        metrics = calculate_metrics_manual(y_true, y_pred)
        distributions = analyze_distributions(data)
        confusion_matrix = create_confusion_matrix(y_true, y_pred)
        agreement = calculate_agreement_rate(data)
        
        # Print results
        print_detailed_analysis(data, metrics, distributions, confusion_matrix, agreement)
        
        # Save results to file if requested
        if args.output:
            save_results_to_file(args.output, data, metrics, distributions, confusion_matrix, agreement)
            print(f"\nDetailed results saved to: {args.output}")
        
        # Save processed CSV if requested
        if args.csv_output:
            with open(args.csv_output, 'w', newline='', encoding='utf-8') as f:
                if data:
                    fieldnames = list(data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            print(f"Processed data saved to: {args.csv_output}")
        
        print("\nEvaluation completed successfully!")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()