import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, calculate_kpi, filter_by_date
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="PLTU Sebalang HSE Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Styling (Glassmorphism & Colors) ---
# Styles loaded via utils


# --- 3. Data Loading ---
df_exploded, df_master, df_map = load_data()

if df_master.empty:
    st.error("Data could not be loaded. Please check the data path.")
    st.stop()

# --- 4. Sidebar Filters ---
from utils import render_sidebar
df_master_filtered, df_exploded_filtered, granularity = render_sidebar(df_master, df_exploded)

# --- 5. Header & Global Alerts ---
st.title("HSE Executive Summary")

# Global Alert for Open Near Miss
near_miss_open = df_master_filtered[
    (df_master_filtered['temuan_kategori'] == 'Near Miss') & 
    (df_master_filtered['temuan_status'] == 'Open')
]

if not near_miss_open.empty:
    count_nm = near_miss_open.shape[0]
    st.error(f"ALERT: There are {count_nm} OPEN Near Miss findings requiring immediate attention!")

# --- 6. KPI Cards ---
# Calculate Metrics
total_findings = df_master_filtered['kode_temuan'].nunique()

if 'temuan_status' in df_master_filtered.columns:
    # Use case-insensitive matching for safety
    status_lower = df_master_filtered['temuan_status'].astype(str).str.lower()
    closed_findings = status_lower[status_lower == 'closed'].shape[0]
    open_findings = status_lower[status_lower == 'open'].shape[0]
else:
    closed_findings = 0
    open_findings = 0

if total_findings > 0:
    closing_rate = (closed_findings / total_findings) * 100
else:
    closing_rate = 0.0

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Total Findings</h3>
        <h2>{total_findings}</h2>
        <p style="color:grey; font-size:0.8rem;">Unique 'kode_temuan' count.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Open / Closed</h3>
        <h2>{open_findings} / {closed_findings}</h2>
        <p style="color:grey; font-size:0.8rem;">Active vs Resolved findings.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Closing Rate</h3>
        <h2>{closing_rate:.1f}%</h2>
        <p style="color:grey; font-size:0.8rem;">(Closed / Total) * 100.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 7. Charts (Row 1) ---
col_left, col_right = st.columns([2, 1])

with col_left:
    with st.container():
        st.subheader(f"Finding Trend ({granularity})")
        st.caption("Visualizes the volume of findings over time to identify seasonal trends or spikes.")
        
        # Breakdown Switch
        trend_mode = st.radio("View Mode:", ["Total Trend", "Breakdown by Category"], horizontal=True, label_visibility="collapsed")
        
        # Determine frequency and label based on granularity
        if granularity == 'Daily':
            resample_freq = 'D'
            period_freq = 'D'
            time_label = 'Day'
        else:
            resample_freq = 'M'
            period_freq = 'M'
            time_label = 'Month'

        if 'tanggal' in df_master_filtered.columns:
            if trend_mode == "Total Trend":
                df_trend = df_master_filtered.set_index('tanggal').resample(resample_freq)['kode_temuan'].nunique().reset_index()
                fig_trend = px.line(df_trend, x='tanggal', y='kode_temuan', markers=True, 
                                    color_discrete_sequence=['#00526A'],
                                    title=f"<b>Finding Trend (Total)</b><br><sup style='color:#00526A'>Count of unique 'kode_temuan' per {time_label}</sup>")
            else:
                # Breakdown by Category
                if 'temuan_kategori' in df_master_filtered.columns:
                    # Create a period column for grouping
                    df_temp = df_master_filtered.copy()
                    df_temp['Period'] = df_temp['tanggal'].dt.to_period(period_freq).dt.to_timestamp()
                    
                    df_trend = df_temp.groupby(['Period', 'temuan_kategori'])['kode_temuan'].nunique().reset_index()
                    df_trend.rename(columns={'Period': 'tanggal', 'kode_temuan': 'Count'}, inplace=True)
                    
                    # Define colors specific for this chart or reuse global map if accessible
                    trend_colors = {
                        'Near Miss': '#FF4B4B',
                        'Unsafe Condition': '#FFAA00',
                        'Unsafe Action': '#E67E22',
                        'Positive': '#00526A',
                        'Safe': '#00526A' 
                    }
                    
                    fig_trend = px.line(df_trend, x='tanggal', y='Count', color='temuan_kategori', markers=True,
                                        color_discrete_map=trend_colors,
                                        title=f"<b>Finding Trend (Breakdown)</b><br><sup style='color:#00526A'>Count per Category per {time_label}</sup>")
                else:
                    st.warning("Category column missing.")
                    df_trend = pd.DataFrame() # Fallback
            
            if 'fig_trend' in locals():
                fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                        font=dict(color="#00526A"), 
                                        title=dict(font=dict(color="#00526A")),
                                        xaxis=dict(title=None),
                                        yaxis=dict(title="Count"))
                st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    with st.container():
        st.subheader("Risk Distribution")
        st.caption("Breakdown of findings by Risk Category.")
        if 'temuan_kategori' in df_master_filtered.columns:
            df_risk = df_master_filtered['temuan_kategori'].value_counts().reset_index()
            df_risk.columns = ['Category', 'Count']
            
            # Define colors
            color_map = {
                'Near Miss': '#FF4B4B', # Red
                'Unsafe Condition': '#FFAA00', # Orange
                'Unsafe Action': '#E67E22', # Dark Orange for differentiation
                'Positive': '#00526A', # PLN Dark Blue
            }
            
            fig_pie = px.pie(df_risk, values='Count', names='Category', 
                            color='Category', color_discrete_map=color_map, hole=0.4,
                            title="<b>Risk Distribution</b><br><sup style='color:#00526A'>Proportion of 'temuan_kategori'</sup>")
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#00526A"), 
                                  title=dict(font=dict(color="#00526A")))
            st.plotly_chart(fig_pie, use_container_width=True)

# --- 8. Charts (Row 2: Top Issues) ---
with st.container():
    st.subheader("Top Recuring Issues (Object)")
    st.caption("Identifies the most frequently reported objects to target preventive maintenance.")
    if 'temuan.nama' in df_exploded_filtered.columns and 'temuan_kategori' in df_exploded_filtered.columns:
        
        col_bar, col_line = st.columns([1, 1])
        
        with col_bar:
            # Group by Object AND Category to show category context
            top_objects = df_exploded_filtered.groupby(['temuan.nama', 'temuan_kategori']).size().reset_index(name='Count')
            top_objects.columns = ['Object', 'Category', 'Count']
            
            # Sort by Count to ensure meaningful order
            top_objects = top_objects.sort_values('Count', ascending=False)
            
            # Define colors (Same as Risk Distribution)
            color_map = {
                'Near Miss': '#FF4B4B', # Red
                'Unsafe Condition': '#FFAA00', # Orange
                'Unsafe Action': '#E67E22', # Dark Orange
                'Positive': '#00526A', # PLN Dark Blue
            }
            
            # Custom Legend (Static above scroll area)
            legend_html = "<div style='display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;'>"
            for cat, color in color_map.items():
                legend_html += f"<div style='display: flex; align-items: center;'><span style='width: 12px; height: 12px; background-color: {color}; display: inline-block; margin-right: 5px; border-radius: 2px;'></span><span style='font-size: 12px; color: #00526A;'>{cat}</span></div>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)

            # Dynamic Height
            dynamic_height = max(400, len(top_objects) * 30)
            
            fig_bar = px.bar(top_objects, x='Count', y='Object', orientation='h',
                            color='Category', 
                            color_discrete_map=color_map, # Use consistent colors
                            height=dynamic_height,
                            title="<b>Recurring Issues</b><br><sup style='color:#00526A'>Frequency of 'temuan.nama' by Category</sup>")
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                                  yaxis=dict(autorange="reversed", color="#00526A"),
                                  xaxis=dict(color="#00526A"),
                                  font=dict(color="#00526A"),
                                  title=dict(font=dict(color="#00526A")),
                                  showlegend=False) # Hide internal legend since we added external one
            
            # Convert to HTML for robust scrolling in older Streamlit versions
            import streamlit.components.v1 as components
            chart_html = fig_bar.to_html(include_plotlyjs='cdn', full_html=False)
            
            # Embed with scrolling enabled
            components.html(chart_html, height=400, scrolling=True)
            
        with col_line:
            # Top Object Trend Line Chart
            st.markdown("##### Trend of Recurring Issues") # Generic title
            
            # Get Top 5 Object Names for default selection
            top_5_names = top_objects.groupby('Object')['Count'].sum().nlargest(5).index.tolist()
            all_object_names = top_objects['Object'].unique().tolist()
            
            # Multiselect Filter
            selected_trend_objects = st.multiselect(
                "Select Objects to Filter:",
                options=all_object_names,
                default=top_5_names,
                label_visibility="collapsed"
            )
            
            # Filter Data based on Selection
            if 'tanggal' in df_exploded_filtered.columns:
                if selected_trend_objects:
                    df_trend_filtered = df_exploded_filtered[df_exploded_filtered['temuan.nama'].isin(selected_trend_objects)].copy()
                else:
                    df_trend_filtered = pd.DataFrame() # Empty if nothing selected
                
                if not df_trend_filtered.empty:
                    # Determine frequency based on granularity
                    # Re-evaluating here in case scope is separate
                    freq_alias = 'D' if granularity == 'Daily' else 'M'
                    
                    # Resample by Period (Month or Day) and Object
                    df_trend_filtered['Period'] = pd.to_datetime(df_trend_filtered['tanggal']).dt.to_period(freq_alias).dt.to_timestamp()
                    df_line_data = df_trend_filtered.groupby(['Period', 'temuan.nama']).size().reset_index(name='Count')
                    
                    fig_line_top = px.line(df_line_data, x='Period', y='Count', color='temuan.nama', markers=True,
                                            color_discrete_sequence=px.colors.qualitative.Prism,
                                            title=None)
                    
                    fig_line_top.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                                font=dict(color="#00526A"),
                                                xaxis=dict(title=None, color="#00526A"),
                                                yaxis=dict(title="Count", color="#00526A"),
                                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_line_top, use_container_width=True)
                else:
                    st.info("No objects selected or no data available.")
            else:
                 st.info("Date data missing for trend analysis.")

        
    else:
        st.info("Column 'temuan.nama' not found for object analysis.")

# --- 9. Mini Heatmap (New Requirement) ---
with st.container():
    st.subheader("Heatmaps (Folium)")
    st.caption("Intensity of findings based on location frequency.")
    
    if 'lat' in df_master_filtered.columns and 'lon' in df_master_filtered.columns:
        df_geo_home = df_master_filtered.dropna(subset=['lat', 'lon'])
        
        if not df_geo_home.empty:
            # Fixed Center Coordinates
            center_lat = -5.585357333271365
            center_lon = 105.38785245329919
            
            # Use Session State to prevent re-rendering if data hasn't changed
            # Key depends on data length to allow updates when filter changes
            # Note: We use a simple key strategy. Ideally, hash the dataframe or filter state.
            map_key = f"map_home_{len(df_geo_home)}" 
            
            if map_key not in st.session_state:
                m_home = folium.Map(location=[center_lat, center_lon], zoom_start=16)
                folium.TileLayer(
                    tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg',
                    attr='&copy; CNES, Distribution Airbus DS, &copy; Airbus DS, &copy; PlanetObserver | &copy; Stadia Maps',
                    name='Stadia Satellite'
                ).add_to(m_home)
                
                heat_data = [[row['lat'], row['lon']] for index, row in df_geo_home.iterrows()]
                HeatMap(heat_data, radius=12, blur=8).add_to(m_home)
                
                # --- Custom Legend for Heatmap ---
                # Folium HeatMap uses a default gradient (blue->cyan->lime->yellow->red)
                legend_html = '''
                {% macro html(this, kwargs) %}
                <div style="
                    position: fixed; 
                    bottom: 50px; left: 50px; width: 250px; height: 80px; 
                    background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                    border-radius: 10px; padding: 10px; opacity: 0.9;">
                    <b>Heatmap Findings Intensity</b><br>
                    <div style="background: linear-gradient(to right, blue, cyan, lime, yellow, red); width: 100%; height: 15px; margin-top: 5px;"></div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span>Low (Sparse)</span>
                        <span>High (Dense)</span>
                    </div>
                </div>
                {% endmacro %}
                '''
                from branca.element import MacroElement, Template
                macro = MacroElement()
                macro._template = Template(legend_html)
                m_home.get_root().add_child(macro)
                
                st.session_state[map_key] = m_home
            
            # Display Map using session state object
            st_folium(st.session_state[map_key], height=400, width="100%", returned_objects=[])
        else:
            st.info("No spatial data available for heatmap.")
    else:
        st.warning("Latitude/Longitude data missing.")

