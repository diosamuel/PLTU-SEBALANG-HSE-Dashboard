import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from utils import load_data, render_sidebar

# Page Config
st.set_page_config(page_title="Findings Analysis - HSE", page_icon=None, layout="wide")

# Styling
# Loaded via utils.render_sidebar()

# Data Loading
df_exploded, df_master, _ = load_data()
df_master_filtered, df_exploded_filtered = render_sidebar(df_master, df_exploded)

st.title("Findings Analysis")

# --- A. Object Analysis (Pareto/Treemap) ---
with st.container():
    st.subheader("Object Analysis")

    # Consistent color gradient (matches your Risk Matrix)
    custom_scale = [
        [0.0, 'rgba(0,0,0,0)'],       
        [0.0001, '#96B3D2'],          
        [1.0, '#00526A']              
    ]

    # Drill-down Filter
    selected_parent = "All"
    if 'temuan.nama.parent' in df_exploded_filtered.columns:
        parent_options = ["All"] + sorted(df_exploded_filtered['temuan.nama.parent'].dropna().astype(str).unique())
        selected_parent = st.selectbox("Drill-down by Category (Parent):", parent_options)

    viz_type = st.radio("Visualization Type:", ["Treemap", "Pareto Chart"], horizontal=True)

    if 'temuan.nama' in df_exploded_filtered.columns:
        # Filter data based on selection
        if selected_parent != "All":
            df_analysis = df_exploded_filtered[df_exploded_filtered['temuan.nama.parent'] == selected_parent]
        else:
            df_analysis = df_exploded_filtered

        # Limit Control
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Show Top N Objects:", limit_options, index=1)
        
        if viz_type == "Treemap":
            if 'temuan.nama.parent' in df_analysis.columns:
                path = [px.Constant("All Categories"), 'temuan.nama.parent', 'temuan.nama']
                df_obj = df_analysis.groupby(['temuan.nama.parent', 'temuan.nama']).size().reset_index(name='Count')
                
                if max_items != "All":
                   top_parents = df_obj.groupby('temuan.nama.parent')['Count'].sum().nlargest(max_items).index
                   df_obj = df_obj[df_obj['temuan.nama.parent'].isin(top_parents)]
            else:
                path = ['Object']
                df_obj = df_analysis['temuan.nama'].value_counts().reset_index()
                df_obj.columns = ['Object', 'Count']
                if max_items != "All":
                    df_obj = df_obj.head(max_items)
            
            fig = px.treemap(
                df_obj, 
                path=path, 
                values='Count', 
                color='Count',
                color_continuous_scale=custom_scale,
                maxdepth=2, 
                title="<b>Object Hierarchy</b><br><sup style='color:grey'>Showing Parent Categories. Click a box to see specific objects.</sup>"
            )
            
            # --- UPDATED: Font Size and White Color ---
            fig.update_traces(
                root_color="white", 
                marker_line_width=2,
                marker_line_color="white",
                # textfont controls the label appearance
                textfont=dict(
                    size=18,        # Increased font size
                    color="white"   # Force all text to white
                ),
                texttemplate="<b>%{label}</b><br>Count: %{value}",
                hovertemplate="<b>%{label}</b><br>Findings: %{value}<extra></extra>"
            )

            fig.update_layout(
                height=500, 
                margin=dict(t=70, l=10, r=10, b=10), 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)"
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

# --- B. Condition Wordcloud ---
with st.container():
    st.subheader("Condition Wordcloud")
    st.caption("Visualizing most frequent words in `temuan.kondisi.lemma`")
    
    # Limit Control
    wc_limit_options = [50, 100, 200]
    max_wc_words = st.selectbox("Max Words:", wc_limit_options, index=1) # Default 100

    if 'temuan.kondisi.lemma' in df_exploded_filtered.columns:
        text_data = " ".join(df_exploded_filtered['temuan.kondisi.lemma'].dropna().astype(str).tolist())
        
        if text_data.strip():
            try:
                # 1. Aesthetics: Stopwords & Layout
                stopwords = set([
                    'dan', 'di', 'yang', 'dengan', 'ada', 'tidak', 'pada', 'untuk', 'ke', 'dari', 
                    'ini', 'itu', 'atau', 'dapat', 'sudah', 'juga', 'karena', 'oleh', 'namun', 
                    'sebagai', 'serta', 'bisa', 'akan', 'return', 'temu', 'tindak', 'lanjut', 
                    'kondisi', 'temuan', 'area', 'lokasi', 'tempat' # Context-specific generic words
                ])
                
                # 2. Calculate Layout using WordCloud library
                stopwords.update(["undefined", "nan", "null", "-", "_"]) # Safety against bad data strings
                
                # prefer_horizontal=0.9 makes it mostly horizontal (neater). 
                # scale=2 gives higher resolution for collision detection.
                wc = WordCloud(width=800, height=450, background_color=None, mode="RGBA",
                              max_words=max_wc_words, stopwords=stopwords,
                              prefer_horizontal=0.9, relative_scaling=0.5,
                              min_font_size=10, max_font_size=100
                              ).generate(text_data)
                
                # 3. Extract coordinates and words
                word_list = []
                freq_list = []
                fontsize_list = []
                
                # Calculate raw counts for tooltip
                from collections import Counter
                words_clean = [w for w in text_data.split() if w.lower() not in stopwords]
                word_counts = Counter(words_clean)
                
                position_x_list = []
                position_y_list = []
                
                # Color Mapping Logic (Frequency Based)
                import matplotlib.colors as mcolors
                import matplotlib.cm as cm
                
                # Prepare data for coloring
                colors_mapped = []
                
                # First pass: collect valid items
                items_processed = []
                for item in wc.layout_:
                    if len(item) < 3: continue # Safety
                    
                    # Handle varying unpacking depending on version
                    if len(item) == 5:
                        (word, fontsize, position, orientation, color) = item
                    elif len(item) == 6:
                        (word, _, fontsize, position, orientation, color) = item
                    else: continue

                    if isinstance(word, tuple): word = word[0]
                    word = str(word).strip("('),")
                    
                    if position is None: continue
                    
                    count = word_counts.get(word, 0)
                    items_processed.append({
                        'word': word,
                        'count': count,
                        'fontsize': fontsize,
                        'x': position[1],
                        'y': 450 - position[0]
                    })
                
                if items_processed:
                    # Normalization for coloring
                    counts = [x['count'] for x in items_processed]
                    max_c = max(counts) if counts else 1
                    min_c = min(counts) if counts else 0
                    norm = mcolors.Normalize(vmin=min_c, vmax=max_c)
                    cmap = cm.get_cmap('Blues') # Use Blues colormap
                    
                    # Generate lists for Plotly
                    word_list = [x['word'] for x in items_processed]
                    freq_list = [x['count'] for x in items_processed]
                    fontsize_list = [x['fontsize'] for x in items_processed]
                    position_x_list = [x['x'] for x in items_processed]
                    position_y_list = [x['y'] for x in items_processed]
                    
                    # Map colors (Skip very light start of Blues to ensure visibility)
                    # We map 0.3 to 1.0 of the Blues scale
                    color_list = [mcolors.to_hex(cmap(0.4 + (norm(c) * 0.6))) for c in freq_list]

                    # 3. Create Plotly Scatter
                    fig_wc = go.Figure()
                    
                    # Main Text Trace
                    fig_wc.add_trace(go.Scatter(
                        x=position_x_list,
                        y=position_y_list,
                        text=word_list,
                        mode='text',
                        textfont=dict(
                            size=fontsize_list,
                            family="Source Sans Pro, sans-serif",
                            color=color_list
                        ),
                        hoverinfo='text',
                        hovertext=[f"Word: {w}<br>Count: {f}" for w, f in zip(word_list, freq_list)],
                        showlegend=False
                    ))
                    
                    # Dummy Trace for Colorbar Legend
                    fig_wc.add_trace(go.Scatter(
                        x=[None], y=[None],
                        mode='markers',
                        marker=dict(
                            colorscale='Blues', 
                            showscale=True,
                            cmin=min_c, cmax=max_c,
                            color=[min_c, max_c], # Dummy data range
                            colorbar=dict(
                                title="Frequency",
                                titlefont=dict(color="#00526A"),
                                tickfont=dict(color="#00526A"),
                                len=0.8
                            )
                        ),
                        hoverinfo='none',
                        showlegend=False
                    ))
                    
                    fig_wc.update_layout(
                        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        height=500,
                        font=dict(color="#00526A"), 
                        title_text="", 
                        margin=dict(t=20, b=20, l=20, r=20)
                    ) 
                    
                    st.plotly_chart(fig_wc, use_container_width=True)
                else:
                     st.info("No valid words generated.")
                
            except Exception as e:
                st.warning(f"Could not generate interactive wordcloud: {e}")
        else:
            st.info("No text data available for Wordcloud.")

# --- C. Risk Category Matrix ---
with st.container():
    st.subheader("Risk Category Matrix (Role vs Category)")
    
    if 'team_role' in df_master_filtered.columns and 'temuan_kategori' in df_master_filtered.columns:
        # 1. Create the base matrix
        df_matrix = df_master_filtered.groupby(['team_role', 'temuan_kategori']).size().reset_index(name='Count')
        
        # 2. Define a scale where the absolute bottom (0) is transparent.
        # We start the visible color at a very small offset (0.0001) 
        # so that only true zeros/empty cells are hidden.
        custom_scale = [
            [0.0, 'rgba(0,0,0,0)'],       # Fully Transparent for zero
            [0.0001, '#96B3D2'],          # Start visible blue immediately after zero
            [1.0, '#00526A']              # Dark blue for the maximum count
        ]
        
        fig_matrix = px.density_heatmap(
            df_matrix, 
            x='temuan_kategori', 
            y='team_role', 
            z='Count', 
            color_continuous_scale=custom_scale
        )
        
        fig_matrix.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            margin=dict(t=10, l=10, r=10, b=10),
            font=dict(color="#00526A")
        )
        
        # 3. Add gaps to clearly define the cells that DO have data
        fig_matrix.update_traces(xgap=3, ygap=3)
        
        st.plotly_chart(fig_matrix, use_container_width=True)
# --- D. Finding Details Table ---
with st.container():
    st.subheader("Finding Details")
    
    cols_to_show = ['tanggal', 'temuan_kategori', 'temuan.nama', 'temuan.kondisi.lemma', 'temuan.tempat', 'temuan_status']
    cols_to_show = [c for c in cols_to_show if c in df_exploded_filtered.columns]
    
    # Render dataframe directly to follow standard Streamlit appearance
    st.dataframe(df_exploded_filtered[cols_to_show], use_container_width=True)