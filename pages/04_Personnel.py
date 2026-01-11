import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from utils import load_data, render_sidebar, set_header_title, HSE_COLOR_MAP

# Page Config
# Page Config
st.set_page_config(page_title="Kinerja Personil", page_icon=None, layout="wide")

# Loaded via utils.render_sidebar()

# Data
df_exploded, df_master, _ = load_data()
df_master_filtered, _ = render_sidebar(df_master, df_exploded)[:2]
set_header_title("Analisis Kinerja Personil")



# --- A. KPI Row ---
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
        <h3>Pelapor Aktif</h3>
        <h2>{unique_reporters}</h2>
        <p style="color:grey; font-size:0.8rem;">Kontributor unik</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Beban Kerja Maksimal</h3>
        <h2>{max_workload} Temuan</h2>
        <p style="color:grey; font-size:0.8rem;">Oleh: {top_pic}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Tabs for Analysis ---
# --- C. Data Processing for Tabs ---
dept_col = 'team_role' if 'team_role' in df_master_filtered.columns else None
df_dept = pd.DataFrame()

if dept_col:
    # 1. Calculate detailed breakdown
    df_dept = df_master_filtered.groupby(dept_col).agg(
        Total=('kode_temuan', 'nunique'),
        Closed=('temuan_status', lambda x: (x.str.lower() == 'closed').sum())
    ).reset_index()
    
    df_dept['Open'] = df_dept['Total'] - df_dept['Closed']
    df_dept['Compliance%'] = (df_dept['Closed'] / df_dept['Total'] * 100).round(1)
    
    # Calculate Radar Metrics
    # Activeness Point = Total Findings
    # Effort Factor = Closed Findings
    # RCI = (Activeness * 0.5 + Effort * 0.5)
    df_dept['Activeness'] = df_dept['Total']
    df_dept['Effort'] = df_dept['Closed']
    df_dept['RCI'] = (df_dept['Activeness'] * 0.5 + df_dept['Effort'] * 0.5)
    
    # Sort so highest volume is at the top
    df_dept = df_dept.sort_values('Total', ascending=True)

# --- Tabs for Analysis ---
tab_dept, tab_personnel = st.tabs(["Departemen", "Personil"])

# =============================================
# TAB 1: DEPARTMENT (Grid Layout)
# =============================================
with tab_dept:
    # Create 3-column grid: Left 2/3 for charts, Right 1/3 for radar
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # --- Row 1: Department Performance ---
        st.subheader("Kinerja Departemen")
        st.caption("Volume total vs status penyelesaian per departemen.")
    
        if not df_dept.empty:
            # View Options
            c_view, _ = st.columns([1, 2])
            dept_view = c_view.radio("Tampilan:", ["Scrollable", "Fit To Screen"], horizontal=True, label_visibility="collapsed", key="dept_view_radio")
            
            # Truncate long department names (max 30 chars)
            def truncate_dept(name, limit=30):
                name = str(name)
                return name[:limit] + "..." if len(name) > limit else name
            
            df_dept['DisplayDept'] = df_dept[dept_col].apply(truncate_dept)
            
            # 2. Create Stacked Horizontal Bar Chart (Reuse df_dept)
            fig_dept = go.Figure()

            fig_dept.add_trace(go.Bar(
                y=df_dept['DisplayDept'],
                x=df_dept['Closed'],
                name='Closed',
                orientation='h',
                marker_color='#00526A',
                text=df_dept['Closed'],  # Count labels
                textposition='inside',
                textfont=dict(color='white'),
                hovertemplate="<b>%{y}</b><br>Closed: %{x}<extra></extra>"
            ))

            fig_dept.add_trace(go.Bar(
                y=df_dept['DisplayDept'],
                x=df_dept['Open'],
                name='Open',
                orientation='h',
                marker_color='#FF4B4B',
                text=df_dept['Open'],  # Count labels
                textposition='inside',
                textfont=dict(color='white'),
                hovertemplate="<b>%{y}</b><br>Open: %{x}<extra></extra>"
            ))

            # Annotations for compliance %
            for i, row in df_dept.iterrows():
                fig_dept.add_annotation(
                    x=row['Total'],
                    y=row['DisplayDept'],
                    text=f" <b>{row['Compliance%']}%</b>",
                    showarrow=False,
                    xanchor='left',
                    font=dict(size=11, color="#00526A")
                )
            
            if dept_view == "Scrollable":
                # Dynamic height based on number of departments
                unique_depts = df_dept[dept_col].nunique()
                dynamic_height = max(300, unique_depts * 40)
                
                # Get X range for consistent axis
                x_max = df_dept['Total'].max() * 1.2 if not df_dept.empty else 10
                
                # --- 1. Fixed Header (X-Axis) ---
                fig_header = go.Figure()
                fig_header.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(opacity=0)))
                fig_header.update_layout(
                    xaxis=dict(range=[0, x_max], side="top", color="#00526A", showgrid=False),
                    yaxis=dict(visible=False),
                    height=25,
                    margin=dict(l=180, r=60, t=25, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                st.plotly_chart(fig_header, use_container_width=True, config={'displayModeBar': False})
                
                # Legend outside scroll area (right aligned)
                st.markdown("""
                <div style='display:flex; justify-content:flex-end; gap:15px; margin-top:-10px; margin-bottom:5px; margin-right:10px; font-size:0.8rem;'>
                    <span><span style='display:inline-block;width:12px;height:12px;background:#00526A;margin-right:4px;'></span>Closed</span>
                    <span><span style='display:inline-block;width:12px;height:12px;background:#FF4B4B;margin-right:4px;'></span>Open</span>
                </div>
                """, unsafe_allow_html=True)
                
                # --- 2. Scrollable Body (Bars) ---
                fig_dept.update_layout(
                    barmode='stack',
                    bargap=0.3, 
                    title=None,
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    showlegend=False,  # Legend moved outside
                    yaxis=dict(title=None, color="#00526A", tickfont=dict(size=10)),
                    xaxis=dict(range=[0, x_max], visible=False),
                    height=dynamic_height, 
                    margin=dict(l=180, r=60, t=0, b=10)  # Reduced top margin
                )
                
                import streamlit.components.v1 as components
                chart_html = fig_dept.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
                components.html(chart_html, height=250, scrolling=True)
            else:
                # Fit to Screen - show all labels
                fig_dept.update_layout(
                    barmode='stack',
                    bargap=0.3, 
                    title=None,
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title=None, color="#00526A", tickfont=dict(size=9), automargin=True, dtick=1),
                    xaxis=dict(title="Count", color="#00526A", gridcolor='rgba(0,0,0,0.1)'),
                    height=350, 
                    margin=dict(l=180, r=60, t=30, b=10)
                )
                st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("Data departemen (team_role) tidak ditemukan.")
        
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # --- Row 2: Risk Category Matrix ---
        st.subheader("Matriks Kategori Temuan Departemen")
        st.caption("Rincian temuan berdasarkan departemen dan kategori risiko.")
        
        if 'team_role' in df_master_filtered.columns and 'temuan_kategori' in df_master_filtered.columns:
            # 1. Create the base matrix
            df_matrix = df_master_filtered.groupby(['team_role', 'temuan_kategori']).size().reset_index(name='Count')
            
            # Truncate long department names (max 30 chars)
            def truncate_role(name, limit=30):
                name = str(name)
                return name[:limit] + "..." if len(name) > limit else name
        
        df_matrix['DisplayRole'] = df_matrix['team_role'].apply(truncate_role)
        
        # 2. View Options
        c_view, _ = st.columns([1, 2])
        matrix_view = c_view.radio("Tampilan:", ["Scrollable", "Fit To Screen"], horizontal=True, label_visibility="collapsed", key="matrix_view_radio")
        
        # 3. Define Scale
        custom_scale = [
            [0.0, 'rgba(0,0,0,0)'],       
            [0.0001, '#96B3D2'],          
            [1.0, '#00526A']              
        ]
        
        fig_matrix = px.density_heatmap(
            df_matrix, 
            x='temuan_kategori', 
            y='DisplayRole',  # Use truncated names
            z='Count', 
            color_continuous_scale=custom_scale,
            text_auto=True  # Add count labels inside boxes
        )
        
        fig_matrix.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            margin=dict(t=30, l=200, r=10, b=30), # Increased left margin for labels
            font=dict(color="#00526A"),
            yaxis=dict(title=None),  # Remove y-axis title
            xaxis=dict(title=None)   # Remove x-axis title too for consistency
        )
        # Add gaps
        fig_matrix.update_traces(xgap=3, ygap=3, textfont=dict(color="white", size=12))

        if matrix_view == "Scrollable":
            # Get unique categories for X-axis header
            categories = df_matrix['temuan_kategori'].unique().tolist()
            
            # Split Layout: Scrollable Chart vs Fixed Legend
            c_scroll, c_fixed = st.columns([6, 1])
            
            with c_scroll:
                # Dynamic height calculation
                unique_roles = df_matrix['team_role'].nunique()
                dynamic_height = max(400, unique_roles * 40)
                
                # --- 1. Fixed Header (X-Axis Categories) ---
                fig_header = go.Figure()
                # Create dummy scatter for each category position
                for i, cat in enumerate(categories):
                    # Use HSE Color if available, else default blue
                    header_color = HSE_COLOR_MAP.get(cat, '#00526A')
                    
                    fig_header.add_trace(go.Scatter(
                        x=[i], y=[0], mode='text', text=[f"<b>{cat}</b>"], # Use HTML for bold
                        textposition='bottom center',
                        textfont=dict(color=header_color, size=11), # Removed invalid 'weight'
                        hoverinfo='none'
                    ))
                fig_header.update_layout(
                    xaxis=dict(range=[-0.5, len(categories)-0.5], visible=False),
                    yaxis=dict(visible=False),
                    height=35,
                    margin=dict(l=200, r=10, t=5, b=5),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                st.plotly_chart(fig_header, use_container_width=True, config={'displayModeBar': False})
                
                # Reduce gap
                st.markdown("<div style='margin-top:-20px;'></div>", unsafe_allow_html=True)
                
                # --- 2. Scrollable Body (Heatmap) ---
                # Hide legend on the main scrolling chart
                fig_matrix.update_traces(showscale=False)
                fig_matrix.update_layout(
                    height=dynamic_height,
                    yaxis=dict(autorange="reversed", automargin=True),
                    xaxis=dict(visible=False),  # Hide X-axis on scrollable body
                    margin=dict(l=200, r=10, t=10, b=10),
                    coloraxis_showscale=False
                )
                
                import streamlit.components.v1 as components
                html_code = fig_matrix.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
                components.html(html_code, height=250, scrolling=True)
            
            with c_fixed:
                # Fixed Legend (Dummy Plot)
                z_max = df_matrix['Count'].max() if not df_matrix.empty else 1
                
                fig_legend = go.Figure()
                fig_legend.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(
                        colorscale=custom_scale,
                        showscale=True,
                        cmin=0, cmax=z_max,
                        color=[0, z_max],
                        colorbar=dict(
                            title="Jumlah",
                            titleside="right",
                            thickness=15,
                            len=0.8,
                            titlefont=dict(color="#00526A", size=12),
                            tickfont=dict(color="#00526A", size=10)
                        )
                    ),
                    hoverinfo='none'
                ))
                fig_legend.update_layout(
                    xaxis=dict(visible=False), 
                    yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=450, 
                    margin=dict(t=20, b=20, l=0, r=40)
                )
                st.plotly_chart(fig_legend, use_container_width=True)
            
        else:
            # Fit to screen (default standard)
            fig_matrix.update_layout(yaxis=dict(automargin=True))
            st.plotly_chart(fig_matrix, use_container_width=True)
    # End of col_left (Dept Performance + Risk Category Matrix)

    with col_right:
        # --- Dept Radar Chart ---
        st.subheader("Budaya Pelaporan Departemen")
        st.caption("Radar 3-sumbu: Keaktifan, Upaya, RCI.")
        
        if not df_dept.empty and dept_col:
            all_depts = df_dept[dept_col].tolist()
            top_3_rci = df_dept.sort_values('RCI', ascending=False).head(3)[dept_col].tolist()
            selected_radar_depts = st.multiselect("Departemen:", all_depts, default=top_3_rci, key="radar_depts")
            
            if selected_radar_depts:
                df_radar = df_dept[df_dept[dept_col].isin(selected_radar_depts)]
                fig_radar = go.Figure()
                text_positions = ['top center', 'bottom center', 'middle left', 'middle right', 'top left', 'top right']
                
                for trace_idx, (index, row) in enumerate(df_radar.iterrows()):
                    categories = ['RCI', 'Faktor Upaya<br>(Jumlah Closing)', 'Poin Keaktifan<br>(Jumlah Temuan)']
                    values = [row['RCI'], row['Effort'], row['Activeness']]
                    categories = categories + [categories[0]]
                    values = values + [values[0]]
                    text_vals = [f"{row['RCI']:.1f}", f"{int(row['Effort'])}", f"{int(row['Activeness'])}", ""]
                    pos = text_positions[trace_idx % len(text_positions)]
                    
                    fig_radar.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill=None,
                        name=row[dept_col],
                        text=text_vals,
                        mode='lines+markers+text',
                        textposition=pos,
                        textfont=dict(size=12),
                        hovertemplate=f"<b>{row[dept_col]}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>"
                    ))
                
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, showline=False, gridcolor="rgba(0,0,0,0.1)"), bgcolor="rgba(0,0,0,0)"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                    height=600,
                    margin=dict(t=10, b=10, l=40, r=40)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Pilih departemen untuk melihat Radar.")
        else:
            st.info("Tidak ada data untuk diagram Radar.")

# =============================================
# TAB 2: PERSONNEL
# =============================================
with tab_personnel:
    st.subheader("Produktivitas Personil")
    st.caption("Analisis Beban Kerja: Total Laporan vs. Total Closed.")
    
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
        
        # Calculate Closed Count for Color
        df_perf['Closed Count'] = df_perf['Total Findings'] - df_perf['Open Count']
        
        hover_cols = ['Reporter']
        if 'Role' in df_perf.columns: hover_cols.append('Role')
        if 'Team Role' in df_perf.columns: hover_cols.append('Team Role')
        
        fig_scatter = px.scatter(df_perf, x='Total Findings', y='Closed Count', 
                                 hover_data=hover_cols,
                                 # text='Reporter', # Removed to prevent clutter
                                 size='Total Findings', 
                                 size_max=40, # Make bubbles slightly larger
                                 color='Closed Count',
                                 color_continuous_scale='Teal',
                                 title="<br><sup style='color:#00526A'>X: Total Laporan | Y: Total Closed | Warna: Jumlah Closed</sup>")
        
        # fig_scatter.update_traces(textposition='top center') # Removed
        fig_scatter.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
        
        # Add labels only for Top 10 busiest (by Total Findings)
        top_reporters = df_perf.nlargest(10, 'Total Findings')
        max_closed = df_perf['Closed Count'].max() if not df_perf.empty else 1
        
        for i, row in top_reporters.iterrows():
            # Truncate name to first word + "..."
            short_name = str(row['Reporter']).split()[0] + "..." if len(str(row['Reporter']).split()) > 1 else row['Reporter']
            
            # Dynamic label color: Light if high Closed Count (dark bubble), Dark if low
            intensity = row['Closed Count'] / max_closed if max_closed > 0 else 0
            label_color = "black" if intensity > 0.5 else "#00526A"
            
            fig_scatter.add_annotation(
                x=row['Total Findings'],
                y=row['Closed Count'],
                text=short_name,
                showarrow=False,
                yshift=10,
                font=dict(size=10, color=label_color),
                bgcolor="rgba(255,255,255,0.7)",  # Semi-transparent white background
                bordercolor="black",
                borderwidth=1,
                borderpad=2
            )
            
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#00526A"), title=dict(font=dict(color="#00526A")),
                                  xaxis=dict(color="#00526A"), yaxis=dict(color="#00526A"),
                                  margin=dict(l=0, r=0, t=30, b=10), height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Tidak ada data pelapor yang tersedia.")

    # --- E. Personnel Detail (inside tab_personnel) ---
    with st.container():
        st.subheader("Individual Detail")
    
    # --- Filters for Fast Finding (Compass Layout) ---
    roles_list = ["All"] + sorted(df_master_filtered['role'].dropna().unique().tolist()) if 'role' in df_master_filtered.columns else ["All"]
    teams_list = ["All"] + sorted(df_master_filtered['team_role'].dropna().unique().tolist()) if 'team_role' in df_master_filtered.columns else ["All"]
    
    col_f1, col_f2, col_f3 = st.columns(3) # 3 Column Layout
    
    sel_team = col_f1.selectbox("Filter by Department:", teams_list)

    sel_role = col_f2.selectbox("Filter by Role:", roles_list)

    
    # Filter Logic for selection list
    df_reporters = df_master_filtered.copy()

    if sel_team != "All":
        df_reporters = df_reporters[df_reporters['team_role'] == sel_team]
    if sel_role != "All":
        df_reporters = df_reporters[df_reporters['role'] == sel_role]
        
    reporters = sorted(df_reporters['creator_name'].dropna().unique()) if 'creator_name' in df_reporters.columns else []
    
    selected_reporter = col_f3.selectbox("Select Personnel", options=reporters)
    
    if selected_reporter:
        # Data reported by this person
        df_reported_by = df_master_filtered[df_master_filtered['creator_name'] == selected_reporter]
        
        # Data assigned to/closed by this person (using nama_pic)
        closed_by_count = 0
        if 'nama_pic' in df_master_filtered.columns:
            # We count cases where they are the PIC and the status is Closed
            df_closed_by = df_master_filtered[
                (df_master_filtered['nama_pic'] == selected_reporter) & 
                (df_master_filtered['temuan_status'].str.lower() == 'closed')
            ]
            closed_by_count = df_closed_by.shape[0]
        
        # 1. Header Info (Role & Team Role)
        role = df_reported_by['role'].iloc[0] if 'role' in df_reported_by.columns else "Unknown Role"
        team_role = df_reported_by['team_role'].iloc[0] if 'team_role' in df_reported_by.columns else "Unknown Team"
        
        # --- COMPACT HEADER ROW (Name + Stats) ---
        c_head, c_stats = st.columns([1.5, 1])
        
        with c_head:
            st.markdown(f"""
            <h3 style='margin-bottom:0;'>{selected_reporter}</h3>
            <div style='display:flex; gap: 15px; align-items: baseline;'>
                <div><b style='color:#00526A;'>{role}</b> <span style='font-size:0.8rem; color:grey;'>(role)</span></div>
                <div><b style='color:#00526A;'>{team_role}</b> <span style='font-size:0.8rem; color:grey;'>(team)</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_stats:
            # Inline Stats
            st.markdown(f"""
            <div style="display:flex; gap: 10px; justify-content: flex-end;">
                <div style="background: rgba(255,255,255,0.6); padding:5px 10px; border-radius:8px; border: 1px solid #CBECF5; text-align:center;">
                    <span style="font-size:0.7rem; color:grey;">Reports</span>
                    <h3 style="margin:0; color:#00526A; font-size:1.2rem;">{df_reported_by.shape[0]}</h3>
                </div>
                <div style="background: rgba(255,255,255,0.6); padding:5px 10px; border-radius:8px; border: 1px solid #CBECF5; text-align:center;">
                    <span style="font-size:0.7rem; color:grey;">Closed (PIC)</span>
                    <h3 style="margin:0; color:#00526A; font-size:1.2rem;">{closed_by_count}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---") # Divider
        
        # 2. Charts & Data (Side by Side)
        c_pie, c_table = st.columns([1, 2])
        
        with c_pie:
            if 'temuan_kategori' in df_reported_by.columns:
                risk_counts = df_reported_by['temuan_kategori'].value_counts().reset_index()
                risk_counts.columns = ['Category', 'Count']
                
                # Use Global Palette
                color_map = HSE_COLOR_MAP
                
                fig_pie = px.pie(risk_counts, values='Count', names='Category',
                                 color='Category', color_discrete_map=color_map, hole=0.5,
                                 title=None) # Title removed to save space
                
                fig_pie.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(t=0, b=0, l=0, r=0), height=200)
                                      
                fig_pie.update_traces(textposition='inside', textinfo='value+percent+label')
                
                st.markdown("**Temuan Kategori**")
                st.plotly_chart(fig_pie, use_container_width=True)
                
        with c_table:
            st.markdown("**Recent Reports**")
            st.dataframe(
                df_reported_by[['kode_temuan', 'tanggal', 'temuan_kategori', 'temuan_status']].head(5), 
                use_container_width=True,
                height=200, # Match Pie Chart
                hide_index=True
            )
        
        # 3. Location Map (Where did this person report findings?)
        st.markdown("---")
        st.markdown("**Report Locations**")
        
        # Check for lat/lon data
        has_lat = 'lat' in df_reported_by.columns
        has_lon = 'lon' in df_reported_by.columns
        
        if has_lat and has_lon:
            df_geo = df_reported_by.dropna(subset=['lat', 'lon'])
            
            if not df_geo.empty:
                
                import folium
                from folium.plugins import MarkerCluster
                
                # Fixed center (PLTU Sebalang location)
                center_lat = -5.585357333271365
                center_lon = 105.38785245329919
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
                
                # Stadia Satellite Layer
                folium.TileLayer(
                    tiles='https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg',
                    attr='&copy; Stadia Maps', name='Stadia Satellite'
                ).add_to(m)
                
                def get_color(category):
                    cat_lower = str(category).lower()
                    if 'near miss' in cat_lower: return 'darkblue'      # #1A237E
                    if 'unsafe condition' in cat_lower: return 'orange' # #F57F17
                    if 'unsafe action' in cat_lower: return 'red'       # #B71C1C -> red/darkred
                    if 'positive' in cat_lower: return 'darkgreen'      # #1B5E20
                    return 'cadetblue'
                
                for _, row in df_geo.iterrows():
                    kategori = row.get('temuan_kategori', '-')
                    location = row.get('nama_lokasi', '-')
                    status = row.get('temuan_status', 'Unknown')
                    
                    popup_html = f"""
                    <div style="font-family: sans-serif; color: #00526A; min-width: 150px;">
                        <b>{kategori}</b><hr style="margin: 3px 0;">
                        <b>Status:</b> {status}<br>
                        <b>Location:</b> {location}
                    </div>
                    """
                    
                    # Add marker directly to map (no clustering)
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=folium.Popup(popup_html, max_width=200),
                        icon=folium.Icon(color=get_color(kategori), icon='info-sign')
                    ).add_to(m)
                
                st_folium(m, width="100%", height=400, returned_objects=[])
            else:
                st.info("Tidak ada data lokasi untuk temuan pelapor ini.")
        else:
            st.info("Kolom lokasi (lat/lon) tidak ditemukan dalam data.")