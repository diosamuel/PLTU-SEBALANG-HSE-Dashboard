import pandas as pd
from utils import load_data

try:
    df_exploded, df_master, df_map = load_data()
    print("--- Head of 'temuan.kondisi.lemma' ---")
    if 'temuan.kondisi.lemma' in df_exploded.columns:
        print(df_exploded['temuan.kondisi.lemma'].head(20).tolist())
    else:
        print("Column 'temuan.kondisi.lemma' NOT FOUND")
except Exception as e:
    print(f"Error: {e}")
