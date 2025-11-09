import pandas as pd
import os
import datetime
import subprocess
import glob
from definitions import new_profile_file_path


def find_latest_autotune_log():
    """Find the most recent autotune log file"""
    home = os.path.expanduser('~')
    autotune_dir = os.path.join(home, 'myopenaps', 'autotune')
    
    # Look for autotune log files with timestamp pattern
    pattern = os.path.join(autotune_dir, 'autotune.*.log')
    log_files = glob.glob(pattern)
    
    # Also check for the old format
    old_format = os.path.join(autotune_dir, 'autotune_recommendations.log')
    if os.path.exists(old_format):
        log_files.append(old_format)
    
    if not log_files:
        return None
    
    # Return the most recently modified file
    return max(log_files, key=os.path.getmtime)


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def check_file_datetime():
    # check if file is older than 60 minutes ago, if so raise error
    recommendations_file_path = find_latest_autotune_log()
    if not recommendations_file_path or not os.path.exists(recommendations_file_path):
        return False
        
    creation_time = modification_date(recommendations_file_path)
    current_time = datetime.datetime.now()
    time_diff = (current_time - creation_time).total_seconds() / 60  # difference in minutes
    
    # Allow files that are up to 60 minutes old
    if time_diff <= 60:
        return True
    else:
        return False

def get_recommendations():
    recommendations_file_path = find_latest_autotune_log()
    if recommendations_file_path and check_file_datetime():
        command = "cp {} {}".format(recommendations_file_path, new_profile_file_path)
        subprocess.call(command, shell=True)
        
        # Read CSV with proper column names since autotune log has no headers
        column_names = ['Parameter', 'Time', 'Pump', 'Autotune']
        df = pd.read_csv(new_profile_file_path, delimiter="|", names=column_names, header=None)
        
        # Clean up the DataFrame
        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Remove spaces in column names
        df.columns = df.columns.str.replace(' ', '')
        
        # Remove spaces within values of column (only for string columns)
        for i in df.columns:
            if df[i].dtype == 'object':  # Only apply to string columns
                df[i] = df[i].astype(str).str.replace(' ', '')
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    else:
        print(AssertionError(
            "Recommendations file old, evaluate and rerun autotune or increase comparison time treshold"))
        return pd.DataFrame()


if __name__ == "__main__":
    df = get_recommendations()
    print(df)
