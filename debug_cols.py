import pandas as pd
from utils import load_data

try:
    df_exploded, df_master, df_map = load_data()
    print("--- Columns in df_master ---")
    print(df_master.columns.tolist())
except Exception as e:
    print(f"Error: {e}")
