#!/usr/bin/env python3
"""
Integration tests for the complete Autotune123 system
"""

import unittest
import subprocess
import time
import requests
import json
import sys
import os
from pathlib import Path


class TestContainerIntegration(unittest.TestCase):
    """Test container-based integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the class"""
        cls.container_name = "autotune123-autotune123-1"
        cls.base_url = "http://localhost:8080"
        cls.test_data_dir = Path(__file__).parent.parent / "testdata"
        
    def run_docker_command(self, cmd, timeout=30):
        """Helper to run docker commands"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def test_container_is_running(self):
        """Test that the container is running"""
        success, stdout, stderr = self.run_docker_command(
            f"docker ps --filter name={self.container_name}"
        )
        self.assertTrue(success, f"Docker ps command failed: {stderr}")
        self.assertIn(self.container_name, stdout, "Container should be running")
        
    def test_web_interface_responds(self):
        """Test that the web interface responds"""
        try:
            response = requests.get(self.base_url, timeout=10)
            self.assertEqual(response.status_code, 200, 
                           "Web interface should return 200 OK")
        except requests.exceptions.RequestException as e:
            self.fail(f"Could not connect to web interface: {e}")
            
    def test_sample_data_upload(self):
        """Test uploading sample data to container"""
        sample_file = self.test_data_dir / "sample_autotune.log"
        self.assertTrue(sample_file.exists(), "Sample data file should exist")
        
        # Copy sample data to container
        copy_cmd = f"docker cp {sample_file} {self.container_name}:/app/Autotune123/autotune.log"
        success, stdout, stderr = self.run_docker_command(copy_cmd)
        self.assertTrue(success, f"Failed to copy sample data: {stderr}")
        
        # Verify file exists in container
        verify_cmd = f"docker exec {self.container_name} ls -la /app/Autotune123/autotune.log"
        success, stdout, stderr = self.run_docker_command(verify_cmd)
        self.assertTrue(success, f"Failed to verify file in container: {stderr}")
        self.assertIn("autotune.log", stdout, "File should exist in container")
        
    def test_data_processing_in_container(self):
        """Test data processing pipeline in container"""
        # First ensure sample data is uploaded
        self.test_sample_data_upload()
        
        # Test data processing
        test_cmd = f'''docker exec {self.container_name} python3 -c "
import sys
sys.path.append('/app/Autotune123')
try:
    from data_processing.get_recommendations import get_recommendations
    df = get_recommendations()
    if df is not None and not df.empty:
        print('SUCCESS: Loaded', len(df), 'rows')
    else:
        print('FAILED: No data loaded')
except Exception as e:
    print('ERROR:', str(e))
"'''
        
        success, stdout, stderr = self.run_docker_command(test_cmd)
        self.assertTrue(success, f"Data processing command failed: {stderr}")
        self.assertIn("SUCCESS", stdout, f"Data processing should succeed: {stdout}")
        
    def test_filtering_functionality(self):
        """Test filtering functionality with sample data"""
        # First ensure sample data is uploaded
        self.test_sample_data_upload()
        
        # Test filtering
        filter_cmd = f'''docker exec {self.container_name} python3 -c "
import sys
sys.path.append('/app/Autotune123')
try:
    from data_processing.get_recommendations import get_recommendations
    from data_processing.get_filtered_data import get_filtered_data
    
    df = get_recommendations()
    if df is not None and not df.empty:
        times, pump_values, autotune_values = get_filtered_data(df, 'No filter')
        if len(times) > 0:
            print('SUCCESS: Filtered', len(times), 'time points')
            print('Sample time:', times[0] if times else 'None')
        else:
            print('FAILED: No filtered data')
    else:
        print('FAILED: No input data')
except Exception as e:
    print('ERROR:', str(e))
"'''
        
        success, stdout, stderr = self.run_docker_command(filter_cmd)
        self.assertTrue(success, f"Filtering command failed: {stderr}")
        self.assertIn("SUCCESS", stdout, f"Filtering should succeed: {stdout}")


class TestSystemWorkflow(unittest.TestCase):
    """Test complete system workflow"""
    
    def setUp(self):
        """Set up for each test"""
        self.container_name = "autotune123-autotune123-1"
        self.test_data_dir = Path(__file__).parent.parent / "testdata"
        
    def run_docker_command(self, cmd, timeout=30):
        """Helper to run docker commands"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def test_complete_data_pipeline(self):
        """Test the complete data processing pipeline"""
        # Step 1: Upload sample data
        sample_file = self.test_data_dir / "sample_autotune.log"
        copy_cmd = f"docker cp {sample_file} {self.container_name}:/app/Autotune123/autotune.log"
        success, stdout, stderr = self.run_docker_command(copy_cmd)
        self.assertTrue(success, f"Failed to upload sample data: {stderr}")
        
        # Step 2: Process data and generate recommendations
        process_cmd = f'''docker exec {self.container_name} python3 -c "
import sys
sys.path.append('/app/Autotune123')
try:
    from data_processing.get_recommendations import get_recommendations
    from data_processing.get_filtered_data import get_filtered_data
    
    # Load data
    df = get_recommendations()
    print('Loaded DataFrame with', len(df), 'rows')
    
    # Process with filtering
    times, pump_values, autotune_values = get_filtered_data(df, 'No filter')
    print('Filtered results:', len(times), 'time points')
    
    # Verify data integrity
    if len(times) > 0 and len(pump_values) > 0 and len(autotune_values) > 0:
        print('SUCCESS: Complete pipeline working')
    else:
        print('FAILED: Pipeline produced empty results')
        
except Exception as e:
    print('ERROR:', str(e))
    import traceback
    traceback.print_exc()
"'''
        
        success, stdout, stderr = self.run_docker_command(process_cmd, timeout=60)
        self.assertTrue(success, f"Data processing pipeline failed: {stderr}")
        self.assertIn("SUCCESS", stdout, f"Pipeline should complete successfully: {stdout}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)