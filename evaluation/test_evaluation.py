#!/usr/bin/env python3
# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Test script for the batch evaluation tools.

This script performs basic functionality tests to ensure the evaluation
tools are working correctly.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_csv_parsing():
    """Test CSV parsing functionality."""
    print("Testing CSV parsing...")
    
    # Import the batch_evaluation module
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from batch_evaluation import parse_cppcheck_csv
        
        # Test with the actual CSV file
        csv_path = "test/libav_0.12.3_cppcheck2.17.1_filtered_anno_64.csv"
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return False
        
        defects = parse_cppcheck_csv(csv_path)
        
        if not defects:
            print("❌ No defects parsed from CSV")
            return False
        
        print(f"✅ Successfully parsed {len(defects)} defects")
        
        # Validate first defect structure
        first_defect = defects[0]
        required_fields = {'file', 'line', 'severity', 'id', 'summary', 'row_number'}
        if not required_fields.issubset(first_defect.keys()):
            print(f"❌ Missing required fields in defect: {required_fields - set(first_defect.keys())}")
            return False
        
        print("✅ Defect structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ CSV parsing test failed: {e}")
        return False


def test_single_defect_processing():
    """Test processing a single defect."""
    print("Testing single defect processing...")
    
    try:
        # Create a temporary CSV file with one defect
        csv_content = """File,Line,Severity,Id,Category,Ours,Baseline,Summary
C:\\test\\file.c,100,error,nullPointer,bug,,,Possible null pointer dereference of variable 'ptr'."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_csv = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output = f.name
        
        try:
            # Run batch evaluation on the single defect
            cmd = [
                sys.executable,
                "batch_evaluation.py",
                temp_csv,
                "-o", temp_output,
                "--start-index", "0",
                "--end-index", "1",
                "--no-background-investigation"
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"❌ Batch evaluation failed with return code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
            
            # Check if output file was created
            if not os.path.exists(temp_output):
                print("❌ Output file not created")
                return False
            
            # Check output file content
            import json
            with open(temp_output, 'r') as f:
                output_data = json.load(f)
            
            if 'metadata' not in output_data or 'results' not in output_data:
                print("❌ Invalid output format")
                return False
            
            if len(output_data['results']) != 1:
                print(f"❌ Expected 1 result, got {len(output_data['results'])}")
                return False
            
            print("✅ Single defect processing test passed")
            return True
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_csv)
                os.unlink(temp_output)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Single defect processing test failed: {e}")
        return False


def test_analysis_tools():
    """Test the analysis tools."""
    print("Testing analysis tools...")
    
    try:
        # Create a sample results file
        sample_results = {
            "metadata": {
                "timestamp": "2025-01-01T00:00:00",
                "total_defects": 2,
                "completed_defects": 2,
                "success_count": 1,
                "error_count": 1
            },
            "results": [
                {
                    "defect": {
                        "file": "test.c",
                        "line": 100,
                        "severity": "error",
                        "id": "nullPointer",
                        "summary": "Null pointer dereference",
                        "row_number": 2
                    },
                    "status": "success",
                    "analysis_content": "Analysis content here",
                    "json_summary": {
                        "defect_type": "Null Pointer",
                        "confidence": 90
                    }
                },
                {
                    "defect": {
                        "file": "test2.c", 
                        "line": 200,
                        "severity": "warning",
                        "id": "memoryLeak",
                        "summary": "Memory leak",
                        "row_number": 3
                    },
                    "status": "error",
                    "error": "Analysis failed"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(sample_results, f)
            temp_results = f.name
        
        try:
            # Test analysis script
            cmd = [
                sys.executable,
                "analyze_results.py", 
                temp_results
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"❌ Analysis script failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return False
            
            # Check if report contains expected sections
            output = result.stdout
            expected_sections = [
                "BASIC STATISTICS",
                "DEFECT SEVERITY DISTRIBUTION", 
                "TOP DEFECT TYPES",
                "JSON SUMMARY ANALYSIS",
                "ERROR ANALYSIS"
            ]
            
            for section in expected_sections:
                if section not in output:
                    print(f"❌ Missing section in report: {section}")
                    return False
            
            print("✅ Analysis tools test passed")
            return True
            
        finally:
            try:
                os.unlink(temp_results)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Analysis tools test failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 50)
    print("BATCH EVALUATION TOOLS TEST")
    print("=" * 50)
    
    # Change to evaluation directory
    eval_dir = Path(__file__).parent
    original_cwd = os.getcwd()
    os.chdir(eval_dir)
    
    try:
        tests = [
            test_csv_parsing,
            test_analysis_tools,
            # test_single_defect_processing,  # Skip this for now as it requires full setup
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {e}")
                print()
        
        print("=" * 50)
        print(f"TEST RESULTS: {passed}/{total} tests passed")
        print("=" * 50)
        
        if passed == total:
            print("🎉 All tests passed! The evaluation tools are ready to use.")
            return 0
        else:
            print("⚠️  Some tests failed. Please check the setup and dependencies.")
            return 1
            
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    sys.exit(main()) 