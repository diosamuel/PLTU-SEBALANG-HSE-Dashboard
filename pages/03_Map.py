import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from utils import load_data, render_sidebar

# Page Config
st.set_page_config(page_title="Spatial Analysis - HSE", page_icon=None, layout="wide")

# Loaded via utils.render_sidebar()

# Data
df_exploded, df_master, df_map = load_data()
df_master_filtered, _ = render_sidebar(df_master, df_exploded)

st.title("Spatial Risk Analysis")

col_map, col_details = st.columns([3, 1])

with col_map:
    # --- Folium Map ---
    # Merge Master Data with Coordinates
    # We map 'nama_lokasi' to 'location_name' in df_map
    if not df_map.empty and 'nama_lokasi' in df_master_filtered.columns:
        # Standardize join keys
        df_master_filtered['join_key'] = df_master_filtered['nama_lokasi'].str.lower().str.strip()
        df_map['join_key'] = df_map['location_name'].str.lower().str.strip()
        
        df_geo = df_master_filtered.merge(df_map, on='join_key', how='inner')
        
        if not df_geo.empty:
            # Base Map (Sebalang Coordinates approx)
            center_lat = df_geo['lat'].mean()
            center_lon = df_geo['lon'].mean()
            if pd.isnull(center_lat): center_lat = -5.6
            if pd.isnull(center_lon): center_lon = 105.4
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
            
            # Layer Control
            folium.TileLayer('cartodbpositron').add_to(m)
            folium.TileLayer('OpenStreetMap').add_to(m)
            
            marker_cluster = MarkerCluster().add_to(m)
            
            # Color Logic
            def get_color(category):
                if 'Near Miss' in category: return 'red'
                if 'Unsafe' in category: return 'orange'
                return 'darkblue'
            
            for _, row in df_geo.iterrows():
                if pd.notnull(row['lat']) and pd.notnull(row['lon']):
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=f"<b>{row['kode_temuan']}</b><br>{row['nama_lokasi_x']}<br>{row['temuan_kategori']}",
                        icon=folium.Icon(color=get_color(str(row['temuan_kategori'])))
                    ).add_to(marker_cluster)
            
            folium.LayerControl().add_to(m)
            
            st_folium(m, width="100%", height=600)
        else:
            st.warning("No coordinate matches found for filtered data.")
    else:
        st.warning("Map data missing or invalid columns.")

with col_details:
    st.subheader("Top Risk Areas")
    if 'nama_lokasi' in df_master_filtered.columns:
        # Simple Risk Index: Just count needed for now, schema says weighted but simple count is safer MVP
        top_locs = df_master_filtered['nama_lokasi'].value_counts().head(10)
        st.write(top_locs)
