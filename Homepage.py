import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, calculate_kpi, filter_by_date
from datetime import datetime, timedelta

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="PLTU Sebalang HSE Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Styling (Glassmorphism & Colors) ---
# Styles are loaded via utils.render_sidebar()


# --- 3. Data Loading ---
df_exploded, df_master, df_map = load_data()

if df_master.empty:
    st.error("Data could not be loaded. Please check the data path.")
    st.stop()

# --- 4. Sidebar Filters ---
from utils import render_sidebar
df_master_filtered, df_exploded_filtered = render_sidebar(df_master, df_exploded)

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
total_findings, closing_rate, mttr, participation = calculate_kpi(df_master_filtered)

c1, c2, c3, c4 = st.columns(4)

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
        <h3>Closing Rate</h3>
        <h2>{closing_rate:.1f}%</h2>
        <p style="color:grey; font-size:0.8rem;">(Closed / Total) * 100.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Avg Resolution</h3>
        <h2>{mttr} Days</h2>
        <p style="color:grey; font-size:0.8rem;">Mean Time To Resolve per Finding.</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Participation</h3>
        <h2>{participation}</h2>
        <p style="color:grey; font-size:0.8rem;">Active unique reporters.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 7. Charts (Row 1) ---
col_left, col_right = st.columns([2, 1])

with col_left:
    with st.container(border=True):
        st.subheader("Finding Trend (Monthly)")
        st.caption("Visualizes the volume of findings over time to identify seasonal trends or spikes.")
        # Group by Month
        if 'tanggal' in df_master_filtered.columns:
            df_trend = df_master_filtered.set_index('tanggal').resample('M')['kode_temuan'].nunique().reset_index()
            fig_trend = px.line(df_trend, x='tanggal', y='kode_temuan', markers=True, 
                                color_discrete_sequence=['#00526A'],
                                title="<b>Finding Trend</b><br><sup style='color:grey'>Count of unique 'kode_temuan' per Month</sup>")
            fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    with st.container(border=True):
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
                'Safe': '#00526A' # PLN Dark Blue
            }
            
            fig_pie = px.pie(df_risk, values='Count', names='Category', 
                            color='Category', color_discrete_map=color_map, hole=0.4,
                            title="<b>Risk Distribution</b><br><sup style='color:grey'>Proportion of 'temuan_kategori'</sup>")
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)

# --- 8. Charts (Row 2: Top Issues) ---
with st.container(border=True):
    st.subheader("Top Recuring Issues (Object)")
    st.caption("Identifies the most frequently reported objects to target preventive maintenance.")
    if 'temuan.nama' in df_exploded_filtered.columns:
        top_objects = df_exploded_filtered['temuan.nama'].value_counts().reset_index()
        top_objects.columns = ['Object', 'Count']
        
        # Dynamic Height
        dynamic_height = max(400, len(top_objects) * 30)
        
        fig_bar = px.bar(top_objects, x='Count', y='Object', orientation='h',
                        color_discrete_sequence=['#00526A'],
                        height=dynamic_height,
                        title="<b>Recurring Issues</b><br><sup style='color:grey'>Frequency of 'temuan.nama' elements</sup>")
        fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
        
        # Wrap in scrollable container
        with st.container(height=400):
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Column 'temuan.nama' not found for object analysis.")

