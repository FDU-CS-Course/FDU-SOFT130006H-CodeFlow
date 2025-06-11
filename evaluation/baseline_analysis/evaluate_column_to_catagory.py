#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Target Column to Category Evaluation Script

This script evaluates the accuracy, F1 score, and recall between the target column 
and 'category' columns in the CppCheck CSV file. It compares the target column 
annotations with the category classifications directly.

This version uses scikit-learn for metrics calculation.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter, defaultdict

# Import scikit-learn for metrics calculation
try:
    from sklearn.metrics import classification_report, precision_recall_fscore_support, accuracy_score
    from sklearn.metrics import confusion_matrix as sklearn_confusion_matrix
except ImportError:
    print("Error: scikit-learn is required. Please install it with: pip install scikit-learn")
    sys.exit(1)

test_target_column = "Baseline"

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
            required_columns = {'Category', test_target_column}
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


def clean_category_value(category: str) -> str:
    """Clean and normalize category values.
    
    Args:
        category: Original category value
        
    Returns:
        Cleaned category value
    """
    if category is None:
        category = ''
    elif not isinstance(category, str):
        category = str(category)
    
    category = category.lower().strip()
    
    # Handle empty or nan values
    if category in ['', 'nan', 'none']:
        return 'unknown'
    
    return category


def clean_target_category(target: str) -> str:
    """Clean and normalize target category values.
    
    Args:
        target: Original target value
        
    Returns:
        Cleaned target category
    """
    if target is None:
        target = ''
    elif not isinstance(target, str):
        target = str(target)
    
    target = target.lower().strip()
    
    # Handle empty or nan values
    if target in ['', 'nan', 'none']:
        return 'unknown'
    
    return target


def calculate_cppcheck_similarity_rate(y_true: List[str], y_pred: List[str]) -> float:
    """Calculate the original CppCheck similarity rate (manual F1-like calculation).
    
    This preserves the original calculation method as a custom similarity metric.
    
    Args:
        y_true: True labels (category)
        y_pred: Predicted labels (target column)
        
    Returns:
        CppCheck similarity rate
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    # Overall accuracy
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    accuracy = correct / len(y_true) if len(y_true) > 0 else 0.0
    
    # Get unique labels
    labels = sorted(set(y_true + y_pred))
    
    # Calculate per-class metrics using original method
    total_f1 = 0.0
    valid_classes = 0
    
    for label in labels:
        # True positives, false positives, false negatives
        tp = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred == label)
        fp = sum(1 for true, pred in zip(y_true, y_pred) if true != label and pred == label)
        fn = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred != label)
        
        # Precision, Recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        if (tp + fp) > 0 or (tp + fn) > 0:  # Only count classes that actually appear
            total_f1 += f1
            valid_classes += 1
    
    return total_f1 / valid_classes if valid_classes > 0 else 0.0


def calculate_sklearn_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, any]:
    """Calculate classification metrics using scikit-learn.
    
    Args:
        y_true: True labels (category)
        y_pred: Predicted labels (target column)
        
    Returns:
        Dictionary containing various metrics from sklearn
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    # Get unique labels
    labels = sorted(set(y_true + y_pred))
    
    # Calculate metrics using sklearn
    accuracy = accuracy_score(y_true, y_pred)
    
    # Calculate precision, recall, f1 with different averaging methods
    precision_macro, recall_macro, f1_macro, support = precision_recall_fscore_support(
        y_true, y_pred, average='macro', zero_division=0
    )
    
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted', zero_division=0
    )
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=labels, zero_division=0
    )
    
    # Create per-class metrics dictionary
    per_class_metrics = {}
    for i, label in enumerate(labels):
        per_class_metrics[label] = {
            'precision': precision_per_class[i],
            'recall': recall_per_class[i],
            'f1': f1_per_class[i],
            'support': support_per_class[i]
        }
    
    # Get classification report as string for detailed output
    classification_rep = classification_report(y_true, y_pred, labels=labels, zero_division=0)
    
    return {
        'accuracy': accuracy,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'precision_weighted': precision_weighted,
        'recall_weighted': recall_weighted,
        'f1_weighted': f1_weighted,
        'per_class_metrics': per_class_metrics,
        'labels': labels,
        'classification_report': classification_rep
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
    
    # Use sklearn confusion matrix
    cm = sklearn_confusion_matrix(y_true, y_pred, labels=labels)
    
    # Convert to dictionary format
    matrix = {}
    for i, true_label in enumerate(labels):
        matrix[true_label] = {}
        for j, pred_label in enumerate(labels):
            matrix[true_label][pred_label] = int(cm[i][j])
    
    return matrix


def calculate_agreement_rate(data: List[Dict[str, str]]) -> Dict[str, any]:
    """Calculate the agreement rate between category and target column.
    
    Args:
        data: List of data records
        
    Returns:
        Dictionary containing agreement statistics
    """
    total_records = len(data)
    matches = 0
    
    # Calculate agreement by original category type
    category_stats = defaultdict(lambda: {'matches': 0, 'total': 0})
    
    for record in data:
        cleaned_category = record['cleaned_category']
        cleaned_target = record['cleaned_target']
        original_category = record['Category']
        
        if cleaned_category == cleaned_target:
            matches += 1
            category_stats[original_category]['matches'] += 1
        
        category_stats[original_category]['total'] += 1
    
    # Calculate rates
    category_agreement = {}
    for category, stats in category_stats.items():
        category_agreement[category] = {
            'matches': stats['matches'],
            'total': stats['total'],
            'rate': stats['matches'] / stats['total'] if stats['total'] > 0 else 0.0
        }
    
    return {
        'overall_agreement_rate': matches / total_records if total_records > 0 else 0.0,
        'total_matches': matches,
        'total_records': total_records,
        'by_category': category_agreement
    }


def analyze_distributions(data: List[Dict[str, str]]) -> Dict[str, Counter]:
    """Analyze category and target column distributions.
    
    Args:
        data: List of data records
        
    Returns:
        Dictionary containing distribution counters
    """
    category_original = Counter(record['Category'] for record in data)
    category_cleaned = Counter(record['cleaned_category'] for record in data)
    target_cleaned = Counter(record['cleaned_target'] for record in data)
    
    return {
        'category_original': category_original,
        'category_cleaned': category_cleaned,
        'target_cleaned': target_cleaned
    }


def print_detailed_analysis(data: List[Dict[str, str]], sklearn_metrics: Dict[str, any], 
                          cppcheck_similarity: float, distributions: Dict[str, Counter], 
                          confusion_matrix: Dict[str, Dict[str, int]],
                          agreement: Dict[str, any]) -> None:
    """Print detailed analysis results.
    
    Args:
        data: List of data records
        sklearn_metrics: Calculated sklearn metrics
        cppcheck_similarity: CppCheck similarity rate
        distributions: Category distributions
        confusion_matrix: Confusion matrix
        agreement: Agreement rate analysis
    """
    print("=" * 80)
    print(f"{test_target_column} vs CATEGORY EVALUATION ANALYSIS")
    print("=" * 80)
    
    total_records = len(data)
    
    print(f"\nDATASET OVERVIEW:")
    print(f"  Total Records: {total_records}")
    print(f"  Overall Agreement Rate: {agreement['overall_agreement_rate']:.4f} ({agreement['total_matches']}/{agreement['total_records']})")
    
    print(f"\nCATEGORY DISTRIBUTION (Original):")
    for category, count in distributions['category_original'].most_common():
        percentage = count / total_records * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    print(f"\nCLEANED CATEGORY DISTRIBUTION:")
    for category, count in sorted(distributions['category_cleaned'].items()):
        percentage = count / total_records * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    print(f"\n{test_target_column} DISTRIBUTION:")
    for target, count in sorted(distributions['target_cleaned'].items()):
        percentage = count / total_records * 100
        print(f"  {target}: {count} ({percentage:.1f}%)")
    
    print(f"\nCLASSIFICATION METRICS (using scikit-learn):")
    print(f"  Accuracy: {sklearn_metrics['accuracy']:.4f}")
    print(f"  Precision (Macro): {sklearn_metrics['precision_macro']:.4f}")
    print(f"  Recall (Macro): {sklearn_metrics['recall_macro']:.4f}")
    print(f"  F1 Score (Macro): {sklearn_metrics['f1_macro']:.4f}")
    print(f"  Precision (Weighted): {sklearn_metrics['precision_weighted']:.4f}")
    print(f"  Recall (Weighted): {sklearn_metrics['recall_weighted']:.4f}")
    print(f"  F1 Score (Weighted): {sklearn_metrics['f1_weighted']:.4f}")
    
    print(f"\nCPPCHECK SIMILARITY RATE:")
    print(f"  CppCheck Similarity Rate: {cppcheck_similarity:.4f}")
    
    print(f"\nAGREEMENT BY ORIGINAL CATEGORY:")
    for category, stats in agreement['by_category'].items():
        print(f"  {category}: {stats['matches']}/{stats['total']} ({stats['rate']:.4f})")
    
    print(f"\nCONFUSION MATRIX:")
    labels = sklearn_metrics['labels']
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
    
    print(f"\nPER-CLASS DETAILED METRICS (from scikit-learn):")
    for label in labels:
        if label in sklearn_metrics['per_class_metrics']:
            class_metrics = sklearn_metrics['per_class_metrics'][label]
            print(f"  {label}:")
            print(f"    Precision: {class_metrics['precision']:.4f}")
            print(f"    Recall: {class_metrics['recall']:.4f}")
            print(f"    F1-Score: {class_metrics['f1']:.4f}")
            print(f"    Support: {class_metrics['support']}")
    
    print(f"\nDETAILED CLASSIFICATION REPORT:")
    print(sklearn_metrics['classification_report'])


def save_results_to_file(output_file: str, data: List[Dict[str, str]], 
                        sklearn_metrics: Dict[str, any], cppcheck_similarity: float,
                        distributions: Dict[str, Counter],
                        confusion_matrix: Dict[str, Dict[str, int]], 
                        agreement: Dict[str, any]) -> None:
    """Save analysis results to a file.
    
    Args:
        output_file: Path to save the results
        data: List of data records
        sklearn_metrics: Calculated sklearn metrics
        cppcheck_similarity: CppCheck similarity rate
        distributions: Category distributions
        confusion_matrix: Confusion matrix
        agreement: Agreement rate analysis
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{test_target_column} vs CATEGORY EVALUATION ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"DATASET OVERVIEW:\n")
        f.write(f"  Total Records: {len(data)}\n")
        f.write(f"  Overall Agreement Rate: {agreement['overall_agreement_rate']:.4f} ({agreement['total_matches']}/{agreement['total_records']})\n\n")
        
        f.write(f"CLASSIFICATION METRICS (scikit-learn):\n")
        f.write(f"  Accuracy: {sklearn_metrics['accuracy']:.4f}\n")
        f.write(f"  Precision (Macro): {sklearn_metrics['precision_macro']:.4f}\n")
        f.write(f"  Recall (Macro): {sklearn_metrics['recall_macro']:.4f}\n")
        f.write(f"  F1 Score (Macro): {sklearn_metrics['f1_macro']:.4f}\n")
        f.write(f"  Precision (Weighted): {sklearn_metrics['precision_weighted']:.4f}\n")
        f.write(f"  Recall (Weighted): {sklearn_metrics['recall_weighted']:.4f}\n")
        f.write(f"  F1 Score (Weighted): {sklearn_metrics['f1_weighted']:.4f}\n\n")
        
        f.write(f"CPPCHECK SIMILARITY:\n")
        f.write(f"  CppCheck Similarity Rate: {cppcheck_similarity:.4f}\n\n")
        
        f.write(f"DISTRIBUTIONS:\n")
        f.write(f"  Original Category: {dict(distributions['category_original'])}\n")
        f.write(f"  Cleaned Category: {dict(distributions['category_cleaned'])}\n")
        f.write(f"  {test_target_column}: {dict(distributions['target_cleaned'])}\n\n")
        
        f.write(f"AGREEMENT BY CATEGORY:\n")
        for category, stats in agreement['by_category'].items():
            f.write(f"  {category}: {stats['matches']}/{stats['total']} ({stats['rate']:.4f})\n")
        f.write("\n")
        
        f.write(f"CONFUSION MATRIX:\n")
        for true_label in sklearn_metrics['labels']:
            f.write(f"{true_label}: {confusion_matrix.get(true_label, {})}\n")
        
        f.write(f"\nDETAILED CLASSIFICATION REPORT:\n")
        f.write(sklearn_metrics['classification_report'])


def main():
    """Main function for the target column accuracy evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate target column vs category agreement in CppCheck CSV data"
    )
    
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="codeflow_data_edited.csv",
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
        
        # Apply cleaning to category and target column values
        print("Applying category and target column cleaning...")
        for record in data:
            record['cleaned_category'] = clean_category_value(record['Category'])
            record['cleaned_target'] = clean_target_category(record[test_target_column])
        
        # Show distributions
        category_dist = Counter(record['cleaned_category'] for record in data)
        target_dist = Counter(record['cleaned_target'] for record in data)
        
        print(f"\nCategory value distribution:")
        for category, count in category_dist.most_common():
            print(f"  '{category}': {count}")
        
        print(f"\n{test_target_column} value distribution:")
        for target, count in target_dist.most_common():
            print(f"  '{target}': {count}")
        
        if len(data) == 0:
            print("No valid records found. Exiting.")
            sys.exit(1)
        
        # Prepare data for metrics calculation
        y_true = [record['cleaned_category'] for record in data]  # Category as ground truth
        y_pred = [record['cleaned_target'] for record in data]  # Target column as prediction
        
        # Calculate metrics
        print("Calculating metrics...")
        sklearn_metrics = calculate_sklearn_metrics(y_true, y_pred)
        cppcheck_similarity = calculate_cppcheck_similarity_rate(y_true, y_pred)
        distributions = analyze_distributions(data)
        confusion_matrix = create_confusion_matrix(y_true, y_pred)
        agreement = calculate_agreement_rate(data)
        
        # Print results
        print_detailed_analysis(data, sklearn_metrics, cppcheck_similarity, distributions, confusion_matrix, agreement)
        
        # Save results to file if requested
        if args.output:
            save_results_to_file(args.output, data, sklearn_metrics, cppcheck_similarity, distributions, confusion_matrix, agreement)
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