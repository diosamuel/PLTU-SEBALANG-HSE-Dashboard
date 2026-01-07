import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
from utils import load_data, render_sidebar

# Page Config
st.set_page_config(page_title="Spatial Analysis - HSE", layout="wide")

# Data Loading
df_exploded, df_master, df_map = load_data()
df_master_filtered, _ = render_sidebar(df_master, df_exploded)

st.title("Spatial Risk Analysis")

col_map, col_details = st.columns([3, 1])

with col_map:
    if 'lat' in df_master_filtered.columns and 'lon' in df_master_filtered.columns:
        df_geo = df_master_filtered.dropna(subset=['lat', 'lon'])
        
        if not df_geo.empty:
            center_lat = -5.585357333271365
            center_lon = 105.38785245329919
            
            # --- Marker Data: Now includes ALL findings (Removed 'Open' filter) ---
            df_pins = df_geo.copy() 

            map_key = f"map_data_{len(df_geo)}" # Updated key for session state
            
            if map_key not in st.session_state:
                m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
                
                # Satellite Layer
                folium.TileLayer(
                    tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg',
                    attr='&copy; Stadia Maps', name='Stadia Satellite'
                ).add_to(m)
                
                # --- CATEGORY-MATCHED HEATMAP ---
                # Gradient mapping: 0.2 (Positive), 0.4 (Action), 0.6 (Condition), 1.0 (Near Miss)
                custom_gradient = {
                    0.2: '#00526A', # Positive
                    0.4: '#E67E22', # Unsafe Action
                    0.6: '#FFAA00', # Unsafe Condition
                    1.0: '#FF4B4B'  # Near Miss
                }
                
                heat_data = [[row['lat'], row['lon']] for index, row in df_geo.iterrows()]
                HeatMap(heat_data, radius=18, blur=12, gradient=custom_gradient, name='Risk Heatmap').add_to(m)
                
                # Marker Cluster for clickability
                marker_cluster = MarkerCluster(name='All Findings').add_to(m)
                
                def get_color(category):
                    cat_lower = str(category).lower()
                    if 'near miss' in cat_lower: return 'red'
                    if 'unsafe condition' in cat_lower: return 'beige' # Folium 'beige' is close to Orange
                    if 'unsafe action' in cat_lower: return 'orange'
                    if 'positive' in cat_lower: return 'blue'
                    return 'cadetblue' 
                
                for _, row in df_pins.iterrows():
                    kategori = row.get('temuan_kategori', '-')
                    parent = row.get('temuan.nama.parent', '-')
                    child = row.get('temuan.nama', '-')
                    location = row.get('nama_lokasi', '-')
                    status = row.get('temuan_status', 'Unknown')
                    
                    popup_html = f"""
                    <div style="font-family: 'Source Sans Pro', sans-serif; color: #00526A; min-width: 200px;">
                        <b style="font-size: 14px;">{kategori}</b><hr style="margin: 5px 0;">
                        <b>Status:</b> {status}<br>
                        <b>Temuan Nama Parent:</b> {parent}<br>
                        <b>Temuan Nama Child:</b> {child}<br>
                        <b>Temuan Location:</b> {location}
                    </div>
                    """
                    
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color=get_color(kategori), icon='info-sign')
                    ).add_to(marker_cluster)
                
                folium.LayerControl().add_to(m)
                st.session_state[map_key] = m

            st_folium(st.session_state[map_key], width="100%", height=700, returned_objects=[])
        else:
            st.warning("No coordinate matches found for filtered data.")
    else:
        st.warning("Spatial data fields (lat/lon) missing.")

with col_details:
    st.markdown("### Top Lokasi Temuan")
    if 'nama_lokasi' in df_master_filtered.columns:
        top_locs = df_master_filtered.groupby('nama_lokasi')['kode_temuan'].nunique().sort_values(ascending=False).head(20)
        st.dataframe(top_locs)