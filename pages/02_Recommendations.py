import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data, render_sidebar

# Page Config
st.set_page_config(page_title="Recommendations - HSE", page_icon=None, layout="wide")

# Styling
# Loaded via utils.render_sidebar()

# Data Loading
df_exploded, df_master, _ = load_data()
df_master_filtered, df_exploded_filtered = render_sidebar(df_master, df_exploded)

st.title("Recommendations & SLA")

# --- A. Risk-to-Location Flow (Sankey) ---
with st.container():
    st.subheader("Risk Flow Analysis (Category → Object → Place)")

    if not df_exploded_filtered.empty:
        # --- Prepare Nodes & Links for Sankey ---
        # Flow: temuan_kategori -> temuan.nama.parent -> nama_lokasi
        
        has_parent = 'temuan.nama.parent' in df_exploded_filtered.columns
        cols = ['temuan_kategori', 'temuan.nama.parent', 'nama_lokasi'] if has_parent else ['temuan_kategori', 'temuan.nama', 'nama_lokasi']
        cols = [c for c in cols if c in df_exploded_filtered.columns]
        
        # Limit Control
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Limit Flows/Nodes (Top N):", limit_options, index=1) # Default 20
        
        if len(cols) >= 2:
            df_sankey = df_exploded_filtered[cols].dropna().copy()
            
            # --- CLUTTER REDUCTION: Group "Small" Nodes to "Others" ---
            if max_items != "All":
                # 1. Limit Parents (Middle Node)
                if len(cols) > 1:
                    parent_col = cols[1]
                    top_parents = df_sankey[parent_col].value_counts().head(max_items).index
                    df_sankey = df_sankey[df_sankey[parent_col].isin(top_parents)]
                
                # 2. Limit Locations (Target Node) - Grouping logic
                if len(cols) > 2:
                    loc_col = cols[2]
                    top_locs = df_sankey[loc_col].value_counts().head(max_items).index
                    # Replace non-top locations with "Others"
                    df_sankey[loc_col] = df_sankey[loc_col].apply(lambda x: x if x in top_locs else 'Others')

            # 2. Assign unique index to all distinct labels
            unique_labels = []
            for c in cols:
                unique_labels.extend(df_sankey[c].unique().tolist())
            unique_labels = list(set(unique_labels))
            label_map = {label: i for i, label in enumerate(unique_labels)}
            
            # --- COLOR MAPPING ---
            # Colors matching Homepage Risk Distribution
            color_map = {
                'Near Miss': '#FF4B4B',        # Red
                'Unsafe Condition': '#FFAA00', # Orange
                'Unsafe Action': '#E67E22',    # Dark Orange
                'Positive': '#00526A',         # PLN Blue
                'Safe': '#00526A',
                'Others': '#B0BEC5'            # Grey for "Others"
            }
            # Default color for objects/places
            default_node_color = "#00526A"
            
            node_colors = []
            for label in unique_labels:
                # Check if label matches known categories
                if label in color_map:
                    node_colors.append(color_map[label])
                elif label == 'Others':
                    node_colors.append(color_map['Others'])
                else:
                    node_colors.append(default_node_color)

            # Helper for transparency
            def hex_to_rgba(hex_color, opacity=0.4):
                hex_color = hex_color.lstrip('#')
                if len(hex_color) == 6:
                    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    return f"rgba({r}, {g}, {b}, {opacity})"
                return f"rgba(0, 82, 106, {opacity})"

            # 3. Build Links
            source = []
            target = []
            value = []
            link_colors = []
            
            for i in range(len(cols) - 1):
                src_col = cols[i]
                tgt_col = cols[i+1]
                link_df = df_sankey.groupby([src_col, tgt_col]).size().reset_index(name='Count')
                link_df = link_df.sort_values('Count', ascending=False)
                
                for _, row in link_df.iterrows():
                    src_idx = label_map[row[src_col]]
                    tgt_idx = label_map[row[tgt_col]]
                    source.append(src_idx)
                    target.append(tgt_idx)
                    value.append(row['Count'])
                    
                    # Determine Link Color based on Source Node
                    src_label = row[src_col]
                    if src_label in color_map:
                        base_color = color_map[src_label]
                    elif src_label == 'Others':
                        base_color = color_map['Others']
                    else:
                        base_color = default_node_color
                    
                    link_colors.append(hex_to_rgba(base_color, 0.4))
            
            # 4. Render
            fig_sankey = go.Figure(data=[go.Sankey(
                textfont = dict(color="#00526A", size=12, family="Source Sans Pro"),
                node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "white", width = 0.5),
                label = unique_labels,
                color = node_colors # Applied dynamic colors
                ),
                link = dict(
                source = source,
                target = target,
                value = value,
                color = link_colors # Dynamic Link Colors
            ))])
            
            flow_desc = " → ".join([c.replace('temuan.', '').replace('_', ' ').title() for c in cols])
            
            fig_sankey.update_layout(
                title=dict(text=f"<b>Risk Flow Analysis</b><br><sup style='color:#00526A'>Flow: {flow_desc}</sup>", font=dict(color="#00526A")),
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#00526A"),
                height=700
            )
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.warning("Not enough data columns available for Sankey flow.")
    else:
        st.info("No data available.")

# --- B. Execution KPIs ---
st.subheader("Execution Performance")

# KPI Calculation
pending_high_risk = df_master_filtered[
    (df_master_filtered['temuan_kategori'] == 'Near Miss') & 
    (df_master_filtered['temuan_status'] == 'Open')
].shape[0]

overdue_count = 0
if 'deadline_sla' in df_master_filtered.columns:
    overdue_mask = (df_master_filtered['temuan_status'] == 'Open') & (pd.to_datetime('today') > df_master_filtered['deadline_sla'])
    overdue_count = df_master_filtered[overdue_mask].shape[0]

avg_aging = 0
if 'tanggal' in df_master_filtered.columns:
    open_items = df_master_filtered[df_master_filtered['temuan_status'] == 'Open'].copy()
    if not open_items.empty:
        open_items['age'] = (pd.to_datetime('today') - open_items['tanggal']).dt.days
        avg_aging = int(open_items['age'].mean())

# Render KPIs using HTML Cards (White Background)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Pending High-Risk</h3>
        <h2 style="color: #FF4B4B;">{pending_high_risk}</h2>
        <p style="color:grey; font-size:0.8rem;">Open 'Near Miss' findings</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Overdue Findings</h3>
        <h2>{overdue_count}</h2>
        <p style="color:grey; font-size:0.8rem;">Open items past SLA</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Avg. Aging</h3>
        <h2>{avg_aging} Days</h2>
        <p style="color:grey; font-size:0.8rem;">For Open findings</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- C. High Risk Priority Table---
with st.container():
    st.subheader("High-Risk Priority Actions")
    high_risk_df = df_master_filtered[df_master_filtered['temuan_kategori'] == 'Near Miss']

    if not high_risk_df.empty:
        st.dataframe(
            high_risk_df[['tanggal', 'temuan.nama', 'temuan.kondisi.lemma', 'nama_lokasi', 'deadline_sla', 'temuan_status']].head(20),
            use_container_width=True
        )
    else:
        st.success("No 'Near Miss' findings found in this filter selection.")

# --- D. SLA per Department ---
with st.container():
    st.subheader("Department Performance")
    
    dept_col = 'team_role' if 'team_role' in df_master_filtered.columns else None
    
    if dept_col:
        # 1. Calculate detailed breakdown
        df_dept = df_master_filtered.groupby(dept_col).agg(
            Total=('kode_temuan', 'nunique'),
            Closed=('temuan_status', lambda x: (x.str.lower() == 'closed').sum())
        ).reset_index()
        
        df_dept['Open'] = df_dept['Total'] - df_dept['Closed']
        df_dept['Compliance%'] = (df_dept['Closed'] / df_dept['Total'] * 100).round(1)
        
        # Sort so highest volume is at the top
        df_dept = df_dept.sort_values('Total', ascending=True)

        # 2. Create Stacked Horizontal Bar Chart
        fig_dept = go.Figure()

        fig_dept.add_trace(go.Bar(
            y=df_dept[dept_col],
            x=df_dept['Closed'],
            name='Closed',
            orientation='h',
            marker_color='#00526A',
            # Adjust bar thickness via width (optional, bargap is usually better)
            hovertemplate="<b>%{y}</b><br>Closed: %{x}<extra></extra>"
        ))

        fig_dept.add_trace(go.Bar(
            y=df_dept[dept_col],
            x=df_dept['Open'],
            name='Open',
            orientation='h',
            marker_color='#FF4B4B',
            hovertemplate="<b>%{y}</b><br>Open: %{x}<extra></extra>"
        ))

        # 3. Layout Styling: Control Gaps and Height
        fig_dept.update_layout(
            barmode='stack',
            # bargap: defines the space between bars (0 to 1). 
            # 0.4 or 0.5 creates a clear separation to prevent clumping.
            bargap=0.5, 
            title="<b>Department Performance Breakdown</b><br><sup style='color:#00526A'>Total Volume vs. Completion Status</sup>",
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#00526A"),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title=None, color="#00526A", tickfont=dict(size=12)),
            xaxis=dict(title="Number of Findings", color="#00526A", gridcolor='rgba(0,0,0,0.1)'),
            # Increased height to give the thicker bars enough room
            height=650, 
            margin=dict(l=10, r=80, t=100, b=10) # Added right margin for labels
        )

        # 4. Annotations with descriptive labels
        for i, row in df_dept.iterrows():
            fig_dept.add_annotation(
                x=row['Total'],
                y=row[dept_col],
                # Explicit label: "XX% Closed"
                text=f" <b>{row['Compliance%']}% Closed</b>",
                showarrow=False,
                xanchor='left',
                font=dict(size=11, color="#00526A")
            )
        
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("Department data (team_role) not found.")