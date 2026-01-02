import pandas as pd
from utils import load_data

try:
    df_exploded, df_master, df_map = load_data()
    if 'team_role' in df_master.columns:
        print("--- Unique team_role ---")
        print(df_master['team_role'].unique().tolist())
    else:
        print("team_role NOT FOUND")
except Exception as e:
    print(f"Error: {e}")
