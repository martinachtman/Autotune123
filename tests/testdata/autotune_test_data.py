#!/usr/bin/env python3
"""
Test data for Autotune123 - Comprehensive autotune recommendations
Contains realistic diabetes management data for testing purposes
"""

# Sample autotune recommendations data structure
SAMPLE_AUTOTUNE_RECOMMENDATIONS = [
    {'Parameter': 'ISF[mg/dL/U]', 'Pump': '45.00', 'Autotune': '45.05', 'DaysMissing': None},
    {'Parameter': 'ISF[mmol/L/U]', 'Pump': '2.50', 'Autotune': '2.50', 'DaysMissing': None},
    {'Parameter': 'CarbRatio[g/U]', 'Pump': '12.00', 'Autotune': '10.70', 'DaysMissing': None},
    {'Parameter': 'Basals[U/hr]', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '00:00', 'Pump': '0.51', 'Autotune': '0.63', 'DaysMissing': '1'},
    {'Parameter': '00:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '01:00', 'Pump': '0.58', 'Autotune': '0.66', 'DaysMissing': '1'},
    {'Parameter': '01:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '02:00', 'Pump': '0.60', 'Autotune': '0.68', 'DaysMissing': '2'},
    {'Parameter': '02:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '03:00', 'Pump': '0.61', 'Autotune': '0.70', 'DaysMissing': '2'},
    {'Parameter': '03:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '04:00', 'Pump': '0.61', 'Autotune': '0.72', 'DaysMissing': '1'},
    {'Parameter': '04:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '05:00', 'Pump': '0.62', 'Autotune': '0.72', 'DaysMissing': '1'},
    {'Parameter': '05:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '06:00', 'Pump': '0.62', 'Autotune': '0.72', 'DaysMissing': '1'},
    {'Parameter': '06:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '07:00', 'Pump': '0.62', 'Autotune': '0.72', 'DaysMissing': '1'},
    {'Parameter': '07:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '08:00', 'Pump': '0.61', 'Autotune': '0.70', 'DaysMissing': '0'},
    {'Parameter': '08:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '09:00', 'Pump': '0.59', 'Autotune': '0.68', 'DaysMissing': '0'},
    {'Parameter': '09:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '10:00', 'Pump': '0.56', 'Autotune': '0.64', 'DaysMissing': '0'},
    {'Parameter': '10:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '11:00', 'Pump': '0.52', 'Autotune': '0.60', 'DaysMissing': '1'},
    {'Parameter': '11:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '12:00', 'Pump': '0.48', 'Autotune': '0.57', 'DaysMissing': '1'},
    {'Parameter': '12:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '13:00', 'Pump': '0.44', 'Autotune': '0.54', 'DaysMissing': '1'},
    {'Parameter': '13:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '14:00', 'Pump': '0.41', 'Autotune': '0.51', 'DaysMissing': '1'},
    {'Parameter': '14:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '15:00', 'Pump': '0.40', 'Autotune': '0.49', 'DaysMissing': '2'},
    {'Parameter': '15:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '16:00', 'Pump': '0.40', 'Autotune': '0.47', 'DaysMissing': '2'},
    {'Parameter': '16:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '17:00', 'Pump': '0.41', 'Autotune': '0.46', 'DaysMissing': '2'},
    {'Parameter': '17:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '18:00', 'Pump': '0.42', 'Autotune': '0.46', 'DaysMissing': '1'},
    {'Parameter': '18:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '19:00', 'Pump': '0.42', 'Autotune': '0.47', 'DaysMissing': '2'},
    {'Parameter': '19:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '20:00', 'Pump': '0.43', 'Autotune': '0.49', 'DaysMissing': '2'},
    {'Parameter': '20:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '21:00', 'Pump': '0.44', 'Autotune': '0.51', 'DaysMissing': '3'},
    {'Parameter': '21:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '22:00', 'Pump': '0.45', 'Autotune': '0.53', 'DaysMissing': '3'},
    {'Parameter': '22:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''},
    {'Parameter': '23:00', 'Pump': '0.46', 'Autotune': '0.54', 'DaysMissing': '3'},
    {'Parameter': '23:30', 'Pump': '', 'Autotune': '', 'DaysMissing': ''}
]

def get_test_recommendations():
    """Return a copy of the sample autotune recommendations for testing"""
    return SAMPLE_AUTOTUNE_RECOMMENDATIONS.copy()

if __name__ == "__main__":
    print("🧪 Autotune123 Test Data")
    print("=" * 40)
    print(f"📊 Sample recommendations: {len(SAMPLE_AUTOTUNE_RECOMMENDATIONS)} entries")
    
    # Display sample data structure
    print("\n📋 Sample Data Structure:")
    for i, entry in enumerate(SAMPLE_AUTOTUNE_RECOMMENDATIONS[:5]):
        print(f"  {i+1}. {entry}")
    print(f"  ... and {len(SAMPLE_AUTOTUNE_RECOMMENDATIONS) - 5} more entries")
    print("\n✅ Pure JSON test data - no external web service references")