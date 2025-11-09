#!/usr/bin/env python3
"""
Unit tests for data processing functions
"""

import unittest
import sys
import os
import pandas as pd
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from data_processing.get_filtered_data import get_filtered_data
    from data_processing.get_recommendations import get_recommendations
except ImportError as e:
    print(f"Warning: Could not import data processing modules: {e}")
    print("These tests require the data processing modules to be available")


class TestDataProcessing(unittest.TestCase):
    """Test data processing functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = Path(__file__).parent.parent / "testdata"
        self.sample_file = self.test_data_dir / "sample_autotune.log"
        
    def test_sample_data_exists(self):
        """Test that sample data files exist"""
        self.assertTrue(self.sample_file.exists(), "Sample autotune.log file should exist")
        
    def test_sample_data_format(self):
        """Test that sample data has correct format"""
        with open(self.sample_file, 'r') as f:
            content = f.read()
        
        # Check for required sections
        self.assertIn("ISF |", content, "Should contain ISF data")
        self.assertIn("CarbRatio |", content, "Should contain CarbRatio data") 
        self.assertIn("Basal |", content, "Should contain Basal data")
        
        # Count lines (should have meaningful data)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        self.assertGreater(len(lines), 20, "Should have at least 20 lines of data")
        
    def test_data_processing_with_mock_data(self):
        """Test data processing with mock DataFrame"""
        # Create mock data similar to what get_recommendations would return
        mock_data = {
            'Parameter': ['ISF', 'CarbRatio', '00:00', '01:00', '02:00', '08:00'],
            'Pump': ['', '', '0.85', '0.72', '0.68', '1.15'],
            'Autotune': ['', '', '0.92', '0.78', '0.74', '1.25']
        }
        df = pd.DataFrame(mock_data)
        
        try:
            times, pump_values, autotune_values = get_filtered_data(df, "No filter")
            
            # Verify results
            self.assertIsInstance(times, list, "Times should be a list")
            self.assertIsInstance(pump_values, list, "Pump values should be a list")
            self.assertIsInstance(autotune_values, list, "Autotune values should be a list")
            
            # Should have 4 time points (skip ISF and CarbRatio rows)
            self.assertEqual(len(times), 4, "Should have 4 time points")
            self.assertEqual(len(pump_values), 4, "Should have 4 pump values")
            self.assertEqual(len(autotune_values), 4, "Should have 4 autotune values")
            
        except Exception as e:
            self.fail(f"Data processing failed with error: {e}")
            
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        
        try:
            times, pump_values, autotune_values = get_filtered_data(empty_df, "No filter")
            
            # Should return empty lists for empty input
            self.assertEqual(times, [], "Should return empty times list")
            self.assertEqual(pump_values, [], "Should return empty pump values list") 
            self.assertEqual(autotune_values, [], "Should return empty autotune values list")
            
        except Exception as e:
            self.fail(f"Empty DataFrame handling failed with error: {e}")


class TestFileOperations(unittest.TestCase):
    """Test file operations and data loading"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = Path(__file__).parent.parent / "testdata"
        
    def test_testdata_directory_exists(self):
        """Test that testdata directory exists"""
        self.assertTrue(self.test_data_dir.exists(), "testdata directory should exist")
        self.assertTrue(self.test_data_dir.is_dir(), "testdata should be a directory")
        
    def test_sample_files_readable(self):
        """Test that sample files are readable"""
        sample_files = ["sample_autotune.log", "alternative_autotune.log"]
        
        for filename in sample_files:
            filepath = self.test_data_dir / filename
            with self.subTest(filename=filename):
                self.assertTrue(filepath.exists(), f"{filename} should exist")
                
                # Test readability
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    self.assertGreater(len(content), 0, f"{filename} should not be empty")
                except Exception as e:
                    self.fail(f"Could not read {filename}: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)