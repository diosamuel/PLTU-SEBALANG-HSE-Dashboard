import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, render_sidebar

# Page Config
st.set_page_config(page_title="Personnel Performance - HSE", page_icon=None, layout="wide")

# Loaded via utils.render_sidebar()

# Data
df_exploded, df_master, _ = load_data()
df_master_filtered, _ = render_sidebar(df_master, df_exploded)

st.title("Personnel Performance")

# --- A. KPI Row ---
# --- A. KPI Row ---
st.subheader("Performance Overview")

# KPI Logic
unique_reporters = df_master_filtered['creator_name'].nunique() if 'creator_name' in df_master_filtered.columns else 0

max_workload = 0
top_pic = "-"
if 'creator_name' in df_master_filtered.columns:
    # Workload by Reporter (creator_name) instead of Dept (nama) for consistency?
    # Or sticking to original logic? User asked for "Personnel" page, so creator_name makes more sense.
    pic_open_counts = df_master_filtered[df_master_filtered['temuan_status'] == 'Open']['creator_name'].value_counts()
    if not pic_open_counts.empty:
        max_workload = pic_open_counts.iloc[0]
        top_pic = pic_open_counts.index[0]

# Render KPI Cards
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Active Reporters</h3>
        <h2>{unique_reporters}</h2>
        <p style="color:grey; font-size:0.8rem;">Unique contributors</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Max Workload</h3>
        <h2>{max_workload} Tasks</h2>
        <p style="color:grey; font-size:0.8rem;">Held by: {top_pic}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- B. Productivity Scatter ---
with st.container(border=True):
    st.subheader("Productivity Matrix (Volume vs Activity)")
    
    if 'creator_name' in df_master_filtered.columns:
        # Group by Reporter
        # Include Role and Team Role (taking the first/most common value for that person)
        agg_dict = {
            'kode_temuan': 'count',
            'temuan_status': lambda x: (x == 'Open').sum()
        }
        if 'role' in df_master_filtered.columns: agg_dict['role'] = 'first'
        if 'team_role' in df_master_filtered.columns: agg_dict['team_role'] = 'first'
        
        df_perf = df_master_filtered.groupby('creator_name').agg(agg_dict).reset_index()
        
        # Renaissance Columns
        new_cols = ['Reporter', 'Total Findings', 'Open Count']
        if 'role' in df_master_filtered.columns: new_cols.append('Role')
        if 'team_role' in df_master_filtered.columns: new_cols.append('Team Role')
        df_perf.columns = new_cols
        
        # Calculate Closing Rate for Color
        df_perf['Closing Rate'] = ((df_perf['Total Findings'] - df_perf['Open Count']) / df_perf['Total Findings']) * 100
        
        hover_cols = ['Reporter']
        if 'Role' in df_perf.columns: hover_cols.append('Role')
        if 'Team Role' in df_perf.columns: hover_cols.append('Team Role')
        
        fig_scatter = px.scatter(df_perf, x='Total Findings', y='Open Count', 
                                 hover_data=hover_cols,
                                 # text='Reporter', # Removed to prevent clutter
                                 size='Total Findings', 
                                 size_max=40, # Make bubbles slightly larger
                                 color='Closing Rate',
                                 color_continuous_scale='Teal',
                                 title="<b>Workload Analysis</b><br><sup style='color:grey'>X: Total Reports | Y: Active Open Findings | Color: Closing Rate % ((Total-Open)/Total)</sup>")
        
        # fig_scatter.update_traces(textposition='top center') # Removed
        fig_scatter.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
        
        # Add labels only for Top 5 busiest (by Total Findings)
        top_reporters = df_perf.nlargest(5, 'Total Findings')
        for i, row in top_reporters.iterrows():
            fig_scatter.add_annotation(
                x=row['Total Findings'],
                y=row['Open Count'],
                text=row['Reporter'],
                showarrow=False,
                yshift=10,
                font=dict(size=10, color="#00526A")
            )
            
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color='#00526A'))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No reporter data available.")

# --- C. Personnel Detail ---
with st.container(border=True):
    st.subheader("Individual Detail")
    
    # --- Filters for Fast Finding ---
    # Prepare unique lists
    roles_list = ["All"] + sorted(df_master_filtered['role'].dropna().unique().tolist()) if 'role' in df_master_filtered.columns else ["All"]
    teams_list = ["All"] + sorted(df_master_filtered['team_role'].dropna().unique().tolist()) if 'team_role' in df_master_filtered.columns else ["All"]
    
    c_filt1, c_filt2 = st.columns(2)
    sel_role = c_filt1.selectbox("Filter by Role:", roles_list)
    sel_team = c_filt2.selectbox("Filter by Team:", teams_list)
    
    # Filter Logic
    df_reporters = df_master_filtered.copy()
    if sel_role != "All":
        df_reporters = df_reporters[df_reporters['role'] == sel_role]
    if sel_team != "All":
        df_reporters = df_reporters[df_reporters['team_role'] == sel_team]
        
    reporters = sorted(df_reporters['creator_name'].dropna().unique()) if 'creator_name' in df_reporters.columns else []
    
    selected_reporter = st.selectbox("Select Personnel", options=reporters)
    
    if selected_reporter:
        df_person = df_master_filtered[df_master_filtered['creator_name'] == selected_reporter]
        
        # 1. Header Info (Role & Team Role)
        # Attempt to get role from the first row of this person
        role = df_person['role'].iloc[0] if 'role' in df_person.columns else "Unknown Role"
        team_role = df_person['team_role'].iloc[0] if 'team_role' in df_person.columns else "Unknown Team"
        
        # Using columns for layout like the picture
        col_header, _ = st.columns([2, 1])
        with col_header:
            st.markdown(f"""
            <h2 style='margin-bottom:0;'>{selected_reporter}</h2>
            <div style='display:flex; gap: 20px; align-items: baseline;'>
                <div>
                    <h4 style='margin-bottom:0; color:#00526A;'>{role}</h4>
                    <span style='font-size:0.8rem; color:grey;'>(role)</span>
                </div>
                <div>
                    <h4 style='margin-bottom:0; color:#00526A;'>{team_role}</h4>
                    <span style='font-size:0.8rem; color:grey;'>(team role)</span>
                </div>
            </div>
            <br>
            """, unsafe_allow_html=True)
        
        # 2. Charts & Data
        col_chart, col_table = st.columns([1, 2])
        
        with col_chart:
            # Risk Category Pie Chart for this person
            if 'temuan_kategori' in df_person.columns:
                risk_counts = df_person['temuan_kategori'].value_counts().reset_index()
                risk_counts.columns = ['Category', 'Count']
                
                # Colors
                color_map = {
                    'Near Miss': '#FF4B4B', 
                    'Unsafe Condition': '#FFAA00', 
                    'Unsafe Action': '#E67E22', 
                    'Positive': '#00526A',
                    'Safe': '#00526A'
                }
                
                fig_pie = px.pie(risk_counts, values='Count', names='Category',
                                 color='Category', color_discrete_map=color_map, hole=0.4,
                                 title=f"<b>Risk Profile</b><br><sup style='color:grey'>Reports by Category</sup>")
                fig_pie.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color='#00526A'))
                # Force text inside to save space
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                
                st.plotly_chart(fig_pie, use_container_width=True)
                
        with col_table:
            st.write(f"**Reports Submitted:** {df_person.shape[0]}")
            st.dataframe(df_person[['kode_temuan', 'tanggal', 'temuan_kategori', 'temuan_status']], use_container_width=True)
