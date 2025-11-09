

def adjust_table(df, new_columns, column_names, start_row_index):
    """Insert the given columns (new_columns = list of new columns) into the pandas dataframe based on column names and start index"""
    for i, new_column in enumerate(new_columns):
        if new_column and len(new_column) > 0:  # if column not empty and has data
            # Calculate the end index based on the available data and new column length
            end_index = min(start_row_index + len(new_column) - 1, len(df) - 1)
            
            # Ensure we don't exceed DataFrame bounds
            if start_row_index < len(df) and column_names[i] in df.columns:
                # Only assign values up to the smaller of: available rows or new column length
                slice_length = end_index - start_row_index + 1
                column_slice = new_column[:slice_length]  # Truncate new_column if needed
                
                df.loc[start_row_index:end_index, column_names[i]] = column_slice
    return df

def isfloat(num):
    try:
        float(num)
        return True
    except (ValueError, TypeError) as e:
        return False

def sum_column(table_data, column):
    total = 0
    for row in table_data[-48:]:
        if isfloat(row[column]):
            total += float(row[column])
    return total

if __name__ == "__main__":
    from .get_recommendations import get_recommendations
    df = get_recommendations()
    l3 = ['0.868', '', '1.218', '', '1.180', '', '1.158', '', '1.114', '', '1.119', '', '0.469',
          '', '0.534', '', '0.541', '', '0.415', '', '0.381', '', '0.381', '', '0.425', '', '0.482', '', '0.600', '',
          '0.600', '', '0.600', '', '0.503', '', '0.480', '', '0.590', '', '0.594', '', '0.600', '', '0.545', '',
          '20000', '']
    new_columns = [[], l3]
    column_names = ["Pump", "Autotune"]
    start_row_index = 4
    adjust_table(df, new_columns, column_names, start_row_index)