import numpy as np
import pandas as pd

def isf_conversion(df):
    # Check if DataFrame is empty or missing required columns
    if df.empty or "Parameter" not in df.columns:
        print("Warning: Empty or invalid DataFrame provided to isf_conversion")
        return df
    
    # Find the ISF row
    isf_mask = df["Parameter"] == "ISF[mg/dL/U]"
    if not isf_mask.any():
        print("Warning: No ISF[mg/dL/U] row found, skipping ISF conversion")
        return df
    
    # Check if the ISF row has valid numeric data
    isf_row_idx = df[isf_mask].index[0]
    pump_val = df.loc[isf_row_idx, "Pump"]
    autotune_val = df.loc[isf_row_idx, "Autotune"]
    
    # Skip conversion if values are empty or invalid
    if not pump_val or not autotune_val or pump_val == '' or autotune_val == '':
        print("Warning: ISF values are empty, skipping ISF conversion")
        return df
    
    try:
        # https://stackoverflow.com/questions/24029659/python-pandas-replicate-rows-in-dataframe
        reps = [2 if val=="ISF[mg/dL/U]" else 1 for val in df.Parameter]
        df = df.loc[np.repeat(df.index.values, reps)]
        df = df.reset_index(drop=True)
        
        # Find the new ISF row position after duplication
        isf_idx = df[df["Parameter"] == "ISF[mg/dL/U]"].index[0]
        mmol_idx = isf_idx + 1
        
        # Convert to mmol/L
        df.loc[mmol_idx, "Pump"] = str(round(float(df.loc[isf_idx, "Pump"])/18, 2))
        df.loc[mmol_idx, "Autotune"] = str(round(float(df.loc[isf_idx, "Autotune"])/18, 2))
        df.loc[mmol_idx, "Parameter"] = "ISF[mmol/L/U]"
        df.loc[mmol_idx, "DaysMissing"] = df.loc[isf_idx, "DaysMissing"]
        
        return df
    except (ValueError, KeyError, IndexError) as e:
        print(f"Warning: Failed to convert ISF units: {e}")
        return df

def remove_isf_conversion(df):
    df = df.drop(df.index[1])
    return df


if __name__ == "__main__":
    from .get_recommendations import get_recommendations
    df = get_recommendations()
    df = isf_conversion(df)
    df["Pump"][3] = ""
    df["Pump"] = df["Pump"].replace('',np.nan).astype(float)
    df["Autotune"] = df["Autotune"].replace('',np.nan).astype(float)
    df["Autotune"] = df['Autotune'].apply(lambda x: f'{x:.2f}')
    df["Pump"] = df['Pump'].apply(lambda x: f'{x:.2f}')
    df = df.replace("nan", "")
    print(df)