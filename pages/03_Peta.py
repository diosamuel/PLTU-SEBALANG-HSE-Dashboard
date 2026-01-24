import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
from utils import load_data, render_sidebar, set_header_title, HSE_COLOR_MAP
from branca.element import Template, MacroElement

# Page Config
st.set_page_config(page_title="Peta Risiko & Analisis Spasial", layout="wide")

# Data Loading
df_exploded, df_master, df_map = load_data()
df_master_filtered, _, _ = render_sidebar(df_master, df_exploded)
set_header_title("Analisis Risiko Spasial")

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
                
                # Satellite Layer (Stadia Maps with API key)
                folium.TileLayer(
                    tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg?api_key=0956e908-f9e5-41a5-9d89-f01b65803cc9',
                    attr='&copy; Stadia Maps', name='Stadia Satellite'
                ).add_to(m)
                heat_data = [[row['lat'], row['lon']] for index, row in df_geo.iterrows()]
                HeatMap(heat_data, radius=18, blur=12, name='Heatmap Temuan').add_to(m)
                
                # Marker Cluster for clickability
                marker_cluster = MarkerCluster(name='Semua Temuan').add_to(m)
                
                def get_color(category):
                    cat_lower = str(category).lower()
                    if 'near miss' in cat_lower: return 'darkblue'      # #1A237E -> darkblue
                    if 'unsafe condition' in cat_lower: return 'orange' # #F57F17 -> orange
                    if 'unsafe action' in cat_lower: return 'red'       # #B71C1C -> red/darkred
                    if 'positive' in cat_lower: return 'darkgreen'      # #1B5E20 -> darkgreen
                    return 'cadetblue'
                
                def get_light_bg_color(category):
                    """Get lighter background color based on HSE category"""
                    # Light versions of HSE_COLOR_MAP colors (with transparency)
                    light_colors = {
                        'Positive': 'rgba(27, 94, 32, 0.15)',           # Light green
                        'Unsafe Action': 'rgba(183, 28, 28, 0.15)',    # Light red
                        'Unsafe Condition': 'rgba(245, 127, 23, 0.15)', # Light amber
                        'Near Miss': 'rgba(26, 35, 126, 0.15)'         # Light indigo
                    }
                    return light_colors.get(category, 'rgba(255, 255, 255, 0.9)')
                for _, row in df_pins.iterrows():
                    kode_temuan = row.get('kode_temuan', '-')
                    kategori = row.get('temuan_kategori', '-')
                    temuan_nama = row.get('temuan_nama', '-')
                    kondisi = row.get('raw_kondisi', '-')
                    rekomendasi = row.get('raw_rekomendasi', '-')
                    location = row.get('nama_lokasi', '-')
                    judul = row.get('raw_judul', '-')
                    status = row.get('temuan_status', 'Unknown')
                    opened_at = row.get('open_at', '-')
                    closed_at = row.get('close_at', '-') 

                    # Get background color based on category
                    bg_color = get_light_bg_color(kategori)
                    
                    popup_html = f"""
                    <div style="font-family: 'Source Sans Pro', sans-serif; color: #00526A; min-width: 200px; 
                                background-color: {bg_color}; padding: 10px; border-radius: 8px;">
                        <b style="font-size: 14px;">{kategori}</b><hr style="margin: 5px 0;">
                        <b>Kode Temuan:</b> {kode_temuan}<br>
                        <b>Status :</b> {status}<br>
                        <b>Judul:</b> {judul}<br>
                        <b>Temuan:</b> {temuan_nama}<br>
                        <hr/>
                        <b>Kondisi:</b> {kondisi}<br>
                        <b>Rekomendasi:</b> {rekomendasi}<br>
                        <b>Lokasi :</b> {location}<br>
                        <b>Dibuka pada :</b> {opened_at}<br>
                        <!--<b>Ditutup pada :</b> {closed_at}<br>-->
                    </div>
                    """
                    
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color=get_color(kategori), icon='info-sign')
                    ).add_to(marker_cluster)
                
                # --- ADD LEGEND (MacroElement) ---
                
                legend_template = f"""
                {{% macro html(this, kwargs) %}}
                <div id='maplegend' class='maplegend' 
                    style='position: absolute; z-index:9999; background-color: rgba(255, 255, 255, 0.85);
                        border-radius: 8px; padding: 10px; font-size: 12px; bottom: 30px; left: 30px; 
                        border: 1px solid grey; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); font-family: sans-serif;'>
                    <div class='legend-title' style='font-weight: bold; margin-bottom: 5px; font-size: 14px;'>Kategori Temuan</div>
                    <div class='legend-scale'>
                    <ul class='legend-labels' style='list-style: none; padding: 0; margin: 0;'>
                        <li style='margin-bottom: 5px;'><span style='background:{HSE_COLOR_MAP['Near Miss']}; width: 15px; height: 15px; display: inline-block; margin-right: 5px; border-radius: 50%;'></span>Near Miss</li>
                        <li style='margin-bottom: 5px;'><span style='background:{HSE_COLOR_MAP['Unsafe Action']}; width: 15px; height: 15px; display: inline-block; margin-right: 5px; border-radius: 50%;'></span>Unsafe Action</li>
                        <li style='margin-bottom: 5px;'><span style='background:{HSE_COLOR_MAP['Unsafe Condition']}; width: 15px; height: 15px; display: inline-block; margin-right: 5px; border-radius: 50%;'></span>Unsafe Condition</li>
                        <li style='margin-bottom: 5px;'><span style='background:{HSE_COLOR_MAP['Positive']}; width: 15px; height: 15px; display: inline-block; margin-right: 5px; border-radius: 50%;'></span>Positive</li>
                    </ul>
                    </div>
                </div>
                {{% endmacro %}}
                """
                macro = MacroElement()
                macro._template = Template(legend_template)
                m.get_root().add_child(macro)

                folium.LayerControl().add_to(m)
                st.session_state[map_key] = m

            st_folium(st.session_state[map_key], width="100%", height=600, returned_objects=[])
        else:
            st.warning("Tidak ada kecocokan koordinat untuk data yang difilter.")
    else:
        st.warning("Field data spasial (lat/lon) hilang.")

with col_details:
    st.markdown("### Lokasi Temuan Teratas")
    if 'nama_lokasi' in df_master_filtered.columns:
        top_locs = df_master_filtered.groupby('nama_lokasi')['kode_temuan'].nunique().sort_values(ascending=False).head(20).reset_index(name='Total')
        st.dataframe(top_locs, hide_index=True, use_container_width=True)
