import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from utils import load_data, render_sidebar, set_header_title, HSE_COLOR_MAP

# Page Config
st.set_page_config(page_title="Analisis Temuan", page_icon=None, layout="wide")

# Styling
# Loaded via utils.render_sidebar()

# Data Loading
df_exploded, df_master, _ = load_data()
df_master_filtered, df_exploded_filtered, _ = render_sidebar(df_master, df_exploded)
set_header_title("Analisis Temuan")



# --- Tabs for Compact Layout ---
tab1, tab2, tab3 = st.tabs(["Analisis Objek", "Analisis Kondisi", "Alur Kategori Temuan"])

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
    c_drill, c_limit, c_check = st.columns([1.5, 1, 1])
    
    # Col 1: Drill-down
    selected_parent = "Semua"
    with c_drill:
        if 'temuan.nama.parent' in df_exploded_filtered.columns:
            parent_options = ["Semua"] + sorted(df_exploded_filtered['temuan.nama.parent'].dropna().astype(str).unique())
            selected_parent = st.selectbox("Filter per Kategori (Parent):", parent_options)
            
    # Col 2: Limit
    with c_limit:
        limit_options = [10, 20, 50, "Semua"]
        max_items = st.selectbox("Tampilkan N Objek Teratas:", limit_options, index=1)

    # Col 3: Breakdown Checkbox (For Treemap)
    with c_check:
        st.write("") # Spacer for alignment
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        breakdown_cat = st.checkbox("Rincian per Kategori (Treemap)?", value=False)
        
    if 'temuan.nama' in df_exploded_filtered.columns:
        # Filter data based on selection (Shared for both charts)
        if selected_parent != "Semua":
            df_analysis = df_exploded_filtered[df_exploded_filtered['temuan.nama.parent'] == selected_parent]
        else:
            df_analysis = df_exploded_filtered

        # --- CHART LAYOUT (Side-by-Side) ---
        col_pareto, col_treemap = st.columns(2)

            # --- 1. PARETO CHART (Left) ---
        with col_pareto:
            # Dynamic Column Selection:
            # - If "All" selected -> Analyze Parent Categories (temuan.nama.parent)
            # - If "Specific Parent" selected -> Analyze Objects (temuan.nama)
            
            col_analysis = 'temuan.nama' # Default
            if selected_parent == "Semua" and 'temuan.nama.parent' in df_analysis.columns:
                col_analysis = 'temuan.nama.parent'
                chart_title = "<b>Kategori Isu Teratas</b><br><sup style='color:grey'>Mengidentifikasi jenis temuan yang menyebabkan mayoritas masalah (Prinsip 80/20).</sup>"
            else:
                col_analysis = 'temuan.nama'
                chart_title = f"<b>Objek Teratas dalam '{selected_parent}'</b><br><sup style='color:grey'>Fokus pada objek yang paling sering muncul dalam kategori ini.</sup>"

            df_obj_pareto = df_analysis[col_analysis].value_counts().reset_index()
            df_obj_pareto.columns = ['Object', 'Count']
            
            if not df_obj_pareto.empty:
                df_obj_pareto['Cumulative Percentage'] = df_obj_pareto['Count'].cumsum() / df_obj_pareto['Count'].sum() * 100
                
                # Apply Limit
                if max_items != "Semua":
                    df_plot = df_obj_pareto.head(max_items)
                else:
                    df_plot = df_obj_pareto
                
                from plotly.subplots import make_subplots
                import plotly.graph_objects as go
                
                fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Bar Trace (Count)
                fig_pareto.add_trace(
                    go.Bar(x=df_plot['Object'], y=df_plot['Count'], 
                           name="Frequency", marker_color='#00526A',
                           text=df_plot['Count'], textposition='outside'),
                    secondary_y=False
                )
                
                # Line Trace (Cumulative %)
                fig_pareto.add_trace(
                    go.Scatter(x=df_plot['Object'], y=df_plot['Cumulative Percentage'], 
                               name="Cumulative %", mode='lines+markers', 
                               line=dict(color='#FF4B4B')),
                    secondary_y=True
                )
                
                # Annotations for Line Trace (to ensure readability on top of bars)
                annotations = []
                for index, row in df_plot.iterrows():
                    # Stagger labels to prevent overlap
                    # Even indices: standard height
                    # Odd indices: shifted higher
                    y_offset = 10 if index % 2 == 0 else 30
                    
                    annotations.append(dict(
                        x=row['Object'], 
                        y=row['Cumulative Percentage'],
                        text=f"{row['Cumulative Percentage']:.1f}%",
                        showarrow=False,
                        yshift=y_offset,
                        font=dict(color='#FF4B4B', size=9), # Slightly smaller font
                        bgcolor="rgba(255,255,255,0.9)", # More opaque background
                        bordercolor="#FF4B4B",
                        borderwidth=1,
                        borderpad=2
                    ))

                fig_pareto.update_layout(
                    title=dict(text=chart_title, font=dict(color="#00526A")),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#00526A"),
                    yaxis=dict(title="Jumlah", gridcolor='rgba(0,0,0,0.1)'), # Frequency -> Jumlah
                    yaxis2=dict(title="Persentase Kumulatif (%)", range=[0, 115], showgrid=False), # Cumulative %
                    height=500,
                    margin=dict(t=80, l=10, r=10, b=10) # Increased top margin for title
                )
                
                # Add annotations to the secondary y-axis context if needed, 
                # but standard layout annotations work on the plot area. 
                # We need to map yref to 'y2' for the line values.
                for ann in annotations:
                    ann['xref'] = 'x'
                    ann['yref'] = 'y2'
                    fig_pareto.add_annotation(ann)
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.info("Tidak ada data untuk Analisis Pareto.")

        # --- 2. TREEMAP CHART (Right) ---
        with col_treemap:
            # Treemap Logic
            if 'temuan.nama.parent' in df_analysis.columns:
                target_cols = ['temuan.nama.parent', 'temuan.nama']
                if breakdown_cat and 'temuan_kategori' in df_analysis.columns:
                     target_cols.append('temuan_kategori')
                
                path = [px.Constant("Semua Kategori")] + target_cols
                df_obj_tree = df_analysis.groupby(target_cols).size().reset_index(name='Count')
                
                if max_items != "Semua":
                   top_parents = df_obj_tree.groupby('temuan.nama.parent')['Count'].sum().nlargest(max_items).index
                   df_obj_tree = df_obj_tree[df_obj_tree['temuan.nama.parent'].isin(top_parents)]
            else:
                path = ['Object']
                df_obj_tree = df_analysis['temuan.nama'].value_counts().reset_index()
                df_obj_tree.columns = ['Object', 'Count']
                if max_items != "Semua":
                    df_obj_tree = df_obj_tree.head(max_items)
            
            # Color Strategy
            if breakdown_cat:
                 color_params = dict(color='temuan_kategori', color_discrete_map=HSE_COLOR_MAP)
            else:
                 color_params = dict(color='Count', color_continuous_scale=custom_scale)

            fig_tree = px.treemap(
                df_obj_tree, 
                path=path, 
                values='Count', 
                **color_params,
                maxdepth=3 if breakdown_cat else 2, 
                title="<b>Hirarki Objek</b><br><sup style='color:grey'>Visualisasi proporsi volume temuan. Blok lebih besar = Lebih banyak temuan.</sup>"
            )
            
            # Styling
            fig_tree.update_traces(
                root_color="white", 
                marker_line_width=2,
                marker_line_color="white",
                textfont=dict(size=18, color="white"),
                texttemplate="<b>%{label}</b><br>%{value}",
                hovertemplate="<b>%{label}</b><br>Findings: %{value}<extra></extra>"
            )

            fig_tree.update_layout(
                height=500, 
                margin=dict(t=80, l=10, r=10, b=10), # Aligned with Pareto
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False # Clean look
            )
            
            st.plotly_chart(fig_tree, use_container_width=True)

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
            st.error(f"Gagal membuat wordcloud: {e}")
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
        # st.markdown("##### Kata Sifat (Adjectives)")
        fig_sifat = render_wordcloud_interactive(kata_sifat_data, 'Reds')
        
        # Add Title & Description (Consistent with Tab 1)
        fig_sifat.update_layout(
            title="<b>Kata Sifat (Adjectives)</b><br><sup style='color:grey'>Kata deskriptif yang paling sering muncul yang menunjukkan sifat temuan.</sup>",
            margin=dict(t=80, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_sifat, use_container_width=True)
        
    with wc_col2:
        # st.markdown("##### Kata Benda (Nouns)")
        fig_benda = render_wordcloud_interactive(kata_benda_data, 'Blues')
        
        # Add Title & Description
        fig_benda.update_layout(
             title="<b>Kata Benda (Nouns)</b><br><sup style='color:grey'>Objek atau komponen umum yang disebutkan dalam temuan.</sup>",
             margin=dict(t=80, l=10, r=10, b=10)
        )
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
        max_items = st.selectbox("Batasi Alur/Node (N Teratas):", limit_options, index=0) # Default 10
        
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
            # Colors matching Global HSE Palette
            color_map = HSE_COLOR_MAP.copy()
            color_map['Safe'] = HSE_COLOR_MAP['Positive']
            color_map['Others'] = '#B0BEC5' # Grey for "Others"
            
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
            
            # Helper: Map Parent -> Category for flow coloring
            # df_sankey is already filtered. We can map each unique Parent to its dominant Category.
            parent_to_cat_map = {}
            if len(cols) > 1:
                # Group by Parent (cols[1]), take most frequent Category (cols[0])
                try:
                    p_to_c = df_sankey.groupby(cols[1])[cols[0]].agg(lambda x: x.mode()[0])
                    parent_to_cat_map = p_to_c.to_dict()
                except Exception:
                    pass

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
                    
                    # Determine Link Color based on Origin Category
                    src_label = row[src_col]
                    origin_cat = src_label
                    
                    # If source is a Parent node (Middle layer), look up its Category
                    if src_col == cols[1]:
                        origin_cat = parent_to_cat_map.get(src_label, src_label)
                    
                    if origin_cat in color_map:
                        base_color = color_map[origin_cat]
                    elif origin_cat == 'Others':
                        base_color = color_map['Others']
                    else:
                        base_color = default_node_color
                    
                    link_colors.append(hex_to_rgba(base_color, 0.4))
            
            # Calculate Node Totals for Labels
            node_values = {i: 0 for i in range(len(unique_labels))}
            # Sum max flow for each node to represent throughput
            # Since In == Out (mostly), we can sum incoming links for targets and outgoing for sources?
            # Actually, standard Sankey logic: Value = max(total_in, total_out)
            node_in = {i: 0 for i in range(len(unique_labels))}
            node_out = {i: 0 for i in range(len(unique_labels))}
            
            for s, t, v in zip(source, target, value):
                node_out[s] += v
                node_in[t] += v
                
            formatted_labels = []
            for i, label in enumerate(unique_labels):
                val = max(node_in[i], node_out[i])
                formatted_labels.append(f"<b>{label}</b>: {val}")

            # 4. Render
            fig_sankey = go.Figure(data=[go.Sankey(
                textfont = dict(color="#00526A", size=12, family="Source Sans Pro"),
                node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "white", width = 0.5),
                label = formatted_labels, # Labels with counts
                color = node_colors 
                ),
                link = dict(
                source = source,
                target = target,
                value = value,
                color = link_colors
                )
            )])
            
            flow_desc = " → ".join([c.replace('temuan.', '').replace('_', ' ').title() for c in cols])
            
            fig_sankey.update_layout(
                title=dict(text=f"<b>Analisis Alur Kategori Temuan</b><br><sup style='color:grey'>Melacak pergerakan temuan dari Kategori ke Objek ke Lokasi.</sup><br><sup style='color:#00526A'>Alur: {flow_desc}</sup>", font=dict(color="#00526A")),
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#00526A"),
                height=700
            )
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.warning("Kolom data tidak cukup untuk alur Sankey.")
    else:
        st.info("Tidak ada data tersedia.")

st.markdown("<br>", unsafe_allow_html=True)
