import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, calculate_kpi, filter_by_date, HSE_COLOR_MAP
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from utils import render_sidebar, set_header_title
import streamlit.components.v1 as components
from plotly.subplots import make_subplots
from branca.element import MacroElement, Template

def truncate_label(text, limit=12):
    text = str(text)
    if len(text) > limit:
        return text[:limit] + "..."
    return text
st.set_page_config(
    page_title="DASHBOARD ANALISIS IZAT PLN NP UP SEBALANG",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)
df_exploded, df_master, df_map = load_data()

if df_master.empty:
    st.error("Data tidak dapat dimuat. Silakan periksa path data.")
    st.stop()

df_master_filtered, df_exploded_filtered, granularity = render_sidebar(df_master, df_exploded)

set_header_title("DASHBOARD ANALISIS IZAT PLN NP UP SEBALANG")

near_miss_open = df_master_filtered[
    (df_master_filtered['temuan_kategori'] == 'Near Miss') & 
    (df_master_filtered['temuan_status'] == 'Open')
]

if not near_miss_open.empty:
    count_nm = near_miss_open.shape[0]
    st.error(f"PERINGATAN: Ada {count_nm} temuan 'Near Miss' berstatus OPEN yang memerlukan perhatian segera!")

total_findings = len(df_master_filtered['kode_temuan'])

if 'temuan_status' in df_master_filtered.columns:
    status_lower = df_master_filtered['temuan_status'].astype(str).str.lower()
    closed_findings = status_lower[status_lower == 'closed'].shape[0]
    open_findings = status_lower[status_lower == 'open'].shape[0]
    butuh_verifikasi = status_lower[status_lower == 'butuh verifikasi'].shape[0]
else:
    closed_findings = 0
    open_findings = 0
    butuh_verifikasi = 0
if total_findings > 0:
    closing_rate = ((closed_findings) / total_findings) * 100
else:
    closing_rate = 0.0

pending_near_miss = df_master_filtered[
    (df_master_filtered['temuan_kategori'] == 'Near Miss') & 
    (df_master_filtered['temuan_status'] == 'Open')
].shape[0]

# st.write(df_master)
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Total Temuan</h3>
        <h1>{total_findings}</h1>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Open / Closed / Butuh Verifikasi</h3>
        <h1>{open_findings} <span style="opacity:0.2">/</span> {closed_findings} <span style="opacity:0.2">/</span> {butuh_verifikasi}</h1>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Closing Rate</h3>
        <h1>{closing_rate:.1f}%</h1>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Temuan Near Miss Terbuka</h3>
        <h1 style="color: #FF4B4B;">{pending_near_miss}</h1>
    </div>
    """, unsafe_allow_html=True)
# --- 7. Charts (Row 1) ---
col_left, col_right = st.columns([2, 1])

with col_left:
    with st.container():
        st.subheader(f"Tren Temuan ({granularity})")
        st.caption("Visualisasi temuan dari waktu ke waktu untuk mengidentifikasi tren atau lonjakan.")
        
        # Breakdown Switch
        trend_mode = st.radio("Mode Tampilan:", ["Tren Total", "Rincian per Kategori"], horizontal=True, label_visibility="collapsed")
        
        # Determine frequency and label based on granularity
        if granularity == 'Mingguan':
            resample_freq = 'W'
            period_freq = 'W'
            time_label = 'Minggu'
        else:
            resample_freq = 'M'
            period_freq = 'M'
            time_label = 'Bulan'

        if 'tanggal' in df_master_filtered.columns:
            if trend_mode == "Tren Total":
                # Use period grouping instead of resample for better month alignment
                df_temp = df_master_filtered.copy()
                df_temp['Period'] = df_temp['tanggal'].dt.to_period(period_freq).dt.to_timestamp()
                df_trend = df_temp.groupby('Period')['kode_temuan'].nunique().reset_index()
                df_trend.rename(columns={'Period': 'tanggal'}, inplace=True)
                
                fig_trend = px.line(df_trend, x='tanggal', y='kode_temuan', markers=True, 
                                    color_discrete_sequence=['black'],
                                    title=f"<b>Tren Temuan ({time_label})</b>")
                
                # Force show all x-axis labels
                if granularity == 'Mingguan':
                     fig_trend.update_xaxes(dtick="604800000.0", tickformat="%d %b") # Mingguan in ms
                else: 
                     fig_trend.update_xaxes(dtick="M1", tickformat="%b %Y")
            else:
                # Breakdown by Category
                if 'temuan_kategori' in df_master_filtered.columns:
                    # Create a period column for grouping
                    df_temp = df_master_filtered.copy()
                    df_temp['Period'] = df_temp['tanggal'].dt.to_period(period_freq).dt.to_timestamp()
                    df_trend = df_temp.groupby(['Period', 'temuan_kategori'])['kode_temuan'].nunique().reset_index()
                    df_trend.rename(columns={'Period': 'tanggal', 'kode_temuan': 'Count'}, inplace=True)
                    
                    # Use GLOBAL HSE_COLOR_MAP
                    
                    fig_trend = px.line(df_trend, x='tanggal', y='Count', color='temuan_kategori', markers=True,
                                        color_discrete_map=HSE_COLOR_MAP,
                                        title=f"<b>Tren Temuan (Rincian)</b><br><sup style='color:#00526A'>Jumlah per Kategori per {time_label}</sup>")
                    
                    # Force show all x-axis labels
                    if granularity == 'Mingguan':
                         fig_trend.update_xaxes(dtick="604800000.0", tickformat="%d %b")
                    else:
                         fig_trend.update_xaxes(dtick="M1", tickformat="%b %Y")
                else:
                    st.warning("Kolom kategori hilang.")
                    df_trend = pd.DataFrame() # Fallback
            
            if 'fig_trend' in locals():
                fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                        font=dict(color="#00526A"), 
                                        title=dict(font=dict(color="#00526A")),
                                        xaxis=dict(title=None),
                                        yaxis=dict(title="Jumlah"),
                                        height=280, # Compact Height
                                        margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    with st.container():
        st.subheader("Distribusi Risiko")
        st.caption("Rincian temuan berdasarkan Kategori Risiko.")
        if 'temuan_kategori' in df_master_filtered.columns:
            kategori_clean = df_master_filtered['temuan_kategori'].dropna()
            kategori_clean = kategori_clean[kategori_clean.astype(str).str.strip() != '']
            kategori_clean = kategori_clean[kategori_clean.astype(str).str.lower() != 'none']
            
            df_risk = kategori_clean.value_counts().reset_index()
            df_risk.columns = ['Category', 'Count']
            fig_pie = px.pie(df_risk, values='Count', names='Category', 
                            color='Category', color_discrete_map=HSE_COLOR_MAP, hole=0.4,
                            title=" ")
            fig_pie.update_traces(textinfo='percent+value', texttemplate='%{value}<br>(%{percent})')
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#00526A"), 
                                  title=dict(font=dict(color="#00526A")),
                                  height=300,
                                  margin=dict(l=0, r=0, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

# --- 8. Charts (Row 2: Top Issues) ---
if 'temuan_nama_spesifik' in df_exploded_filtered.columns and 'temuan_kategori' in df_exploded_filtered.columns:
    
    col_bar, col_line = st.columns([1, 1])
    
    with col_bar:
        st.subheader("Temuan Berulang Teratas (Objek)")
        st.caption("Mengidentifikasi objek yang paling sering dilaporkan.")
        
    with col_line:
        st.subheader("Tren Temuan Berulang")
        st.caption("Tren volume objek tertentu dari waktu ke waktu.")

    with col_bar:
        # Group by Object AND Category to show category context
            top_objects = df_exploded_filtered.groupby(['temuan_nama_spesifik', 'temuan_kategori']).size().reset_index(name='Count')
            top_objects.columns = ['Object', 'Category', 'Count']
            object_totals = top_objects.groupby('Object')['Count'].sum().reset_index().sort_values('Count', ascending=False)
            sorted_objects = object_totals['Object'].tolist()
            # Filter limit
            limit_mode = st.radio("Tampilkan:", ["Top 10", "Semua"], horizontal=True, key="bar_limit", label_visibility="collapsed")
            if limit_mode == "Top 10":
                top_10_names = sorted_objects[:10]
                top_objects_plot = top_objects[top_objects['Object'].isin(top_10_names)]
            else:
                top_objects_plot = top_objects.copy()

            legend_html = "<div style='display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 5px; margin-top: 5px;'>"
            for cat, color in HSE_COLOR_MAP.items():
                legend_html += f"<div style='display: flex; align-items: center;'><span style='width: 12px; height: 12px; background-color: {color}; display: inline-block; margin-right: 5px; border-radius: 2px;'></span><span style='font-size: 12px; color: #00526A;'>{cat}</span></div>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)

            # Determine Shared X-Axis Range
            max_val = top_objects_plot.groupby(['Object'])['Count'].sum().max()
            if pd.isna(max_val): max_val = 10 
            # Add some padding
            range_x = [0, max_val * 1.1]
            # Group by Object, Sum Count, Sort Descending (Highest at Top visually if reversed)
            plot_totals = top_objects_plot.groupby('Object')['Count'].sum().sort_values(ascending=False)
            sorted_plot_objects = plot_totals.index.tolist()

            # Dynamic Height
            dynamic_height = max(400, len(top_objects_plot) * 30)
            
            # --- 1. Fixed Header (X-Axis) ---
            fig_header = go.Figure()
            fig_header.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(opacity=0))) # Dummy trace
            
            fig_header.update_layout(
                xaxis=dict(
                    range=range_x, 
                    side="top", 
                    title="Jumlah", # Added Title
                    color="#00526A",
                    showgrid=False
                ),
                yaxis=dict(visible=False),

                height=30, # Compact height (Reduced further)
                margin=dict(l=100, r=0, t=30, b=0), # Reduced top margin
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_header, use_container_width=True, config={'displayModeBar': False})

            # --- 2. Scrollable Body (Bars) ---
            top_objects_plot = top_objects_plot.copy()
            top_objects_plot['DisplayObject'] = top_objects_plot['Object'].apply(lambda x: truncate_label(str(x)))

            fig_bar = px.bar(top_objects_plot, x='Count', y='DisplayObject', orientation='h',
                            color='Category', 
                            text='Count', 
                            color_discrete_map=HSE_COLOR_MAP, 
                            height=dynamic_height,
                            category_orders={'DisplayObject': [truncate_label(x) for x in sorted_plot_objects]},
                            hover_data={'Object': True, 'DisplayObject': False}, # Show Full Name on Hover
                            title=None) # Remove Title
            
            fig_bar.update_traces(
                textposition='outside',
                texttemplate='%{value}' # Custom Label Format
            )
            
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                yaxis=dict(
                    autorange="reversed", 
                    color="#00526A",
                    title=None,
                    categoryorder='array', 
                    categoryarray=[truncate_label(x) for x in sorted_plot_objects]
                ),
                xaxis=dict(
                    range=range_x,
                    visible=True, 
                    showticklabels=False,
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                font=dict(color="#00526A"),
                margin=dict(l=100, r=0, t=0, b=0),
                title=None,
                showlegend=False
            )
            
            chart_html = fig_bar.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
            components.html(chart_html, height=280, scrolling=True)
            
    with col_line:
        top_5_names = top_objects.groupby('Object')['Count'].sum().nlargest(5).index.tolist()
        all_object_names = top_objects['Object'].unique().tolist()
        selected_trend_objects = st.multiselect(
            "Pilih Objek untuk Difilter:",
            options=all_object_names,
            default=top_5_names,
            label_visibility="collapsed"
        )
        if 'tanggal' in df_exploded_filtered.columns:
            if selected_trend_objects:
                df_trend_filtered = df_exploded_filtered[df_exploded_filtered['temuan_nama_spesifik'].isin(selected_trend_objects)].copy()
            else:
                df_trend_filtered = pd.DataFrame()
            
            if not df_trend_filtered.empty:
                freq_alias = 'W' if granularity == 'Mingguan' else 'M'
                
                # Resample by Period and Object
                df_trend_filtered['Period'] = pd.to_datetime(df_trend_filtered['tanggal']).dt.to_period(freq_alias).dt.to_timestamp()
                
                # Aggregate by Period and Object
                df_bar_data = df_trend_filtered.groupby(['Period', 'temuan_nama_spesifik']).size().reset_index(name='Count')
                
                # Create complete date range to fill missing periods
                min_period = df_bar_data['Period'].min()
                max_period = df_bar_data['Period'].max()
                if granularity == 'Mingguan':
                    all_periods = pd.date_range(start=min_period, end=max_period, freq='W')
                else:
                    all_periods = pd.date_range(start=min_period, end=max_period, freq='MS')  # Month Start
                
                # Fill missing periods for each object with 0
                df_bar_complete = []
                for obj in selected_trend_objects:
                    df_obj = df_bar_data[df_bar_data['temuan_nama_spesifik'] == obj]
                    df_obj_complete = pd.DataFrame({'Period': all_periods})
                    df_obj_complete = df_obj_complete.merge(df_obj, on='Period', how='left')
                    df_obj_complete['temuan_nama_spesifik'] = obj
                    df_obj_complete['Count'] = df_obj_complete['Count'].fillna(0).astype(int)
                    df_bar_complete.append(df_obj_complete)
                
                df_bar_data = pd.concat(df_bar_complete, ignore_index=True)
                
                # Calculate total per period for line chart
                df_total = df_bar_data.groupby('Period')['Count'].sum().reset_index()
                df_total.columns = ['Period', 'Total']
                
                # Create figure with bars and line
                fig_combo = go.Figure()
                
                # Add stacked bars for each object
                colors = px.colors.qualitative.Plotly
                for idx, obj in enumerate(selected_trend_objects):
                    df_obj = df_bar_data[df_bar_data['temuan_nama_spesifik'] == obj]
                    fig_combo.add_trace(go.Bar(
                        x=df_obj['Period'],
                        y=df_obj['Count'],
                        name=obj,
                        marker_color=colors[idx % len(colors)],
                        text=df_obj['Count'],
                        textposition='inside',
                        textfont=dict(color='white', size=10),
                        hovertemplate='<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>Count: %{y}<extra></extra>'
                    ))
                
                # Add line for total trend
                fig_combo.add_trace(go.Scatter(
                    x=df_total['Period'],
                    y=df_total['Total'],
                    name='Total',
                    mode='lines+markers+text',
                    line=dict(color='black', width=3),
                    marker=dict(size=8),
                    text=df_total['Total'],
                    textposition='top center',
                    textfont=dict(color='black', size=11),
                    yaxis='y2',
                    hovertemplate='<b>Total</b><br>%{x|%d %b %Y}<br>Total: %{y}<extra></extra>'
                ))
                
                # Update layout with secondary y-axis
                fig_combo.update_layout(
                    barmode='stack',
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    xaxis=dict(
                        title=None, 
                        color="#00526A",
                        dtick="M1" if granularity != 'Mingguan' else None,  # Force show all months
                        tickformat="%b %Y" if granularity != 'Mingguan' else "%d %b"
                    ),
                    yaxis=dict(title="Jumlah per Objek", color="#00526A", side='left'),
                    yaxis2=dict(
                        title="Total", 
                        color="black",
                        overlaying='y',
                        side='right',
                        showgrid=False
                    ),
                    height=280,
                    margin=dict(l=0, r=40, t=0, b=0),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.02, 
                        xanchor="right", 
                        x=1,
                        bgcolor="rgba(255,255,255,0.8)"
                    ),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_combo, use_container_width=True)
            else:
                st.info("Tidak ada objek yang dipilih atau data tidak tersedia.")
        else:
                st.info("Data tanggal hilang untuk analisis tren.")

    
else:
    st.info("Column 'temuan_nama_spesifik' not found for object analysis.")

# --- 8. Near Miss Table & Heatmap (Combined) ---
st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)
col_nm, col_map = st.columns([1, 1])

with col_nm:
    st.subheader("Temuan Near Miss")
    high_risk_df = df_master_filtered[df_master_filtered['temuan_kategori'] == 'Near Miss']

    # st.write(df_master_filtered)
    if not high_risk_df.empty:
        # cols_to_show = ['kode_temuan', 'tanggal', 'temuan_nama_spesifik', 'nama_lokasi', 'temuan_status']
        # valid_cols = [c for c in cols_to_show if c in high_risk_df.columns]

        column_rename_map = {
            'kode_temuan': 'Kode Temuan',
            'tanggal': 'Tanggal',
            'temuan_nama_spesifik': 'Objek Temuan',
            'nama_lokasi': 'Lokasi',
            'temuan_status': 'Status'
        }
        df_display = high_risk_df.head(20).copy().rename(columns=column_rename_map)
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=280 # Compact Height
        )
    else:
        st.success("Tidak ada temuan 'Near Miss' dalam seleksi filter ini.")

with col_map:
    st.subheader("Peta Sebaran Temuan")
    st.caption("Intensitas sebaran temuan.")
    
    if 'lat' in df_master_filtered.columns and 'lon' in df_master_filtered.columns:
        df_geo_home = df_master_filtered.dropna(subset=['lat', 'lon'])
        
        if not df_geo_home.empty:
            # Fixed Center Coordinates
            center_lat = -5.585357333271365
            center_lon = 105.38785245329919
            
            map_key = f"map_home_{len(df_geo_home)}" 
            
            if map_key not in st.session_state:
                m_home = folium.Map(location=[center_lat, center_lon], zoom_start=16)
                folium.TileLayer(
                    tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg?api_key=0956e908-f9e5-41a5-9d89-f01b65803cc9',
                    attr='&copy; CNES, Distribution Airbus DS, &copy; Airbus DS, &copy; PlanetObserver | &copy; Stadia Maps',
                    name='Stadia Satellite'
                ).add_to(m_home)
                
                heat_data = [[row['lat'], row['lon']] for index, row in df_geo_home.iterrows()]
                HeatMap(heat_data, radius=12, blur=8).add_to(m_home)
                
                # --- Custom Legend for Heatmap ---
                legend_html = '''
                {% macro html(this, kwargs) %}
                <div style="
                    position: fixed; 
                    bottom: 30px; left: 30px; width: 200px; height: 60px; 
                    background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
                    border-radius: 10px; padding: 5px; opacity: 0.9;">
                    <b>Heatmap Intensity</b><br>
                    <div style="background: linear-gradient(to right, blue, cyan, lime, yellow, red); width: 100%; height: 10px; margin-top: 5px;"></div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px;">
                        <span>Low</span>
                        <span>High</span>
                    </div>
                </div>
                {% endmacro %}
                '''
                macro = MacroElement()
                macro._template = Template(legend_html)
                m_home.get_root().add_child(macro)
                
                st.session_state[map_key] = m_home
            
            st_folium(st.session_state[map_key], height=280, width="100%", returned_objects=[])
        else:
            st.info("Data spasial tidak tersedia untuk heatmap.")
    else:
        st.warning("Data Latitude/Longitude hilang.")

