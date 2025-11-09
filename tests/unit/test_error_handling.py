#!/usr/bin/env python3
"""
Comprehensive error handling and performance tests
Tests edge cases, error scenarios, and system limits
"""

import unittest
import sys
import os
import tempfile
import time as time_module
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock pandas for import resolution
class MockDataFrame:
    def __init__(self, data=None):
        self.data = data or {}
        self._columns = list(data.keys()) if data else []
        
    @property
    def columns(self):
        return self._columns
        
    def __len__(self):
        return len(list(self.data.values())[0]) if self.data else 0
        
    def empty(self):
        return len(self) == 0
        
    def to_dict(self, orient='records'):
        if not self.data:
            return []
        rows = []
        length = len(list(self.data.values())[0])
        for i in range(length):
            row = {}
            for col, values in self.data.items():
                row[col] = values[i]
            rows.append(row)
        return rows

class MockPandas:
    DataFrame = MockDataFrame

sys.modules['pandas'] = MockPandas()

try:
    from autotune import Autotune
    from autotune_engine import AutotuneEngine, NightscoutClient
except ImportError as e:
    print(f"Warning: Could not import autotune modules: {e}")


class TestNetworkErrorHandling(unittest.TestCase):
    """Test handling of various network errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        self.test_url = "https://test.nightscout.com"
        self.test_token = "test-token"
        
    @patch('autotune_engine.NightscoutClient')
    def test_connection_timeout_handling(self, mock_client_class):
        """Test handling of connection timeouts"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate connection timeout
        import requests
        mock_client.fetch_entries.side_effect = requests.exceptions.ConnectTimeout("Connection timed out")
        
        # Should handle timeout gracefully
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token=self.test_token
        )
        
        # Should return None or empty result, not crash
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')  
    def test_read_timeout_handling(self, mock_client_class):
        """Test handling of read timeouts"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate read timeout
        import requests
        mock_client.fetch_treatments.side_effect = requests.exceptions.ReadTimeout("Read timed out")
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01", 
            end_date="2023-01-02",
            token=self.test_token
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')
    def test_dns_resolution_error(self, mock_client_class):
        """Test handling of DNS resolution errors"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate DNS error
        import requests
        mock_client.fetch_profile.side_effect = requests.exceptions.ConnectionError("Name resolution failed")
        
        result = self.autotune.run_modern(
            nightscout="https://nonexistent.domain.invalid",
            start_date="2023-01-01",
            end_date="2023-01-02", 
            token=self.test_token
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')
    def test_ssl_certificate_error(self, mock_client_class):
        """Test handling of SSL certificate errors"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate SSL error
        import requests
        mock_client.fetch_entries.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token=self.test_token
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))


class TestAuthenticationErrorHandling(unittest.TestCase):
    """Test handling of authentication and authorization errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        self.test_url = "https://test.nightscout.com"
        
    @patch('autotune_engine.NightscoutClient')
    def test_invalid_token_handling(self, mock_client_class):
        """Test handling of invalid authentication tokens"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate 401 Unauthorized
        import requests
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        
        mock_client.fetch_entries.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="invalid-token"
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')
    def test_forbidden_access_handling(self, mock_client_class):
        """Test handling of forbidden access (403)"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate 403 Forbidden
        import requests
        mock_client.fetch_profile.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="limited-token"
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')
    def test_token_expired_handling(self, mock_client_class):
        """Test handling of expired tokens"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate token expiration (could be 401 or custom error)
        mock_client.fetch_treatments.side_effect = Exception("Token expired")
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="expired-token"
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))


class TestDataValidationErrorHandling(unittest.TestCase):
    """Test handling of invalid or corrupted data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        self.test_url = "https://test.nightscout.com"
        self.test_token = "test-token"
        
    @patch('autotune_engine.NightscoutClient')
    def test_malformed_json_handling(self, mock_client_class):
        """Test handling of malformed JSON responses"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate JSON decode error
        mock_client.fetch_entries.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token=self.test_token
        )
        
        self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
        
    @patch('autotune_engine.NightscoutClient')
    def test_missing_required_fields(self, mock_client_class):
        """Test handling of data with missing required fields"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Return data with missing fields
        mock_client.fetch_entries.return_value = [
            {"invalid": "entry"},  # Missing sgv and dateString
            {"sgv": 120},  # Missing dateString
            {"dateString": "2023-01-01T10:00:00Z"}  # Missing sgv
        ]
        
        mock_client.fetch_treatments.return_value = [
            {"invalid": "treatment"},  # Missing required fields
            {"eventType": "Meal Bolus"}  # Missing insulin/carbs
        ]
        
        mock_client.fetch_profile.return_value = {
            "store": {
                "Default": {
                    "invalid": "profile"  # Missing required profile fields
                }
            }
        }
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token=self.test_token
        )
        
        # Should handle gracefully, possibly with empty/default result
        self.assertIsNotNone(result)  # Should not crash
        
    @patch('autotune_engine.NightscoutClient')
    def test_invalid_data_types(self, mock_client_class):
        """Test handling of invalid data types"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Return data with wrong types
        mock_client.fetch_entries.return_value = [
            {"sgv": "not_a_number", "dateString": "2023-01-01T10:00:00Z"},
            {"sgv": None, "dateString": "2023-01-01T10:05:00Z"},
            {"sgv": 120, "dateString": "invalid_date"}
        ]
        
        mock_client.fetch_treatments.return_value = [
            {"eventType": "Meal Bolus", "insulin": "not_a_number", "carbs": "also_not_a_number"}
        ]
        
        mock_client.fetch_profile.return_value = {
            "store": {
                "Default": {
                    "dia": "not_a_number",
                    "carbratio": "invalid_structure",
                    "sens": [],
                    "basal": None
                }
            }
        }
        
        result = self.autotune.run_modern(
            nightscout=self.test_url,
            start_date="2023-01-01",
            end_date="2023-01-02",
            token=self.test_token
        )
        
        # Should handle gracefully
        self.assertIsNotNone(result)


class TestInputValidationErrorHandling(unittest.TestCase):
    """Test handling of invalid inputs"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid.protocol.com",
            "http://",
            "",
            None,
            "javascript:alert('xss')"
        ]
        
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                result = self.autotune.run_modern(
                    nightscout=invalid_url,
                    start_date="2023-01-01",
                    end_date="2023-01-02",
                    token="test-token"
                )
                
                # Should handle invalid URL gracefully
                self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
                
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        invalid_date_combinations = [
            ("2023-02-30", "2023-03-01"),  # Invalid date
            ("2023-01-02", "2023-01-01"),  # End before start
            ("not-a-date", "2023-01-02"),  # Invalid format
            ("2023-01-01", "not-a-date"),  # Invalid format
            ("", "2023-01-02"),  # Empty date
            ("2023-01-01", ""),  # Empty date
            (None, "2023-01-02"),  # None date
            ("2023-01-01", None)  # None date
        ]
        
        for start_date, end_date in invalid_date_combinations:
            with self.subTest(start=start_date, end=end_date):
                result = self.autotune.run_modern(
                    nightscout="https://test.nightscout.com",
                    start_date=start_date,
                    end_date=end_date,
                    token="test-token"
                )
                
                # Should handle invalid dates gracefully
                self.assertTrue(result is None or (hasattr(result, '__len__') and len(result) == 0))
                
    def test_extreme_date_ranges(self):
        """Test handling of extreme date ranges"""
        # Very long date range (should be limited)
        start_date = "2023-01-01"
        end_date = "2023-12-31"  # 365 days
        
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date=start_date,
            end_date=end_date,
            token="test-token"
        )
        
        # Should handle by limiting range or returning empty
        self.assertIsNotNone(result)


class TestPerformanceLimits(unittest.TestCase):
    """Test system performance under various loads"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    @patch('autotune_engine.NightscoutClient')
    def test_large_dataset_memory_usage(self, mock_client_class):
        """Test memory usage with large datasets"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Generate large dataset (simulate 30 days of 5-minute readings)
        entries = []
        base_time = datetime.fromisoformat("2023-01-01T00:00:00")
        
        for i in range(8640):  # 30 days * 24 hours * 12 readings per hour
            time = base_time + timedelta(minutes=i*5)
            entries.append({
                "sgv": 100 + (i % 50),  # Simple pattern
                "dateString": time.isoformat() + ".000Z"
            })
            
        # Generate treatments (3 per day for 30 days)
        treatments = []
        for day in range(30):
            for meal_hour in [7, 12, 18]:
                time = base_time + timedelta(days=day, hours=meal_hour)
                treatments.append({
                    "eventType": "Meal Bolus",
                    "insulin": 8.0 + (day % 3),
                    "carbs": 60,
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
        
        mock_client.fetch_entries.return_value = entries
        mock_client.fetch_treatments.return_value = treatments
        mock_client.fetch_profile.return_value = profile
        
        # Test processing
        start_time = time_module.time()
        
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-30",
            token="test-token"
        )
        
        end_time = time_module.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (2 minutes for 30 days)
        self.assertLess(processing_time, 120.0, f"Large dataset processing took {processing_time:.2f}s - too slow")
        
        # Should produce result
        self.assertIsNotNone(result)
        
        print(f"Large dataset (30 days) processing time: {processing_time:.2f}s")
        print(f"Processed {len(entries)} entries and {len(treatments)} treatments")
        
    @patch('autotune_engine.NightscoutClient')
    def test_concurrent_request_simulation(self, mock_client_class):
        """Test behavior under simulated concurrent load"""
        import threading
        import queue
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simple test data
        mock_client.fetch_entries.return_value = [
            {"sgv": 120, "dateString": "2023-01-01T10:00:00Z"}
        ]
        mock_client.fetch_treatments.return_value = [
            {"eventType": "Meal Bolus", "insulin": 5.0, "carbs": 45}
        ]
        mock_client.fetch_profile.return_value = {
            "store": {"Default": {"dia": 6.0, "carbratio": [], "sens": [], "basal": []}}
        }
        
        # Results queue
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def run_autotune_thread(thread_id):
            """Run autotune in a thread"""
            try:
                autotune = Autotune()
                result = autotune.run_modern(
                    nightscout="https://test.nightscout.com",
                    start_date="2023-01-01",
                    end_date="2023-01-02",
                    token=f"test-token-{thread_id}"
                )
                results_queue.put((thread_id, result))
            except Exception as e:
                errors_queue.put((thread_id, str(e)))
                
        # Start multiple threads
        threads = []
        num_threads = 5
        
        start_time = time_module.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=run_autotune_thread, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
            
        end_time = time_module.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
            
        errors = []
        while not errors_queue.empty():
            errors.append(errors_queue.get())
            
        # Verify results
        self.assertEqual(len(results), num_threads, f"Expected {num_threads} results, got {len(results)}")
        self.assertEqual(len(errors), 0, f"Got unexpected errors: {errors}")
        
        print(f"Concurrent processing ({num_threads} threads) completed in {total_time:.2f}s")
        
    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up"""
        import gc
        
        # Get initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and use autotune objects
        for i in range(10):
            autotune = Autotune()
            # Simulate some usage without actual network calls
            del autotune
            
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory growth
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 1000, f"Memory leak detected: {object_growth} new objects")
        
        print(f"Memory test: {object_growth} object growth after 10 iterations")


class TestEdgeCaseHandling(unittest.TestCase):
    """Test handling of edge cases and unusual scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.autotune = Autotune()
        
    @patch('autotune_engine.NightscoutClient')
    def test_empty_nightscout_data(self, mock_client_class):
        """Test handling of completely empty Nightscout data"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Return empty data for all requests
        mock_client.fetch_entries.return_value = []
        mock_client.fetch_treatments.return_value = []
        mock_client.fetch_profile.return_value = {"store": {}}
        
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="test-token"
        )
        
        # Should handle empty data gracefully
        self.assertIsNotNone(result)
        
    @patch('autotune_engine.NightscoutClient')
    def test_single_data_point(self, mock_client_class):
        """Test handling of minimal data (single data points)"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Return minimal data
        mock_client.fetch_entries.return_value = [
            {"sgv": 120, "dateString": "2023-01-01T10:00:00Z"}
        ]
        mock_client.fetch_treatments.return_value = [
            {"eventType": "Meal Bolus", "insulin": 5.0, "carbs": 45}
        ]
        mock_client.fetch_profile.return_value = {
            "store": {
                "Default": {
                    "dia": 6.0,
                    "carbratio": [{"time": "00:00", "value": 9.0}],
                    "sens": [{"time": "00:00", "value": 45.0}],
                    "basal": [{"time": "00:00", "value": 0.8}]
                }
            }
        }
        
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2023-01-01",
            end_date="2023-01-02",
            token="test-token"
        )
        
        # Should handle minimal data
        self.assertIsNotNone(result)
        
    def test_boundary_date_handling(self):
        """Test handling of boundary date conditions"""
        # Test leap year
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com",
            start_date="2024-02-28",
            end_date="2024-03-01",  # Includes leap day
            token="test-token"
        )
        
        # Should handle leap year gracefully
        self.assertIsNotNone(result)
        
        # Test year boundary
        result = self.autotune.run_modern(
            nightscout="https://test.nightscout.com", 
            start_date="2023-12-31",
            end_date="2024-01-01",
            token="test-token"
        )
        
        # Should handle year boundary
        self.assertIsNotNone(result)


if __name__ == '__main__':
    print("🧪 Running Error Handling and Performance Tests")
    print("=" * 50)
    
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthenticationErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidationErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestInputValidationErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceLimits))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCaseHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Error Handling and Performance Tests Summary:")
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