#!/usr/bin/env python3
"""
Test script for CppCheck API endpoint.
This script tests the new /api/cppcheck/analyze endpoint.

NOTE: This is a temporary test file. You can delete it after verifying the API works.
To test: python test_cppcheck_api.py
"""

import requests
import json
import sys
import time

def test_cppcheck_api():
    """Test the CppCheck analysis API endpoint."""
    
    # Test data
    test_data = {
        "cppcheck_data": {
            "file": "src/utils/example.c",
            "line": 42,
            "severity": "error",
            "id": "nullPointer",
            "summary": "Null pointer dereference"
        },
        "debug": False,
        "thread_id": "__test__",
        "max_plan_iterations": 1,
        "max_step_num": 3,
        "auto_accepted_plan": True,
        "enable_background_investigation": False
    }
    
    # API endpoint
    url = "http://localhost:8000/api/cppcheck/analyze"
    
    print("Testing CppCheck API endpoint...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        # Send POST request
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ API endpoint is responding")
            print("Streaming response:")
            print("-" * 30)
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('event:') or decoded_line.startswith('data:'):
                        print(decoded_line)
                        
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running on localhost:8000?")
        print("Start the server with: python server.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✅ Test completed successfully!")
    return True


def test_api_validation():
    """Test API validation with invalid data."""
    
    # Test with missing required fields
    invalid_data = {
        "cppcheck_data": {
            "file": "test.c",
            # missing line, severity, id, summary
        }
    }
    
    url = "http://localhost:8000/api/cppcheck/analyze"
    
    print("\nTesting API validation...")
    
    try:
        response = requests.post(
            url,
            json=invalid_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ API validation is working (422 returned for invalid data)")
        else:
            print(f"⚠️  Expected 422 but got {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("CppCheck API Test Suite")
    print("=" * 40)
    
    # Test basic API functionality
    success = test_cppcheck_api()
    
    if success:
        # Test validation
        test_api_validation()
    
    print("\nInstructions:")
    print("1. Make sure the server is running: python server.py")
    print("2. Make sure environment variables are set (CPPCHECK_PROJECT_DIR, API keys, etc.)")
    print("3. Test the frontend by opening the web interface and using the CppCheck input mode") 