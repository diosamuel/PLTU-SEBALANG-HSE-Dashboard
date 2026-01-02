import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
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
    # Note: df_master already has 'lat', 'lon' joined in utils.load_data() logic if available
    
    if 'lat' in df_master_filtered.columns and 'lon' in df_master_filtered.columns:
        # Filter purely for mapping (must have coords)
        df_geo = df_master_filtered.dropna(subset=['lat', 'lon'])
        
        if not df_geo.empty:
            # Base Map (Fixed Coordinates as requested)
            center_lat = -5.585357333271365
            center_lon = 105.38785245329919
            
            st.info(f"Debug: {len(df_geo)} findings with coordinates loaded.")
            
            # Show the user the data to prove lat/lon exists and is split
            with st.expander("Show Map Data (Debug)"):
                st.dataframe(df_geo[['kode_temuan', 'nama_lokasi', 'lat', 'lon']].head(50))
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
            
            # --- Layers ---
            # 1. Stadia Alidade Satellite (Default)
            folium.TileLayer(
                tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg',
                attr='&copy; CNES, Distribution Airbus DS, &copy; Airbus DS, &copy; PlanetObserver (Contains Copernicus Data) | &copy; Stadia Maps &copy; OpenMapTiles &copy; OpenStreetMap contributors',
                name='Stadia Satellite'
            ).add_to(m)
            
            # 2. CartoDB Light (Optional Layer for contrast)
            folium.TileLayer('cartodbpositron', name='Street Map (Light)').add_to(m)
            
            # 2. Heatmap (All findings freq)
            heat_data = [[row['lat'], row['lon']] for index, row in df_geo.iterrows()]
            HeatMap(heat_data, radius=15, blur=10, name='Heatmap').add_to(m)
            
            # 3. Markers (Pins) - Only for 'Open' status
            # Check if temuan_status exists
            if 'temuan_status' in df_geo.columns:
                df_pins = df_geo[df_geo['temuan_status'].astype(str).str.lower() == 'open']
            else:
                df_pins = df_geo # Fallback
            
            marker_cluster = MarkerCluster(name='Findings (Open)').add_to(m)
            
            # Color Logic
            def get_color(category):
                cat_lower = str(category).lower()
                if 'near miss' in cat_lower: return 'red'
                if 'unsafe condition' in cat_lower: return 'beige' # Folium doesn't have yellow, beige is close or use custom HTML
                if 'unsafe action' in cat_lower: return 'orange'
                if 'positive' in cat_lower: return 'green'
                return 'blue' # Default
            
            # Folium valid colors: 'red', 'blue', 'green', 'purple', 'orange', 'darkred',
            # 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
            
            for _, row in df_pins.iterrows():
                # Prepare Popup Content
                parent = row['temuan.nama.parent'] if 'temuan.nama.parent' in row else '-'
                child = row['temuan.nama'] if 'temuan.nama' in row else '-'
                location = row['nama_lokasi'] if 'nama_lokasi' in row else '-'
                
                popup_html = f"""
                <b>Parent:</b> {parent}<br>
                <b>Child:</b> {child}<br>
                <b>Loc:</b> {location}
                """
                
                color = get_color(row.get('temuan_kategori', ''))
                
                folium.Marker(
                    location=[row['lat'], row['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(marker_cluster)
            
            folium.LayerControl().add_to(m)
            
            st_folium(m, width="100%", height=700)
        else:
            st.warning("No coordinate matches found for filtered data.")
    else:
        st.warning("Spatial data fields (lat/lon) missing in master dataset.")

with col_details:
    st.markdown("### Top Lokasi Temuan")
    if 'nama_lokasi' in df_master_filtered.columns:
        # Ranking based on unique findings count
        top_locs = df_master_filtered.groupby('nama_lokasi')['kode_temuan'].nunique().sort_values(ascending=False).head(20)
        st.dataframe(top_locs)
