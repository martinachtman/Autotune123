#!/usr/bin/env python3
"""
Automated test script for Autotune123
Tests the complete pipeline without requiring manual approval
"""

import subprocess
import time
import requests
import json
import sys
import os
from pathlib import Path

def run_docker_command(cmd, description=""):
    """Run a docker command and return the result"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            return result.stdout.strip()
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {description}")
        return None
    except Exception as e:
        print(f"💥 Exception: {description} - {str(e)}")
        return None

def test_container_status():
    """Test if container is running and healthy"""
    print("\n=== Testing Container Status ===")
    result = run_docker_command("docker ps --filter name=autotune123", "Check container status")
    if result and "autotune123" in result:
        print("✅ Container is running")
        return True
    else:
        print("❌ Container not found or not running")
        return False

def test_sample_data_creation():
    """Create sample data for testing"""
    print("\n=== Creating Sample Data ===")
    
    # Use the test data file from the testdata directory
    test_data_dir = Path(__file__).parent.parent / "testdata"
    sample_file = test_data_dir / "sample_autotune.log"
    
    if not sample_file.exists():
        print(f"❌ Sample data file not found: {sample_file}")
        return False
    
    # Copy file to container
    cmd = f"docker cp {sample_file} autotune123-autotune123-1:/app/Autotune123/autotune.log"
    result = run_docker_command(cmd, "Copy sample data to container")
    
    if result is not None:
        # Verify file was created successfully
        verify_cmd = "docker exec autotune123-autotune123-1 wc -l /app/Autotune123/autotune.log"
        verify_result = run_docker_command(verify_cmd, "Verify sample data file")
        if verify_result:
            lines = verify_result.split()[0] if verify_result.split() else "0"
            if int(lines) >= 20:  # Should have at least 20+ lines of data
                print(f"✅ Sample data created successfully ({lines} lines)")
                return True
            else:
                print(f"❌ Sample data file too small ({lines} lines)")
        else:
            print("❌ Could not verify sample data file")
    
    print("❌ Failed to create sample data")
    return False

def test_webui_response():
    """Test if the web UI is responding"""
    print("\n=== Testing Web UI Response ===")
    try:
        response = requests.get("http://localhost:8080", timeout=10)
        if response.status_code == 200:
            print("✅ Web UI is responding")
            return True
        else:
            print(f"❌ Web UI returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Web UI: {str(e)}")
        return False

def test_data_processing():
    """Test the data processing pipeline"""
    print("\n=== Testing Data Processing ===")
    
    # Test the filtering function with proper data loading
    cmd = '''docker exec autotune123-autotune123-1 python3 -c "
import sys
sys.path.append('/app/Autotune123')
from data_processing.get_filtered_data import get_filtered_data
from data_processing.get_recommendations import get_recommendations
import pandas as pd
try:
    # Load data using get_recommendations first
    df = get_recommendations()
    if df is not None and not df.empty:
        # Now test filtering with the loaded data
        times, pump_values, autotune_values = get_filtered_data(df, 'No filter')
        if len(times) > 0 and len(pump_values) > 0 and len(autotune_values) > 0:
            print('SUCCESS: Data processing returned', len(times), 'time points')
            print('Sample data - Time:', times[0] if times else 'None', 'Pump:', pump_values[0] if pump_values else 'None')
        else:
            print('FAILED: Empty data returned from filtering')
    else:
        print('FAILED: No data loaded from get_recommendations')
except Exception as e:
    print('ERROR:', str(e))
"'''
    
    result = run_docker_command(cmd, "Test data processing function")
    if result and "SUCCESS" in result:
        print("✅ Data processing pipeline working")
        return True
    else:
        print("❌ Data processing pipeline failed")
        if result:
            print(f"Output: {result}")
        return False

def test_file_permissions():
    """Test file permissions and access"""
    print("\n=== Testing File Permissions ===")
    
    # Check if autotune.log exists and is readable
    cmd = "docker exec autotune123-autotune123-1 ls -la /app/Autotune123/autotune.log"
    result = run_docker_command(cmd, "Check autotune.log permissions")
    
    if result and "autotune.log" in result:
        print("✅ autotune.log file exists and is accessible")
        return True
    else:
        print("❌ autotune.log file not accessible")
        return False

def test_python_imports():
    """Test that all required Python modules can be imported"""
    print("\n=== Testing Python Imports ===")
    
    cmd = '''docker exec autotune123-autotune123-1 python3 -c "
try:
    import pandas as pd
    import dash
    from data_processing.get_filtered_data import get_filtered_data
    from data_processing.get_recommendations import get_recommendations
    print('SUCCESS: All imports working')
except Exception as e:
    print('ERROR:', str(e))
"'''
    
    result = run_docker_command(cmd, "Test Python imports")
    if result and "SUCCESS" in result:
        print("✅ All Python imports working")
        return True
    else:
        print("❌ Python import issues detected")
        if result:
            print(f"Output: {result}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Autotune123 Automated Tests")
    print("=" * 50)
    
    tests = [
        ("Container Status", test_container_status),
        ("Sample Data Creation", test_sample_data_creation),
        ("Python Imports", test_python_imports),
        ("File Permissions", test_file_permissions),
        ("Data Processing", test_data_processing),
        ("Web UI Response", test_webui_response),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        if not success:
            print(f"⚠️  {test_name} failed - continuing with other tests")
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())