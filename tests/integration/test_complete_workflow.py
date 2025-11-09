#!/usr/bin/env python3
"""
Comprehensive integration tests for the Autotune system
Tests the complete workflow from data fetching to recommendations
"""

import unittest
import sys
import os
import pandas as pd
import json
import tempfile
import time as time_module
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from autotune import Autotune
    from autotune_engine import AutotuneEngine, NightscoutClient
    from data_processing.data_preperation import data_preperation
    from data_processing.get_filtered_data import get_filtered_data
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")


class TestFullAutotuneWorkflow(unittest.TestCase):
    """Test the complete autotune workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        self.test_nightscout_url = "https://test.nightscout.com"
        self.test_token = "test-token-123"
        self.test_start_date = "2023-01-01"
        self.test_end_date = "2023-01-03"
        
        # Create comprehensive test data
        self.test_entries = self._generate_test_entries()
        self.test_treatments = self._generate_test_treatments()
        self.test_profile = self._generate_test_profile()
        
    def _generate_test_entries(self):
        """Generate realistic test entries for 48 hours"""
        entries = []
        base_time = datetime.fromisoformat("2023-01-01T00:00:00")
        
        for i in range(576):  # 48 hours * 12 readings per hour
            time = base_time + timedelta(minutes=i*5)
            
            # Simulate realistic daily patterns
            hour = time.hour
            minute = time.minute
            
            # Base glucose level with daily patterns
            if 6 <= hour <= 8:  # Dawn phenomenon
                base_bg = 140
                variation = 20
            elif 12 <= hour <= 14:  # Lunch period
                base_bg = 160
                variation = 30
            elif 18 <= hour <= 20:  # Dinner period
                base_bg = 155
                variation = 25
            elif 22 <= hour or hour <= 6:  # Night/early morning
                base_bg = 110
                variation = 15
            else:  # Regular day
                base_bg = 120
                variation = 20
                
            # Add some randomness
            bg = base_bg + (i % 7 - 3) * variation // 3
            bg = max(70, min(300, bg))  # Clamp to realistic range
            
            entries.append({
                "sgv": bg,
                "dateString": time.isoformat() + ".000Z",
                "direction": "Flat" if i % 3 == 0 else ("SingleUp" if bg > 140 else "SingleDown")
            })
            
        return entries
        
    def _generate_test_treatments(self):
        """Generate realistic test treatments"""
        treatments = []
        base_time = datetime.fromisoformat("2023-01-01T00:00:00")
        
        # Generate meals for 2 days
        for day in range(2):
            day_offset = timedelta(days=day)
            
            # Breakfast
            breakfast_time = base_time + day_offset + timedelta(hours=7, minutes=30)
            treatments.append({
                "eventType": "Meal Bolus",
                "insulin": 8.5 + (day * 0.5),  # Slight variation between days
                "carbs": 55,
                "created_at": breakfast_time.isoformat() + ".000Z",
                "notes": "Breakfast"
            })
            
            # Lunch
            lunch_time = base_time + day_offset + timedelta(hours=12, minutes=15)
            treatments.append({
                "eventType": "Meal Bolus", 
                "insulin": 10.0 + (day * 0.3),
                "carbs": 70,
                "created_at": lunch_time.isoformat() + ".000Z",
                "notes": "Lunch"
            })
            
            # Dinner
            dinner_time = base_time + day_offset + timedelta(hours=18, minutes=45)
            treatments.append({
                "eventType": "Meal Bolus",
                "insulin": 12.0 + (day * 0.4),
                "carbs": 85,
                "created_at": dinner_time.isoformat() + ".000Z",
                "notes": "Dinner"
            })
            
            # Correction bolus
            if day == 1:  # Add correction on second day
                correction_time = base_time + day_offset + timedelta(hours=15, minutes=30)
                treatments.append({
                    "eventType": "Correction Bolus",
                    "insulin": 2.5,
                    "created_at": correction_time.isoformat() + ".000Z",
                    "notes": "High BG correction"
                })
                
        return treatments
        
    def _generate_test_profile(self):
        """Generate realistic test profile"""
        return {
            "store": {
                "Default": {
                    "dia": 6.0,
                    "carbratio": [
                        {"time": "00:00", "value": 9.0, "timeAsSeconds": 0},
                        {"time": "08:00", "value": 8.5, "timeAsSeconds": 28800},
                        {"time": "12:00", "value": 8.0, "timeAsSeconds": 43200},
                        {"time": "18:00", "value": 8.5, "timeAsSeconds": 64800}
                    ],
                    "sens": [
                        {"time": "00:00", "value": 45.0, "timeAsSeconds": 0},
                        {"time": "06:00", "value": 40.0, "timeAsSeconds": 21600},
                        {"time": "12:00", "value": 50.0, "timeAsSeconds": 43200},
                        {"time": "18:00", "value": 45.0, "timeAsSeconds": 64800}
                    ],
                    "basal": [
                        {"time": "00:00", "value": 0.8, "timeAsSeconds": 0},
                        {"time": "02:00", "value": 0.7, "timeAsSeconds": 7200},
                        {"time": "06:00", "value": 1.1, "timeAsSeconds": 21600},
                        {"time": "08:00", "value": 1.3, "timeAsSeconds": 28800},
                        {"time": "10:00", "value": 1.0, "timeAsSeconds": 36000},
                        {"time": "12:00", "value": 0.9, "timeAsSeconds": 43200},
                        {"time": "14:00", "value": 0.85, "timeAsSeconds": 50400},
                        {"time": "16:00", "value": 0.9, "timeAsSeconds": 57600},
                        {"time": "18:00", "value": 1.0, "timeAsSeconds": 64800},
                        {"time": "20:00", "value": 0.95, "timeAsSeconds": 72000},
                        {"time": "22:00", "value": 0.85, "timeAsSeconds": 79200}
                    ],
                    "target_low": [{"time": "00:00", "value": 4.5, "timeAsSeconds": 0}],
                    "target_high": [{"time": "00:00", "value": 5.0, "timeAsSeconds": 0}],
                    "units": "mmol",
                    "timezone": "UTC"
                }
            },
            "defaultProfile": "Default",
            "startDate": "2023-01-01T00:00:00.000Z"
        }
        
    @patch('autotune_engine.NightscoutClient')
    def test_complete_autotune_workflow(self, mock_client_class):
        """Test the complete autotune workflow with realistic data"""
        # Setup mock client
        mock_client = Mock()  
        mock_client_class.return_value = mock_client
        
        mock_client.fetch_entries.return_value = self.test_entries
        mock_client.fetch_treatments.return_value = self.test_treatments
        mock_client.fetch_profile.return_value = self.test_profile
        
        # Run modern autotune
        result_df = self.autotune.run_modern(
            nightscout=self.test_nightscout_url,
            start_date=self.test_start_date,
            end_date=self.test_end_date,
            uam=False,
            token=self.test_token
        )
        
        # Verify results
        self.assertIsInstance(result_df, pd.DataFrame)
        if result_df is not None:
            self.assertGreater(len(result_df), 0)
            
            # Check required columns
            expected_columns = ['Parameter', 'Pump', 'Autotune', 'Days Missing']
            for col in expected_columns:
                self.assertIn(col, result_df.columns)
                
            # Verify ISF recommendations
            isf_rows = result_df[result_df['Parameter'].str.contains('ISF')]
            self.assertGreater(len(isf_rows), 0)
            
            # Verify carb ratio recommendations
            carb_rows = result_df[result_df['Parameter'].str.contains('CarbRatio')]
            self.assertGreater(len(carb_rows), 0)
            
            # Verify basal recommendations (should have multiple time points)
            basal_rows = result_df[result_df['Parameter'].str.match(r'\d{2}:\d{2}')]
            self.assertGreater(len(basal_rows), 5)  # At least several basal rates
            
            # Verify data quality
            for _, row in result_df.iterrows():
                param = str(row['Parameter'])
                pump = str(row['Pump'])
                autotune = str(row['Autotune'])
                
                # Non-empty parameters
                self.assertIsNotNone(param)
                self.assertNotEqual(param, '')
                
                # Numeric values for non-header rows
                if param not in ['ISF[mg/dL/U]', 'CarbRatio[g/U]'] and ':' in param:
                    try:
                        if pump != '':
                            float(pump)
                        if autotune != '':
                            float(autotune)
                    except ValueError:
                        self.fail(f"Non-numeric value found: {param} - Pump: {pump}, Autotune: {autotune}")
        else:
            self.fail("Autotune returned None instead of DataFrame")
                    
    @patch('autotune_engine.NightscoutClient')
    def test_data_processing_integration(self, mock_client_class):
        """Test integration with data processing pipeline"""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.fetch_entries.return_value = self.test_entries
        mock_client.fetch_treatments.return_value = self.test_treatments
        mock_client.fetch_profile.return_value = self.test_profile
        
        # Run autotune
        result_df = self.autotune.run_modern(
            nightscout=self.test_nightscout_url,
            start_date=self.test_start_date,
            end_date=self.test_end_date,
            uam=False,
            token=self.test_token
        )
        
        # Test data processing pipeline
        if result_df is not None:
            processed_df, graph, y1_sum, y2_sum = data_preperation('All', result_df)
            
            # Verify processed data
            self.assertIsInstance(processed_df, pd.DataFrame)
            self.assertGreaterEqual(len(processed_df), len(result_df))  # Processed may have additional data
        else:
            self.fail("Cannot test data processing with None DataFrame")
        
        # Verify graph object (should be a Plotly figure)
        self.assertIsNotNone(graph)
        
        # Verify sums are numeric
        self.assertIsInstance(y1_sum, (int, float))
        self.assertIsInstance(y2_sum, (int, float))
        self.assertGreater(y1_sum, 0)  # Should have positive insulin totals
        self.assertGreater(y2_sum, 0)
        
    def test_filtering_integration(self):
        """Test integration with data filtering"""
        # Create test data
        test_data = pd.DataFrame({
            'Parameter': ['ISF[mg/dL/U]', '00:00', '01:00', '02:00', '08:00', '12:00'],
            'Pump': ['45.0', '0.8', '0.7', '0.75', '1.1', '0.9'],
            'Autotune': ['47.0', '0.85', '0.72', '0.78', '1.15', '0.92'],
            'Days Missing': ['0', '0', '0', '0', '0', '0']
        })
        
        # Test different filter options
        filter_options = ['All', 'No filter', 'ISF only', 'Basal only']
        
        for filter_option in filter_options:
            with self.subTest(filter=filter_option):
                try:
                    times, pump_values, autotune_values = get_filtered_data(test_data, filter_option)
                    
                    # Verify results
                    self.assertIsInstance(times, list)
                    self.assertIsInstance(pump_values, list)
                    self.assertIsInstance(autotune_values, list)
                    
                    # Verify lengths match
                    self.assertEqual(len(times), len(pump_values))
                    self.assertEqual(len(pump_values), len(autotune_values))
                    
                except Exception as e:
                    self.fail(f"Filter '{filter_option}' failed: {e}")


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling throughout the integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    @patch('autotune_engine.NightscoutClient')
    def test_network_error_handling(self, mock_client_class):
        """Test handling of network errors"""
        # Setup mock client to raise network error
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_entries.side_effect = Exception("Network timeout")
        
        # Should handle error gracefully
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="test-token"
        )
        
        # Should return None or empty DataFrame on error
        self.assertTrue(result is None or len(result) == 0)
        
    @patch('autotune_engine.NightscoutClient')
    def test_authentication_error_handling(self, mock_client_class):
        """Test handling of authentication errors"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_profile.side_effect = Exception("Unauthorized")
        
        # Should handle auth error gracefully  
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01", 
            end_date="2023-01-02",
            token="invalid-token"
        )
        
        self.assertTrue(result is None or len(result) == 0)
        
    @patch('autotune_engine.NightscoutClient')
    def test_malformed_data_handling(self, mock_client_class):
        """Test handling of malformed data"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Return malformed entries
        mock_client.fetch_entries.return_value = [
            {"invalid": "data"},
            {"sgv": "not_a_number", "dateString": "invalid_date"},
            None,
            {"sgv": 120}  # Missing dateString
        ]
        
        mock_client.fetch_treatments.return_value = [
            {"eventType": "Unknown", "invalid": "treatment"},
            None
        ]
        
        mock_client.fetch_profile.return_value = {
            "store": {
                "Default": {
                    "invalid": "profile"
                }
            }
        }
        
        # Should handle malformed data gracefully
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-02", 
            token="test-token"
        )
        
        # May return empty result or basic structure
        self.assertIsInstance(result, (pd.DataFrame, type(None)))


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance aspects of the integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    @patch('autotune_engine.NightscoutClient')
    def test_large_dataset_handling(self, mock_client_class):
        """Test handling of large datasets"""
        # Generate large dataset (1 week of 5-minute readings)
        entries = []
        base_time = datetime.fromisoformat("2023-01-01T00:00:00")
        
        for i in range(2016):  # 7 days * 24 hours * 12 readings per hour
            time = base_time + timedelta(minutes=i*5)
            entries.append({
                "sgv": 100 + (i % 20),  # Simple pattern to avoid complexity
                "dateString": time.isoformat() + ".000Z"
            })
            
        treatments = []
        for day in range(7):
            for meal in [(7, 8.0, 60), (12, 10.0, 75), (18, 12.0, 80)]:
                hour, insulin, carbs = meal
                time = base_time + timedelta(days=day, hours=hour)
                treatments.append({
                    "eventType": "Meal Bolus",
                    "insulin": insulin,
                    "carbs": carbs,
                    "created_at": time.isoformat() + ".000Z"
                })
                
        profile = {
            "store": {
                "Default": {
                    "dia": 6.0,
                    "carbratio": [{"time": "00:00", "value": 9.0}],
                    "sens": [{"time": "00:00", "value": 45.0}],
                    "basal": [{"time": "00:00", "value": 0.8}]
                }
            }
        }
        
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_entries.return_value = entries
        mock_client.fetch_treatments.return_value = treatments
        mock_client.fetch_profile.return_value = profile
        
        # Measure performance
        start_time = time_module.time()
        
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-07",
            token="test-token"
        )
        
        end_time = time_module.time()
        processing_time = end_time - start_time
        
        # Verify results
        self.assertIsInstance(result, pd.DataFrame)
        if result is not None:
            self.assertGreater(len(result), 0)
        else:
            self.fail("Performance test returned None instead of DataFrame")
        
        # Performance should be reasonable (less than 30 seconds for 1 week)
        self.assertLess(processing_time, 30.0, f"Processing took {processing_time:.2f}s - too slow")
        
        print(f"Large dataset processing time: {processing_time:.2f}s for {len(entries)} entries")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with legacy systems"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    def test_legacy_vs_modern_output_compatibility(self):
        """Test that modern output is compatible with legacy data processing"""
        # Create expected output format matching legacy system
        expected_columns = ['Parameter', 'Pump', 'Autotune', 'Days Missing']
        expected_parameters = [
            'ISF[mg/dL/U]',
            'CarbRatio[g/U]',
            '00:00', '01:00', '02:00', '03:00'  # Sample basal times
        ]
        
        # Create mock data in expected format
        test_data = pd.DataFrame({
            'Parameter': expected_parameters,
            'Pump': ['45.0', '9.0', '0.8', '0.7', '0.75', '0.8'],
            'Autotune': ['47.0', '8.5', '0.85', '0.72', '0.78', '0.82'],
            'Days Missing': ['0', '0', '0', '0', '0', '0']
        })
        
        # Test that data processing functions work with this format
        try:
            processed_df, graph, y1_sum, y2_sum = data_preperation('All', test_data)
            
            # Verify compatibility
            self.assertIsInstance(processed_df, pd.DataFrame)
            for col in expected_columns:
                self.assertIn(col, processed_df.columns)
                
        except Exception as e:
            self.fail(f"Legacy compatibility test failed: {e}")


if __name__ == '__main__':
    print("🧪 Running Autotune Integration Tests")
    print("=" * 50)
    
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFullAutotuneWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlingIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Integration Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.failures:
        print("Failures:")
        for test, error in result.failures:
            print(f"  - {test}: {error.split(chr(10))[0]}")
    if result.errors:
        print("Errors:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split(chr(10))[0]}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")