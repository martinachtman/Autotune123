import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def get_filtered_data(df, filter="No filter"):
    """Clean lists by removing sensitivity, removing IC ratio, and handling sparse basal data.
     Works with realistic basal profiles that only have entries when rates change."""

    # Check if DataFrame is empty or missing required columns
    if df.empty or "Parameter" not in df.columns:
        print("Warning: Empty or invalid DataFrame provided to get_filtered_data")
        return [], [], []

    # Extract all basal data starting from index 2 (skip ISF and CarbRatio headers)
    # Index 2 should be "00:00" - the first basal time slot
    full_data = df.iloc[2:].copy()  # Skip ISF and CarbRatio rows
    
    # Extract time labels, pump values, and autotune values
    times = full_data["Parameter"].tolist()
    pump_values = full_data["Pump"].tolist()
    autotune_values = full_data["Autotune"].tolist()
    
    # Convert string values to float, keep NaN for empty strings
    def convert_to_float(val):
        if val == "" or val is None or pd.isna(val):
            return np.nan
        try:
            return float(val)
        except (ValueError, TypeError):
            return np.nan
    
    # Convert pump and autotune values to float
    pump_float = [convert_to_float(val) for val in pump_values]
    autotune_float = [convert_to_float(val) for val in autotune_values]
    
    # Extract only the non-NaN autotune values for filtering
    autotune_clean = [val for val in autotune_float if not np.isnan(val)]
    
    # Apply the selected filter to the clean values
    if filter == "No filter" or filter == "None" or filter is None:
        filtered_values = autotune_clean
    else:
        if len(autotune_clean) > 0:
            if filter == "Savitzky-Golay 11.6" and len(autotune_clean) >= 11:
                filtered_values = savgol_filter(autotune_clean, 11, 6).tolist()
            elif filter == "Savitzky-Golay 17.5" and len(autotune_clean) >= 17:
                filtered_values = savgol_filter(autotune_clean, 17, 5).tolist()
            elif filter == "Savitzky-Golay 23.3" and len(autotune_clean) >= 23:
                filtered_values = savgol_filter(autotune_clean, 23, 3).tolist()
            else:
                # Default fallback for any unrecognized filter or insufficient data
                filtered_values = autotune_clean
        else:
            filtered_values = autotune_clean
    
    # Put the filtered values back into the original positions
    filtered_autotune = autotune_float.copy()
    filter_idx = 0
    for i, val in enumerate(autotune_float):
        if not np.isnan(val) and filter_idx < len(filtered_values):
            filtered_autotune[i] = round(float(filtered_values[filter_idx]), 2)
            filter_idx += 1
    
    # Create display format for pump values (set half-hour entries to "nan")
    pump_display = []
    for i, (time, pump_val) in enumerate(zip(times, pump_float)):
        if ":30" in str(time):  # Half-hour entries
            pump_display.append("nan")
        else:  # Hour entries or empty entries
            if np.isnan(pump_val):
                pump_display.append("nan")
            else:
                pump_display.append(pump_val)
    
    return times, pump_display, filtered_autotune
