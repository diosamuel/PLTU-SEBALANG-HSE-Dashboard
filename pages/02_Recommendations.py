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
df_master_filtered, df_exploded_filtered, _ = render_sidebar(df_master, df_exploded)

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

# --- B. Execution Performance (Split View) ---
st.subheader("Near Miss Alert")

# KPI Calculation
pending_high_risk = df_master_filtered[
    (df_master_filtered['temuan_kategori'] == 'Near Miss') & 
    (df_master_filtered['temuan_status'] == 'Open')
].shape[0]

# Layout: KPI Card (Left) vs Priority Table (Right)
c_kpi, c_table = st.columns([1, 3])

with c_kpi:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Pending Near Miss</h3>
        <h2 style="color: #FF4B4B;">{pending_high_risk}</h2>
        <p style="color:grey; font-size:0.8rem;">Open 'Near Miss' findings</p>
    </div>
    """, unsafe_allow_html=True)

with c_table:
    st.markdown("##### Near Miss Findings")
    high_risk_df = df_master_filtered[df_master_filtered['temuan_kategori'] == 'Near Miss']

    if not high_risk_df.empty:
        # Columns: kode_temuan as first column, removed deadline_sla
        cols_to_show = ['kode_temuan', 'tanggal', 'temuan.nama', 'temuan.kondisi.lemma', 'nama_lokasi', 'temuan_status']
        # Filter valid columns
        valid_cols = [c for c in cols_to_show if c in high_risk_df.columns]
        
        st.dataframe(
            high_risk_df[valid_cols].head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No 'Near Miss' findings found in this filter selection.")

st.markdown("<br><br>", unsafe_allow_html=True)