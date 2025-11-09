import numpy as np


def clean_values(df):
    # Handle empty DataFrame case
    if df.empty or 'Pump' not in df.columns:
        print("Warning: Empty or invalid DataFrame provided to clean_values")
        return df
        
    if len(df["Pump"]) > 3 and df["Pump"][3] != float: # remove dash from series
        df["Pump"][3] = ""
    df["Pump"] = df["Pump"].replace('',np.nan).astype(float)
    df["Autotune"] = df["Autotune"].replace('',np.nan).astype(float)
    df["Autotune"] = df['Autotune'].apply(lambda x: f'{x:.2f}')
    df["Pump"] = df['Pump'].apply(lambda x: f'{x:.2f}')
    df = df.replace("nan", "")
    return df