# CppCheck Batch Evaluation

This directory contains tools for batch evaluation of CppCheck defect reports using the DeerFlow analysis workflow.

## Files Overview

- `batch_evaluation.py` - Main batch processing script
- `run_evaluation.py` - Simplified runner for quick evaluations  
- `analyze_results.py` - Results analysis and reporting tool
- `test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv` - Sample CppCheck data
- `README.md` - This documentation

## Quick Start

### 1. Basic Evaluation (First 10 defects)

```bash
cd evaluation
python run_evaluation.py
```

This will process the first 10 defects from the CSV file and save results to `results/evaluation_results.json`.

### 2. Custom Range Evaluation

```bash
python run_evaluation.py --start 10 --count 20 --output results/batch_10_to_30.json
```

This processes defects 10-29 (20 total) and saves to a custom output file.

### 3. Analyze Results

```bash
python analyze_results.py results/evaluation_results.json
```

This generates a comprehensive analysis report of the evaluation results.

## Detailed Usage

### Batch Evaluation Script

The main `batch_evaluation.py` script provides full control over the evaluation process:

```bash
python batch_evaluation.py [CSV_FILE] [OPTIONS]
```

**Required Arguments:**
- `CSV_FILE` - Path to the CppCheck CSV file

**Options:**
- `-o, --output` - Output JSON file (default: evaluation_results.json)
- `--start-index` - Start processing from this index (0-based, default: 0)
- `--end-index` - Stop processing at this index (exclusive)
- `--max-concurrent` - Maximum concurrent analyses (default: 1)
- `--max_plan_iterations` - Maximum plan iterations (default: 1)
- `--max_step_num` - Maximum steps per plan (default: 3)
- `--debug` - Enable debug logging
- `--no-background-investigation` - Disable web search

**Examples:**

```bash
# Process first 50 defects
python batch_evaluation.py test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv \
    --start-index 0 --end-index 50 -o results/first_50.json

# Process with debug logging
python batch_evaluation.py test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv \
    --debug --start-index 0 --end-index 5 -o results/debug_test.json

# Process specific range with custom parameters
python batch_evaluation.py test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv \
    --start-index 100 --end-index 150 \
    --max_plan_iterations 2 --max_step_num 5 \
    -o results/detailed_analysis.json
```

### Results Analysis

The `analyze_results.py` script provides comprehensive analysis of evaluation results:

```bash
python analyze_results.py [RESULTS_FILE] [OPTIONS]
```

**Required Arguments:**
- `RESULTS_FILE` - JSON file containing evaluation results

**Options:**
- `-o, --output` - Save report to file
- `--csv` - Export CSV summary
- `--json-details` - Show detailed JSON field analysis

**Examples:**

```bash
# Basic analysis
python analyze_results.py results/evaluation_results.json

# Generate detailed report and CSV export
python analyze_results.py results/evaluation_results.json \
    -o reports/analysis_report.txt \
    --csv reports/summary.csv \
    --json-details
```

## CSV File Format

The input CSV file should contain the following columns:

| Column | Description | Required |
|--------|-------------|----------|
| File | Path to the source file | Yes |
| Line | Line number of the defect | Yes |
| Severity | Defect severity (error, warning, style, etc.) | Yes |
| Id | CppCheck defect ID | Yes |
| Summary | Description of the defect | Yes |
| Category | Defect category | No |
| Ours | Custom annotation field | No |
| Baseline | Baseline comparison field | No |

## Output Format

The evaluation produces JSON files with the following structure:

```json
{
  "metadata": {
    "timestamp": "2025-01-XX...",
    "total_defects": 534,
    "completed_defects": 10,
    "success_count": 8,
    "error_count": 2
  },
  "results": [
    {
      "defect": {
        "file": "path/to/file.c",
        "line": 123,
        "severity": "error",
        "id": "nullPointer",
        "summary": "Possible null pointer dereference",
        "row_number": 2
      },
      "status": "success",
      "analysis_content": "Full analysis text...",
      "json_summary": {
        "defect_type": "Null Pointer Dereference",
        "severity_assessment": "High",
        "fix_recommendation": "...",
        "confidence": 85
      },
      "raw_result": {...}
    }
  ]
}
```

## Performance Considerations

1. **Sequential Processing**: By default, defects are processed one at a time (`--max-concurrent 1`) to avoid overwhelming the system.

2. **Batch Size**: For large datasets, process in smaller batches (e.g., 50-100 defects) to enable incremental progress tracking.

3. **Resource Usage**: Each analysis may take 30 seconds to several minutes depending on complexity and file size.

4. **Disk Space**: Results files can become large with detailed analysis content. Monitor available disk space.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the evaluation directory and the project structure is intact.

2. **CSV Parsing Errors**: Check that the CSV file has the required columns and proper formatting.

3. **Memory Issues**: Reduce batch size or process smaller ranges if encountering memory problems.

4. **Network Timeouts**: If using background investigation, ensure stable internet connection.

### Debug Mode

Enable debug mode for detailed logging:

```bash
python batch_evaluation.py test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv \
    --debug --start-index 0 --end-index 1
```

This provides verbose output for troubleshooting individual defect processing.

## Example Workflow

Here's a complete workflow for evaluating the provided dataset:

```bash
# 1. Navigate to evaluation directory
cd evaluation

# 2. Test with a small batch first
python run_evaluation.py --start 0 --count 5 --output results/test_batch.json --debug

# 3. Analyze the test results
python analyze_results.py results/test_batch.json

# 4. If successful, process larger batches
python run_evaluation.py --start 0 --count 50 --output results/batch_1.json
python run_evaluation.py --start 50 --count 50 --output results/batch_2.json

# 5. Analyze each batch
python analyze_results.py results/batch_1.json -o reports/batch_1_analysis.txt
python analyze_results.py results/batch_2.json -o reports/batch_2_analysis.txt
```

## Directory Structure

After running evaluations, your directory structure will look like:

```
evaluation/
├── batch_evaluation.py
├── run_evaluation.py  
├── analyze_results.py
├── README.md
├── test/
│   └── libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv
├── results/
│   ├── evaluation_results.json
│   ├── batch_1.json
│   └── batch_2.json
├── reports/
│   ├── analysis_report.txt
│   └── summary.csv
└── evaluation_*.log
```

## Additional Notes

- **Logging**: All runs generate timestamped log files (`evaluation_YYYYMMDD_HHMMSS.log`)
- **Progress Tracking**: Intermediate results are saved every 10 completed analyses
- **Error Handling**: Failed analyses are logged and don't stop the batch process
- **Resumption**: Use `--start-index` to resume from a specific point if needed

For questions or issues, refer to the project documentation or create an issue in the repository. 