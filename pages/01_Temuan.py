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
    
    # Create parent category from first word of temuan_nama_spesifik
    selected_parent = "Semua"
    
    if 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        # Extract first word as parent category
        df_exploded_filtered = df_exploded_filtered.copy()
        df_exploded_filtered['temuan_parent'] = df_exploded_filtered['temuan_nama_spesifik'].apply(
            lambda x: str(x).split()[0].lower().strip() if pd.notna(x) and str(x).strip() else None
        )
    
    # Col 1: Drill-down by Parent (first word)
    with c_drill:
        if 'temuan_parent' in df_exploded_filtered.columns:
            # Get unique parent categories (first words), exclude None/empty
            parents = df_exploded_filtered['temuan_parent'].dropna().unique()
            parents = [p for p in parents if p and p.strip()]
            parent_options = ["Semua"] + sorted(set(parents))
            selected_parent = st.selectbox("Filter per Nama Temuan:", parent_options)
            
    # Col 2: Limit
    with c_limit:
        limit_options = [10, 20, 50, "Semua"]
        max_items = st.selectbox("Tampilkan total Objek Teratas:", limit_options, index=1)

    # Col 3: Breakdown Checkbox (For Treemap)
    with c_check:
        st.write("") # Spacer for alignment
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        breakdown_cat = st.checkbox("Rincian per Temuan Kategori", value=False)
        
    if 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        # Filter data based on parent selection
        if selected_parent != "Semua":
            # Show all items where first word matches selected parent
            df_analysis = df_exploded_filtered[df_exploded_filtered['temuan_parent'] == selected_parent]
        else:
            df_analysis = df_exploded_filtered

        # --- CHART LAYOUT (Side-by-Side) ---
        col_pareto, col_treemap = st.columns(2)

            # --- 1. PARETO CHART (Left) ---
        with col_pareto:
            # Dynamic Column Selection:
            # - If "Semua" selected -> Analyze Parent Categories (first word)
            # - If "Specific Parent" selected -> Analyze full temuan_nama_spesifik within that parent
            
            if selected_parent == "Semua":
                # Show aggregated by parent (first word)
                col_analysis = 'temuan_parent'
                chart_title = "<b>Temuan Teratas</b>"
            else:
                # Show specific items within the selected parent
                col_analysis = 'temuan_nama_spesifik'
                chart_title = f"<b>Detail '{selected_parent.upper()}'</b><br><sup style='color:grey'>Semua temuan yang dimulai dengan '{selected_parent}'.</sup>"

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
                           name="Jumlah Temuan", marker_color='#00526A',
                           text=df_plot['Count'], textposition='outside'),
                    secondary_y=False
                )
                
                # Line Trace (Cumulative %)
                fig_pareto.add_trace(
                    go.Scatter(x=df_plot['Object'], y=df_plot['Cumulative Percentage'], 
                               name="Persentase Kumulatif Temuan %", mode='lines+markers', 
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
                    yaxis=dict(title="Jumlah Temuan", gridcolor='rgba(0,0,0,0.1)'), # Frequency -> Jumlah
                    yaxis2=dict(title="Persentase Kumulatif Temuan (%)", range=[0, 115], showgrid=False), # Cumulative %
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
            # Treemap Logic with Parent-Child Hierarchy
            if 'temuan_nama_spesifik' in df_analysis.columns and 'temuan_parent' in df_analysis.columns:
                
                if selected_parent == "Semua":
                    # Hierarchical view: Parent -> Child
                    target_cols = ['temuan_parent', 'temuan_nama_spesifik']
                    if breakdown_cat and 'temuan_kategori' in df_analysis.columns:
                        target_cols.append('temuan_kategori')
                    
                    path = [px.Constant("Semua Temuan")] + target_cols
                    df_obj_tree = df_analysis.groupby(target_cols).size().reset_index(name='Count')
                    
                    if max_items != "Semua":
                        # Limit by top parents
                        top_parents = df_obj_tree.groupby('temuan_parent')['Count'].sum().nlargest(max_items).index
                        df_obj_tree = df_obj_tree[df_obj_tree['temuan_parent'].isin(top_parents)]
                else:
                    # Show only children within selected parent
                    target_cols = ['temuan_nama_spesifik']
                    if breakdown_cat and 'temuan_kategori' in df_analysis.columns:
                        target_cols.append('temuan_kategori')
                    
                    path = [px.Constant(selected_parent.upper())] + target_cols
                    df_obj_tree = df_analysis.groupby(target_cols).size().reset_index(name='Count')
                    
                    if max_items != "Semua":
                        df_obj_tree = df_obj_tree.nlargest(max_items, 'Count')
            else:
                path = ['Object']
                df_obj_tree = df_analysis['temuan_nama_spesifik'].value_counts().reset_index()
                df_obj_tree.columns = ['Object', 'Count']
                if max_items != "Semua":
                    df_obj_tree = df_obj_tree.head(max_items)
            
            # Color Strategy
            if breakdown_cat:
                 color_params = dict(color='temuan_kategori', color_discrete_map=HSE_COLOR_MAP)
            else:
                 color_params = dict(color='Count', color_continuous_scale=custom_scale)

            # Dynamic title based on selection
            if selected_parent == "Semua":
                tree_title = "<b>Treemap Temuan</b>"
            else:
                tree_title = f"<b>Detail '{selected_parent.upper()}'</b><br><sup style='color:grey'>Semua temuan dalam kategori '{selected_parent}'.</sup>"
            
            fig_tree = px.treemap(
                df_obj_tree, 
                path=path, 
                values='Count', 
                **color_params,
                maxdepth=4 if breakdown_cat else 3, 
                title=tree_title
            )
            
            # Calculate dynamic text colors based on count values
            # Black text for low values (light background), White for high values (dark background)
            if not df_obj_tree.empty and 'Count' in df_obj_tree.columns:
                max_count = df_obj_tree['Count'].max()
                min_count = df_obj_tree['Count'].min()
                threshold = (max_count + min_count) / 2  # Midpoint as threshold
                
                # Create color array for each cell based on count
                # Note: Treemap creates hierarchical cells, so we use textfont with customdata
                fig_tree.update_traces(
                    root_color="white", 
                    marker_line_width=2,
                    marker_line_color="white",
                    textfont=dict(size=16),
                    texttemplate="<b>%{label}</b><br>%{value}",
                    hovertemplate="<b>%{label}</b><br>Temuan: %{value}<extra></extra>",
                    # Dynamic text color: dark for small values, light for large values
                    insidetextfont=dict(
                        color=["#000000" if v < threshold else "#FFFFFF" for v in df_obj_tree['Count']]
                    ) if len(df_obj_tree) > 0 else dict(color="white")
                )
            else:
                # Fallback styling
                fig_tree.update_traces(
                    root_color="white", 
                    marker_line_width=2,
                    marker_line_color="white",
                    textfont=dict(size=16, color="white"),
                    texttemplate="<b>%{label}</b><br>%{value}",
                    hovertemplate="<b>%{label}</b><br>Temuan: %{value}<extra></extra>"
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
    st.caption("Visualisasi kata yang paling sering muncul berdasarkan data temuan")
    
    # Static Wordcloud using Python wordcloud library
    def render_wordcloud_interactive(frequency_dict, color_scheme='blue', title=""):
        """
        Renders a static wordcloud using Python wordcloud library.
        Color schemes: 'blue', 'red', 'green', 'orange', 'purple'
        Reference: https://amueller.github.io/word_cloud/references.html
        """
        if not frequency_dict:
            st.info("Tidak ada data untuk wordcloud")
            return
        
        # Color schemes - using matplotlib colormaps
        colormap_mapping = {
            'blue': 'Blues',
            'red': 'Reds',
            'green': 'Greens',
            'orange': 'Oranges',
            'purple': 'Purples'
        }
        colormap = colormap_mapping.get(color_scheme, 'Blues')
        
        try:
            # Generate wordcloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color=None,
                mode='RGBA',
                colormap=colormap,
                relative_scaling=0.5,
                min_font_size=10,
                max_font_size=100,
                prefer_horizontal=0.7,
                font_path=None,  # Uses default font
                collocations=False,
                margin=10
            ).generate_from_frequencies(frequency_dict)
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            fig.patch.set_alpha(0)  # Transparent background
            ax.patch.set_alpha(0)
            plt.tight_layout(pad=0)
            
            # Display in Streamlit
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            
        except Exception as e:
            st.error(f"Error generating wordcloud: {e}")
            st.info("Data yang tersedia: " + ", ".join(list(frequency_dict.keys())[:5]) + "...")

    # --- Real Data from DataFrame ---
    # Kata Sifat (Conditions) from temuan_kondisi column
    kata_sifat_data = {}
    if 'temuan_kondisi' in df_exploded_filtered.columns:
        kondisi_series = df_exploded_filtered['temuan_kondisi'].dropna().astype(str)
        # Filter out 'None', 'nan', empty strings
        kondisi_series = kondisi_series[
            (kondisi_series.str.strip() != '') & 
            (kondisi_series.str.lower() != 'none') &
            (kondisi_series.str.lower() != 'nan')
        ]
        if len(kondisi_series) > 0:
            kata_sifat_data = kondisi_series.value_counts().head(20).to_dict()
    
    # Kata Benda (Objects) from temuan_nama_spesifik column
    kata_benda_data = {}
    if 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        nama_series = df_exploded_filtered['temuan_nama_spesifik'].dropna().astype(str)
        # Filter out 'None', 'nan', empty strings
        nama_series = nama_series[
            (nama_series.str.strip() != '') & 
            (nama_series.str.lower() != 'none') &
            (nama_series.str.lower() != 'nan')
        ]
        if len(nama_series) > 0:
            kata_benda_data = nama_series.value_counts().head(20).to_dict()
    
    # --- Layout ---
    wc_col1, wc_col2 = st.columns(2)
    
    with wc_col1:
        st.markdown("**Kondisi Temuan**")
        st.caption("Kondisi yang paling sering dilaporkan dalam temuan.")
        if kata_sifat_data and len(kata_sifat_data) > 0:
            st.write(f"📊 {len(kata_sifat_data)} kata unik ditemukan")
            render_wordcloud_interactive(kata_sifat_data, 'red')
        else:
            st.info("Tidak ada data kondisi temuan yang valid")
        
    with wc_col2:
        st.markdown("**Objek Temuan**")
        st.caption("Nama temuan yang paling sering ditemukan.")
        if kata_benda_data and len(kata_benda_data) > 0:
            # st.write(f"📊 {len(kata_benda_data)} objek unik ditemukan")
            render_wordcloud_interactive(kata_benda_data, 'blue')
        else:
            st.info("Tidak ada data objek temuan yang valid")

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
        # Flow: temuan_kategori -> temuan_nama_spesifik -> nama_lokasi
        
        has_parent = 'temuan_nama_spesifik' in df_exploded_filtered.columns
        cols = ['temuan_kategori', 'temuan_nama_spesifik', 'nama_lokasi'] if has_parent else ['temuan_kategori', 'temuan_nama_spesifik', 'nama_lokasi']
        cols = [c for c in cols if c in df_exploded_filtered.columns]
        
        # Limit Control
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Total Temuan", limit_options, index=0) # Default 10
        
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
                title=dict(text=f"<b>Analisis Alur Kategori Temuan</b><br><sup style='color:grey'>Melacak pergerakan temuan dari Kategori ke Objek ke Lokasi.</sup><br>", font=dict(color="#00526A")),
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
