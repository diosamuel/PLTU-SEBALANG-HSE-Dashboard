import pandas as pd
import os
from utils import load_data

try:
    print("Loading data...")
    # This will use the logic in utils.py
    df_exploded, df_master, df_map = load_data()
    
    print(f"Master Shape: {df_master.shape}")
    print(f"Map Shape: {df_map.shape}")
    
    if 'nama_lokasi' in df_master.columns:
        print("\nSample 'nama_lokasi' in Master:")
        print(df_master['nama_lokasi'].unique()[:10])
    
    if 'Tempat' in df_map.columns:
        print("\nSample 'Tempat' in Map:")
        print(df_map['Tempat'].unique()[:10])
        

    print("\nChecking Date Parsing:")
    if 'tanggal' in df_master.columns:
        null_dates = df_master['tanggal'].isnull().sum()
        print(f"Null Dates: {null_dates} / {len(df_master)}")
        print(f"Date Range: {df_master['tanggal'].min()} to {df_master['tanggal'].max()}")
        if null_dates == len(df_master):
            print("CRITICAL: All dates are NaT. Check date format.")
            print(f"Sample raw values from original loading might be needed.")
    
    print("\nChecking Merge Results (lat column presence):")
    if 'lat' in df_master.columns:
        non_null_lat = df_master['lat'].notnull().sum()
        print(f"Rows with valid Latitude in Master: {non_null_lat} / {len(df_master)}")
        
        if non_null_lat == 0:
            print("Merge FAILED. No coordinates matched.")
            
            # Diagnostic: Check for intersection
            master_locs = set(df_master['nama_lokasi'].unique())
            map_locs = set(df_map['Tempat'].unique())
            intersection = master_locs.intersection(map_locs)
            print(f"\nIntersection count between nama_lokasi and Tempat: {len(intersection)}")
            print(f"Sample Intersection: {list(intersection)[:5]}")
            
            # Diagnostic: Check lowercased
            master_lower = set(df_master['nama_lokasi'].str.lower().str.strip())
            map_lower = set(df_map['Tempat'].str.lower().str.strip())
            inter_lower = master_lower.intersection(map_lower)
            print(f"\nLOWERCASE Intersection count: {len(inter_lower)}")
            print(f"Sample LOWER Intersection: {list(inter_lower)[:5]}")

    else:
        print("'lat' column NOT PRODUCED in master.")

except Exception as e:
    print(f"Error: {e}")
