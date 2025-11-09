#!/usr/bin/env python3
"""
Unit tests for Autotune data structures
Tests JSON data format and structure validation - no external web services
"""

import unittest
import sys
import os
import json

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'testdata'))

from autotune_test_data import get_test_recommendations

class TestAutotuneData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_recommendations = get_test_recommendations()
        
    def test_get_test_recommendations(self):
        """Test that test data is properly structured"""
        recommendations = get_test_recommendations()
        
        # Check data structure
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check first entry structure
        first_entry = recommendations[0]
        required_keys = ['Parameter', 'Pump', 'Autotune', 'DaysMissing']
        for key in required_keys:
            self.assertIn(key, first_entry)
            
        # Check specific test values
        self.assertEqual(first_entry['Parameter'], 'ISF[mg/dL/U]')
        self.assertEqual(first_entry['Pump'], '45.00')
        self.assertEqual(first_entry['Autotune'], '45.05')
        
    def test_test_data_integrity(self):
        """Test that test data contains expected diabetes management parameters"""
        recommendations = get_test_recommendations()
        
        # Check for ISF entries
        isf_entries = [r for r in recommendations if 'ISF' in r['Parameter']]
        self.assertGreaterEqual(len(isf_entries), 2)  # mg/dL and mmol/L
        
        # Check for carb ratio
        carb_entries = [r for r in recommendations if 'CarbRatio' in r['Parameter']]
        self.assertEqual(len(carb_entries), 1)
        
        # Check for basal rates (24-hour schedule with 30-min intervals)
        basal_entries = [r for r in recommendations if r['Parameter'].count(':') == 1]
        self.assertEqual(len(basal_entries), 48)  # 24 hours * 2 (30-min intervals)
        
    def test_json_serialization(self):
        """Test that profile data can be properly serialized to JSON"""
        recommendations = get_test_recommendations()
        
        # Test JSON serialization
        try:
            json_string = json.dumps(recommendations, ensure_ascii=False, indent=4)
            self.assertIsInstance(json_string, str)
            
            # Test deserialization
            parsed_data = json.loads(json_string)
            self.assertEqual(len(parsed_data), len(recommendations))
            self.assertEqual(parsed_data[0]['Parameter'], recommendations[0]['Parameter'])
            
        except (TypeError, ValueError) as e:
            self.fail(f"JSON serialization failed: {e}")

class TestAutotuneDataStructure(unittest.TestCase):
    """Test the structure and content of autotune test data"""
    
    def test_basal_rate_schedule(self):
        """Test that basal rate schedule covers full 24-hour period"""
        recommendations = get_test_recommendations()
        
        # Extract time-based entries
        time_entries = []
        for entry in recommendations:
            param = entry['Parameter']
            if ':' in param and len(param) == 5:  # Format: "HH:MM"
                try:
                    hour, minute = map(int, param.split(':'))
                    if 0 <= hour <= 23 and minute in [0, 30]:
                        time_entries.append((hour, minute))
                except ValueError:
                    pass
        
        # Should have 48 entries (24 hours * 2 per hour)
        self.assertEqual(len(time_entries), 48)
        
        # Check coverage of full day
        expected_times = [(h, m) for h in range(24) for m in [0, 30]]
        actual_times = sorted(time_entries)
        self.assertEqual(actual_times, expected_times)

if __name__ == '__main__':
    print("🧪 Running Autotune Upload Tests")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2)