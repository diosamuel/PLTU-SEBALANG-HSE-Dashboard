import pandas as pd
from utils import load_data
import ast

try:
    df_exploded, df_master, df_map = load_data()
    print("--- Sample of 'temuan.kondisi.lemma' ---")
    if 'temuan.kondisi.lemma' in df_exploded.columns:
        # Check for list/tuple start
        suspicious = df_exploded[df_exploded['temuan.kondisi.lemma'].astype(str).str.startswith(('(', '['))]
        if not suspicious.empty:
             print(f"Found {len(suspicious)} suspicious rows:")
             print(suspicious['temuan.kondisi.lemma'].head(10).tolist())
        else:
             print("No values starting with ( or [ found.")
             print("Random sample:")
             print(df_exploded['temuan.kondisi.lemma'].dropna().sample(10).tolist())

except Exception as e:
    print(f"Error: {e}")
