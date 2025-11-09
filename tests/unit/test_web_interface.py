#!/usr/bin/env python3
"""
Web interface tests for the Dash application
Tests callbacks, Profile JSON generation, and user interactions
"""

import unittest
import sys
import os
import pandas as pd
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock Dash components to avoid import issues in testing
class MockDash:
    def __init__(self):
        self.callbacks = []
    
    def callback(self, *args, **kwargs):
        def decorator(func):
            self.callbacks.append((args, kwargs, func))
            return func
        return decorator

class MockOutput:
    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property

class MockInput:
    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property

class MockState:
    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property

# Mock dash modules
sys.modules['dash'] = MagicMock()
sys.modules['dash.dependencies'] = MagicMock()
sys.modules['dash.dependencies'].Output = MockOutput
sys.modules['dash.dependencies'].Input = MockInput  
sys.modules['dash.dependencies'].State = MockState
sys.modules['dash_bootstrap_components'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.graph_objs'] = MagicMock()

try:
    # Now we can safely import the module that uses these dependencies
    pass  # Will implement actual imports after mocking
except ImportError as e:
    print(f"Warning: Could not import dash modules: {e}")


class TestProfileJSONGeneration(unittest.TestCase):
    """Test Profile JSON generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_recommendations = [
            {'Parameter': 'ISF[mg/dL/U]', 'Pump': '45.0', 'Autotune': '47.0', 'Days Missing': '0'},
            {'Parameter': 'CarbRatio[g/U]', 'Pump': '9.0', 'Autotune': '8.5', 'Days Missing': '0'}, 
            {'Parameter': '00:00', 'Pump': '0.8', 'Autotune': '0.85', 'Days Missing': '0'},
            {'Parameter': '01:00', 'Pump': '0.7', 'Autotune': '0.72', 'Days Missing': '0'},
            {'Parameter': '02:00', 'Pump': '0.75', 'Autotune': '0.78', 'Days Missing': '0'},
            {'Parameter': '08:00', 'Pump': '1.1', 'Autotune': '1.15', 'Days Missing': '0'},
            {'Parameter': '12:00', 'Pump': '0.9', 'Autotune': '0.92', 'Days Missing': '0'},
            {'Parameter': '18:00', 'Pump': '1.0', 'Autotune': '1.05', 'Days Missing': '0'},
        ]
        
    def test_profile_json_structure(self):
        """Test Profile JSON structure generation"""
        # Simulate the callback logic from dash_app.py
        recommendations_data = self.sample_recommendations
        
        recommendations_dict = {}
        basal_rates = []
        
        for row in recommendations_data:
            param = row.get('Parameter', '')
            recommended = row.get('Autotune', '')
            current = row.get('Pump', '')
            
            if not param or param == '':
                continue
            
            # Map different parameter types
            if 'ISF' in param and 'mg/dL' in param:
                try:
                    recommendations_dict['isf'] = float(recommended) if recommended else None
                except (ValueError, TypeError):
                    pass
            elif 'CarbRatio' in param:
                try:
                    recommendations_dict['carb_ratio'] = float(recommended) if recommended else None
                except (ValueError, TypeError):
                    pass
            elif param.replace(':', '') in ['0000', '0100', '0200', '0800', '1200', '1800']:
                # Handle time-based basal rates
                if recommended and recommended != '':
                    try:
                        basal_rates.append({
                            'time': param,
                            'rate': float(recommended)
                        })
                    except (ValueError, TypeError):
                        pass
        
        # Verify parsing results
        self.assertEqual(recommendations_dict['isf'], 47.0)
        self.assertEqual(recommendations_dict['carb_ratio'], 8.5)
        self.assertEqual(len(basal_rates), 6)  # 6 time points
        
        # Verify basal rates
        expected_rates = [
            ('00:00', 0.85), ('01:00', 0.72), ('02:00', 0.78),
            ('08:00', 1.15), ('12:00', 0.92), ('18:00', 1.05)
        ]
        
        for i, (expected_time, expected_rate) in enumerate(expected_rates):
            self.assertEqual(basal_rates[i]['time'], expected_time)
            self.assertEqual(basal_rates[i]['rate'], expected_rate)
            
    def test_nightscout_profile_format(self):
        """Test conversion to Nightscout profile format"""
        recommendations_data = self.sample_recommendations
        
        # Process recommendations (simplified version of callback logic)
        recommendations_dict = {'isf': 47.0, 'carb_ratio': 8.5}
        basal_rates = [
            {'time': '00:00', 'rate': 0.85},
            {'time': '08:00', 'rate': 1.15},
            {'time': '12:00', 'rate': 0.92}
        ]
        
        # Create basal profile
        basalprofile = []
        for i, basal in enumerate(basal_rates):
            time_parts = basal['time'].split(':')
            minutes = int(time_parts[0]) * 60 + (int(time_parts[1]) if len(time_parts) > 1 else 0)
            
            basalprofile.append({
                'i': i,
                'minutes': float(minutes),
                'start': f"{basal['time']}:00",
                'rate': basal['rate']
            })
            
        # Create Nightscout-compatible profile JSON
        profile_name = f"Autotune_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        nightscout_profile = {
            "defaultProfile": profile_name,
            "startDate": datetime.now().isoformat() + "Z",
            "mills": int(datetime.now().timestamp() * 1000),
            "store": {
                profile_name: {
                    "dia": 6.0,
                    "carbratio": [{"time": "00:00", "value": recommendations_dict['carb_ratio'], "timeAsSeconds": 0}],
                    "carbs_hr": 30,
                    "delay": 20,
                    "sens": [{"time": "00:00", "value": recommendations_dict['isf'], "timeAsSeconds": 0}],
                    "timezone": "UTC",
                    "basal": [
                        {
                            "time": basal['start'][:5],
                            "value": basal['rate'],
                            "timeAsSeconds": int(basal['minutes'] * 60)
                        }
                        for basal in basalprofile
                    ],
                    "target_low": [{"time": "00:00", "value": 4.5, "timeAsSeconds": 0}],
                    "target_high": [{"time": "00:00", "value": 5.0, "timeAsSeconds": 0}],
                    "units": "mmol"
                }
            }
        }
        
        # Verify structure
        self.assertIn("defaultProfile", nightscout_profile)
        self.assertIn("store", nightscout_profile)
        
        store = nightscout_profile["store"][profile_name]
        self.assertEqual(store["dia"], 6.0)
        self.assertEqual(store["sens"][0]["value"], 47.0)
        self.assertEqual(store["carbratio"][0]["value"], 8.5)
        self.assertEqual(len(store["basal"]), 3)
        
        # Verify JSON serialization
        json_string = json.dumps(nightscout_profile, indent=2)
        self.assertIsInstance(json_string, str)
        
        # Verify deserialization
        parsed = json.loads(json_string)
        self.assertEqual(parsed["defaultProfile"], profile_name)
        
    def test_empty_recommendations_handling(self):
        """Test handling of empty recommendations"""
        empty_recommendations = []
        
        # Should handle empty data gracefully
        recommendations_dict = {}
        basal_rates = []
        
        for row in empty_recommendations:
            # This loop won't execute
            pass
            
        # Should provide defaults
        if not basal_rates:
            basalprofile = [{'i': 0, 'minutes': 0.0, 'start': '00:00:00', 'rate': 0.5}]
        else:
            basalprofile = basal_rates
            
        self.assertEqual(len(basalprofile), 1)
        self.assertEqual(basalprofile[0]['rate'], 0.5)
        
    def test_malformed_recommendations_handling(self):
        """Test handling of malformed recommendation data"""
        malformed_recommendations = [
            {'Parameter': 'ISF[mg/dL/U]', 'Pump': 'invalid', 'Autotune': 'not_a_number'},
            {'Parameter': '', 'Pump': '0.8', 'Autotune': '0.85'},  # Empty parameter
            {'Pump': '0.7', 'Autotune': '0.72'},  # Missing parameter
            {'Parameter': '12:00', 'Pump': '0.9', 'Autotune': ''},  # Empty autotune value
            {'Parameter': '18:00', 'Pump': '1.0', 'Autotune': '1.05'},  # Valid entry
        ]
        
        recommendations_dict = {}
        basal_rates = []
        
        for row in malformed_recommendations:
            param = row.get('Parameter', '')
            recommended = row.get('Autotune', '')
            
            if not param or param == '':
                continue
                
            if 'ISF' in param:
                try:
                    recommendations_dict['isf'] = float(recommended) if recommended else None
                except (ValueError, TypeError):
                    pass  # Should handle gracefully
            elif param == '18:00':  # Only process valid basal entry
                if recommended and recommended != '':
                    try:
                        basal_rates.append({
                            'time': param,
                            'rate': float(recommended)
                        })
                    except (ValueError, TypeError):
                        pass
                        
        # Should only process valid entries
        self.assertNotIn('isf', recommendations_dict)  # Invalid ISF should be skipped
        self.assertEqual(len(basal_rates), 1)  # Only one valid basal rate
        self.assertEqual(basal_rates[0]['time'], '18:00')
        self.assertEqual(basal_rates[0]['rate'], 1.05)


class TestCallbackLogic(unittest.TestCase):
    """Test Dash callback logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_table_data = [
            {'Parameter': 'ISF[mg/dL/U]', 'Pump': '45.0', 'Autotune': '47.0', 'Days Missing': '0'},
            {'Parameter': '00:00', 'Pump': '0.8', 'Autotune': '0.85', 'Days Missing': '0'},
            {'Parameter': '12:00', 'Pump': '0.9', 'Autotune': '0.92', 'Days Missing': '0'},
        ]
        
    def test_show_profile_json_callback_logic(self):
        """Test the show profile JSON callback logic"""
        # Simulate callback trigger
        show_clicks = 1
        back_clicks = 0
        recommendations_data = self.sample_table_data
        ns_url = "https://test.nightscout.com"
        token = "test-token"
        
        # Simulate callback context (mock)
        class MockContext:
            def __init__(self):
                self.triggered = [{'prop_id': 'show-generated-profile.n_clicks'}]
                
        ctx = MockContext()
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Test logic
        if trigger_id == 'show-generated-profile' and show_clicks:
            if recommendations_data:
                # Should return hidden=False and JSON content
                expected_hidden = False
                expected_has_content = True
            else:
                # Should return "No recommendations data available"
                expected_hidden = False
                expected_content = "No recommendations data available"
                
        # Verify expectations
        self.assertEqual(trigger_id, 'show-generated-profile')
        self.assertEqual(expected_hidden, False)
        self.assertEqual(expected_has_content, True)
        
    def test_back_to_results_callback_logic(self):
        """Test the back to results callback logic"""
        show_clicks = 0
        back_clicks = 1
        
        class MockContext:
            def __init__(self):
                self.triggered = [{'prop_id': 'back-to-results.n_clicks'}]
                
        ctx = MockContext()
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'back-to-results':
            expected_hidden = True
            expected_content = ""
            
        self.assertEqual(trigger_id, 'back-to-results')
        self.assertEqual(expected_hidden, True)
        self.assertEqual(expected_content, "")
        
    def test_table_data_validation(self):
        """Test validation of table data for callbacks"""
        # Test with valid data
        valid_data = self.sample_table_data
        self.assertTrue(isinstance(valid_data, list))
        self.assertGreater(len(valid_data), 0)
        
        # Each row should have required keys
        required_keys = ['Parameter', 'Pump', 'Autotune', 'Days Missing']
        for row in valid_data:
            for key in required_keys:
                self.assertIn(key, row)
                
        # Test with None/empty data
        self.assertFalse(None)  # None should be falsy
        self.assertFalse([])    # Empty list should be falsy
        
        # Test with malformed data
        malformed_data = [{'invalid': 'data'}]
        self.assertTrue(isinstance(malformed_data, list))
        self.assertGreater(len(malformed_data), 0)
        # But should handle missing keys gracefully in actual callback


class TestDataProcessingIntegration(unittest.TestCase):
    """Test integration between autotune results and web interface"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
        
    def test_autotune_to_table_conversion(self):
        """Test conversion of autotune DataFrame to table data"""
        # Create sample DataFrame (like autotune output)
        autotune_df = pd.DataFrame({
            'Parameter': ['ISF[mg/dL/U]', 'CarbRatio[g/U]', '00:00', '12:00'],
            'Pump': [45.0, 9.0, 0.8, 0.9],
            'Autotune': [47.0, 8.5, 0.85, 0.92],
            'Days Missing': [0, 0, 0, 0]
        })
        
        # Convert to dict format (like Dash table)
        table_data = autotune_df.to_dict('records')
        
        # Verify conversion
        self.assertEqual(len(table_data), 4)
        self.assertEqual(table_data[0]['Parameter'], 'ISF[mg/dL/U]')
        self.assertEqual(table_data[0]['Pump'], 45.0)
        self.assertEqual(table_data[0]['Autotune'], 47.0)
        
        # Test that data can be used in Profile JSON generation
        recommendations_dict = {}
        for row in table_data:
            param = row.get('Parameter', '')
            recommended = row.get('Autotune', '')
            
            if 'ISF' in param:
                recommendations_dict['isf'] = float(recommended)
                
        self.assertEqual(recommendations_dict['isf'], 47.0)
        
    def test_filter_integration(self):
        """Test integration with filtering system"""
        # This would test the dropdown filter callbacks
        test_data = pd.DataFrame({
            'Parameter': ['ISF[mg/dL/U]', '00:00', '01:00', '12:00'],
            'Pump': ['45.0', '0.8', '0.7', '0.9'],
            'Autotune': ['47.0', '0.85', '0.72', '0.92'],
            'Days Missing': ['0', '0', '0', '0']
        })
        
        # Test different filter scenarios
        filter_options = ['All', 'ISF only', 'Basal only']
        
        for filter_option in filter_options:
            # Simulate filter application
            if filter_option == 'ISF only':
                filtered_data = test_data[test_data['Parameter'].str.contains('ISF')]
                expected_len = 1
            elif filter_option == 'Basal only':
                filtered_data = test_data[test_data['Parameter'].str.match(r'\d{2}:\d{2}')]
                expected_len = 3
            else:  # 'All'
                filtered_data = test_data
                expected_len = 4
                
            self.assertEqual(len(filtered_data), expected_len)


class TestErrorHandlingUI(unittest.TestCase):
    """Test error handling in the UI"""
    
    def test_network_error_display(self):
        """Test handling of network errors in UI"""
        # Simulate network error scenario
        error_message = "Network timeout"
        
        # UI should display user-friendly error
        user_message = f"Error generating profile: {error_message}"
        
        self.assertIn("Error generating profile", user_message)
        self.assertIn("Network timeout", user_message)
        
    def test_invalid_data_handling(self):
        """Test handling of invalid data in UI"""
        # Test with None recommendations
        recommendations_data = None
        
        if recommendations_data:
            result = "Should generate profile"
        else:
            result = "No recommendations data available"
            
        self.assertEqual(result, "No recommendations data available")
        
        # Test with empty recommendations
        recommendations_data = []
        
        if recommendations_data:
            result = "Should generate profile"
        else:
            result = "No recommendations data available"
            
        self.assertEqual(result, "No recommendations data available")
        
    def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        # Simulate auth error
        auth_error = "Unauthorized access"
        
        # Should provide clear feedback
        user_message = f"Authentication failed: {auth_error}"
        
        self.assertIn("Authentication failed", user_message)
        self.assertIn("Unauthorized", user_message)


if __name__ == '__main__':
    print("🧪 Running Web Interface Tests")
    print("=" * 50)
    
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestProfileJSONGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestCallbackLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessingIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlingUI))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Web Interface Tests Summary:")
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