import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from utils import load_data, render_sidebar, set_header_title

# Page Config
st.set_page_config(page_title="Findings Analysis", page_icon=None, layout="wide")

# Styling
# Loaded via utils.render_sidebar()

# Data Loading
df_exploded, df_master, _ = load_data()
df_master_filtered, df_exploded_filtered, _ = render_sidebar(df_master, df_exploded)
set_header_title("Findings Analysis")



# --- Tabs for Compact Layout ---
tab1, tab2, tab3 = st.tabs(["Object Analysis", "Condition Wordcloud", "Risk Flow"])

# --- A. Object Analysis (Pareto/Treemap) ---
with tab1:
    # st.subheader("Object Analysis") # Removed for compactness

    # Consistent color gradient (matches your Risk Matrix)
    # Consistent color gradient (matches your Risk Matrix and Homepage theme)
    # Using explicit hex for consistent Blue gradient
    custom_scale = [
        [0.0, '#DCEEF3'],  # Light Blue (instead of transparent)     
        [1.0, '#00526A']   # PLN Dark Blue           
    ]

    # --- COMPACT CONTROLS ROW ---
    c_drill, c_viz, c_check, c_limit = st.columns([1.5, 1.2, 1, 1])
    
    # Col 1: Drill-down
    selected_parent = "All"
    with c_drill:
        if 'temuan.nama.parent' in df_exploded_filtered.columns:
            parent_options = ["All"] + sorted(df_exploded_filtered['temuan.nama.parent'].dropna().astype(str).unique())
            selected_parent = st.selectbox("Drill-down by Category (Parent):", parent_options)
            
    # Col 2: Viz Type
    with c_viz:
         viz_type = st.radio("Visualization Type:", ["Treemap", "Pareto Chart"], horizontal=True)

    # Col 3: Breakdown Checkbox (Only for Treemap)
    with c_check:
        st.write("") # Spacer for alignment
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        breakdown_cat = st.checkbox("Breakdown by Category?", value=False) if viz_type == "Treemap" else False
        
    # Col 4: Limit
    with c_limit:
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Show Top N Objects:", limit_options, index=1)

    if 'temuan.nama' in df_exploded_filtered.columns:
        # Filter data based on selection
        if selected_parent != "All":
            df_analysis = df_exploded_filtered[df_exploded_filtered['temuan.nama.parent'] == selected_parent]
        else:
            df_analysis = df_exploded_filtered

        if viz_type == "Treemap":
            if 'temuan.nama.parent' in df_analysis.columns:
                target_cols = ['temuan.nama.parent', 'temuan.nama']
                if breakdown_cat and 'temuan_kategori' in df_analysis.columns:
                     target_cols.append('temuan_kategori')
                
                path = [px.Constant("All Categories")] + target_cols
                df_obj = df_analysis.groupby(target_cols).size().reset_index(name='Count')
                
                if max_items != "All":
                   top_parents = df_obj.groupby('temuan.nama.parent')['Count'].sum().nlargest(max_items).index
                   df_obj = df_obj[df_obj['temuan.nama.parent'].isin(top_parents)]
            else:
                path = ['Object']
                df_obj = df_analysis['temuan.nama'].value_counts().reset_index()
                df_obj.columns = ['Object', 'Count']
                if max_items != "All":
                    df_obj = df_obj.head(max_items)
            
            # --- MODIFIED: Unified Color Strategy ---
            # Both views now use the Blue Gradient ('custom_scale') based on 'Count'
            color_params = dict(color='Count', color_continuous_scale=custom_scale)

            fig = px.treemap(
                df_obj, 
                path=path, 
                values='Count', 
                **color_params,
                # Depth 3 shows the extra category layer, Depth 2 stays at Object level
                maxdepth=3 if breakdown_cat else 2, 
                title="<b>Object Hierarchy</b><br><sup style='color:grey'>Showing Parent Categories. Click a box to see specific objects.</sup>"
            )
            
            # --- KEEPING LABELS (Important) ---
            fig.update_traces(
                root_color="white", 
                marker_line_width=2,
                marker_line_color="white",
                textfont=dict(
                    size=18,        # Large labels
                    color="white"   # White text for contrast
                ),
                texttemplate="<b>%{label}</b><br>Count: %{value}",
                hovertemplate="<b>%{label}</b><br>Findings: %{value}<extra></extra>"
            )

            fig.update_layout(
                height=500, 
                margin=dict(t=70, l=10, r=10, b=10), 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=True # Shows the gradient legend
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else: # Pareto
            # Dynamic Column Selection:
            # - If "All" selected -> Analyze Parent Categories (temuan.nama.parent)
            # - If "Specific Parent" selected -> Analyze Objects (temuan.nama)
            
            col_analysis = 'temuan.nama' # Default
            if selected_parent == "All" and 'temuan.nama.parent' in df_analysis.columns:
                col_analysis = 'temuan.nama.parent'
                chart_title = "<b>Top Issue Categories</b><br><sup style='color:grey'>Pareto Analysis of 'temuan.nama.parent'</sup>"
            else:
                col_analysis = 'temuan.nama'
                chart_title = f"<b>Top Objects in '{selected_parent}'</b><br><sup style='color:grey'>Pareto Analysis of 'temuan.nama'</sup>"

            df_obj = df_analysis[col_analysis].value_counts().reset_index()
            df_obj.columns = ['Object', 'Count']
            
            if not df_obj.empty:
                df_obj['Cumulative Percentage'] = df_obj['Count'].cumsum() / df_obj['Count'].sum() * 100
                
                # Apply Limit for display (Pareto usually shows Top N anyway, but now user controls it)
                if max_items != "All":
                    df_plot = df_obj.head(max_items)
                else:
                    df_plot = df_obj
                
                from plotly.subplots import make_subplots
                import plotly.graph_objects as go
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Bar Trace (Count)
                fig.add_trace(
                    go.Bar(x=df_plot['Object'], y=df_plot['Count'], 
                           name="Frequency", marker_color='#00526A'),
                    secondary_y=False
                )
                
                # Line Trace (Cumulative %)
                fig.add_trace(
                    go.Scatter(x=df_plot['Object'], y=df_plot['Cumulative Percentage'], 
                               name="Cumulative %", mode='lines+markers', line=dict(color='#FF4B4B')),
                    secondary_y=True
                )
                
                fig.update_layout(
                    title=dict(text=chart_title, font=dict(color="#00526A")),
                    showlegend=True,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    yaxis=dict(title="Frequency", gridcolor='rgba(0,0,0,0.1)'),
                    yaxis2=dict(title="Cumulative %", range=[0, 110], showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data for Pareto chart.")

# --- B. Condition Wordcloud (Split: Adjectives & Nouns) ---
with tab2:
    # st.subheader("Condition Wordcloud")
    st.caption("Visualizing most frequent words (Dummy Data: Adjectives vs Nouns)")
    
    # Text Processing & Plotting Function (Reusable - Interactive & Compact)
    def render_wordcloud_interactive(frequency_dict, color_cmap='Blues', title=""):
        try:
            # Generate Layout with compact settings
            # We use a larger canvas to ensure high resolution positioning, 
            # then map it to the plotly coordinates.
            wc = WordCloud(width=600, height=400, background_color=None, mode="RGBA",
                          prefer_horizontal=1.0, # All Horizontal for compactness
                          relative_scaling=0.5,
                          margin=2, 
                          min_font_size=10, max_font_size=80, # Adjusted for Plotly scaling
                          colormap=color_cmap 
                          ).generate_from_frequencies(frequency_dict)
            
            # Extract coordinates for Plotly
            word_list = []
            freq_list = []
            fontsize_list = []
            position_x_list = []
            position_y_list = []
            colors_list = []
            
            import matplotlib.colors as mcolors
            import matplotlib.cm as cm
            
            # Re-generate colors to match the cmap strictly
            counts = list(frequency_dict.values())
            if not counts: return go.Figure()
            max_c = max(counts)
            min_c = min(counts)
            norm = mcolors.Normalize(vmin=min_c, vmax=max_c)
            cmap = cm.get_cmap(color_cmap)

            for item in wc.layout_:
                if len(item) < 3: continue
                # Unpack varying tuple lengths
                if len(item) == 5:
                    (word, fontsize, position, orientation, color) = item
                elif len(item) == 6:
                    (word, _, fontsize, position, orientation, color) = item
                else: continue
                
                if isinstance(word, tuple): word = word[0]
                word = str(word).strip("('),")
                
                if position is None: continue
                
                freq = frequency_dict.get(word, 0)
                
                # Append data
                word_list.append(word)
                freq_list.append(freq)
                fontsize_list.append(fontsize) # Plotly matches this reasonably well
                position_x_list.append(position[1])
                position_y_list.append(400 - position[0]) # Flip Y-axis
                
                # Manually map color to ensure consistency with cmap
                colors_list.append(mcolors.to_hex(cmap(0.4 + (norm(freq) * 0.6))))

            # Plotly Scatter
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=position_x_list, y=position_y_list,
                text=word_list,
                mode='text',
                textfont=dict(size=fontsize_list, family="Source Sans Pro, sans-serif", color=colors_list),
                hoverinfo='text',
                hovertext=[f"{w}: {f}" for w, f in zip(word_list, freq_list)]
            ))

            # Add Colorbar Legend
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(
                    colorscale=color_cmap, 
                    showscale=True,
                    cmin=min_c, cmax=max_c,
                    color=[min_c, max_c],
                    colorbar=dict(
                        title="Frequency",
                        titleside="right",
                        thickness=15,
                        len=0.7,
                        titlefont=dict(color="#00526A", size=12),
                        tickfont=dict(color="#00526A", size=10)
                    )
                ),
                hoverinfo='none',
                showlegend=False
            ))
            
            fig.update_layout(
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 600]),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 400]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                height=400,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            return fig

        except Exception as e:
            st.error(f"Error generating wordcloud: {e}")
            return go.Figure()

    # --- Dummy Data ---
    kata_sifat_data = {
        'Rusak': 120, 'Bocor': 90, 'Putus': 85, 'Kotor': 70, 
        'Retak': 65, 'Panas': 60, 'Licin': 55, 'Longgar': 50,
        'Korosif': 45, 'Hilang': 40, 'Miring': 35, 'Aus': 30,
        'Terbuka': 25, 'Pecah': 20, 'Tersumbat': 15
    }
    
    kata_benda_data = {
        'Kabel': 150, 'Pipa': 110, 'Valve': 95, 'Trafo': 80,
        'Motor': 75, 'Pompa': 70, 'Panel': 65, 'Tangga': 60,
        'Lampu': 55, 'Sensor': 50, 'Baut': 45, 'Oli': 40,
        'Helm': 35, 'Sepatu': 30, 'Sarung Tangan': 25
    }
    
    # --- Layout ---
    wc_col1, wc_col2 = st.columns(2)
    
    with wc_col1:
        st.markdown("##### Kata Sifat (Adjectives)")
        fig_sifat = render_wordcloud_interactive(kata_sifat_data, 'Reds')
        st.plotly_chart(fig_sifat, use_container_width=True)
        
    with wc_col2:
        st.markdown("##### Kata Benda (Nouns)")
        fig_benda = render_wordcloud_interactive(kata_benda_data, 'Blues')
        st.plotly_chart(fig_benda, use_container_width=True)

# --- OLD WORDCLOUD CODE FROZEN BELOW ---
# """
#     if 'temuan.kondisi.lemma' in df_exploded_filtered.columns:
#         text_data = " ".join(df_exploded_filtered['temuan.kondisi.lemma'].dropna().astype(str).tolist())
#         ... (Original Logic Frozen) ...
# """

# --- C. Risk Category Matrix (MOVED TO PERSONNEL PAGE) ---
# Code removed and transferred to 04_Personnel.py

with tab3:
    # st.subheader("Risk Flow Analysis (Category → Object → Place)")

    if not df_exploded_filtered.empty:
        # --- Prepare Nodes & Links for Sankey ---
        # Flow: temuan_kategori -> temuan.nama.parent -> nama_lokasi
        
        has_parent = 'temuan.nama.parent' in df_exploded_filtered.columns
        cols = ['temuan_kategori', 'temuan.nama.parent', 'nama_lokasi'] if has_parent else ['temuan_kategori', 'temuan.nama', 'nama_lokasi']
        cols = [c for c in cols if c in df_exploded_filtered.columns]
        
        # Limit Control
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Limit Flows/Nodes (Top N):", limit_options, index=0) # Default 10
        
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
                )
            )])
            
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

st.markdown("<br>", unsafe_allow_html=True)
