#!/usr/bin/env python3
"""
Simple test runner for core functionality
Uses only the guaranteed working test suite
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_core_tests():
    """Run the core working test suite"""
    print("🧪 Running Core Autotune Test Suite")
    print("=" * 50)
    
    # Import and run the guaranteed working tests
    from tests.test_guaranteed_working import TestWorkingComponents
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWorkingComponents)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'=' * 50}")
    print(f"CORE TEST SUMMARY")
    print(f"{'=' * 50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("✅ All core tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        if result.failures:
            print(f"\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print(f"\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
        return False

if __name__ == '__main__':
    success = run_core_tests()
    sys.exit(0 if success else 1)