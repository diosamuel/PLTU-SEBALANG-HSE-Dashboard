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
# --- A. Object Analysis (Pareto/Treemap) ---
with st.container(border=True):
    st.subheader("Object Analysis")

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

        # --- Limit Control ---
        limit_options = [10, 20, 50, "All"]
        max_items = st.selectbox("Show Top N Objects:", limit_options, index=1) # Default 20
        
        if viz_type == "Treemap":
            # Check if parent column exists for hierarchy
            if 'temuan.nama.parent' in df_analysis.columns:
                path = ['temuan.nama.parent', 'temuan.nama']
                df_grouped = df_analysis.groupby(path).size().reset_index(name='Count')
                
                # Apply Limit: Filter by top N occuring parents to keep hierarchy clean
                if max_items != "All":
                   top_parents = df_grouped.groupby('temuan.nama.parent')['Count'].sum().nlargest(max_items).index
                   df_obj = df_grouped[df_grouped['temuan.nama.parent'].isin(top_parents)]
                else:
                   df_obj = df_grouped
            else:
                path = ['Object'] # MATCHES df_obj.columns definition below
                df_obj = df_analysis['temuan.nama'].value_counts().reset_index()
                df_obj.columns = ['Object', 'Count']
                if max_items != "All":
                    df_obj = df_obj.head(max_items)
            
            fig = px.treemap(df_obj, path=path, values='Count', color='Count',
                             color_continuous_scale='Blues',
                             title="<b>Object Hierarchy</b><br><sup style='color:grey'>Size represents frequency. Click to zoom (if interactive).</sup>")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        
        else: # Pareto
            # Pareto is usually on the "Leaf" node (temuan.nama)
            df_obj = df_analysis['temuan.nama'].value_counts().reset_index()
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
                    title=f"<b>Top Issues in '{selected_parent}'</b><br><sup style='color:grey'>Pareto Analysis of 'temuan.nama'</sup>",
                    showlegend=True,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(title="Frequency", gridcolor='rgba(0,0,0,0.1)'),
                    yaxis2=dict(title="Cumulative %", range=[0, 110], showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data for Pareto chart.")

# --- B. Condition Wordcloud ---
# --- B. Condition Wordcloud ---
with st.container(border=True):
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
                # Filter words for counting too
                words_clean = [w for w in text_data.split() if w.lower() not in stopwords]
                word_counts = Counter(words_clean)
                
                position_x_list = []
                position_y_list = []
                
                # Colors: Assign random blues/teals for variety but consistency
                import random
                colors_pool = ['#00526A', '#007EA7', '#00A8CC', '#003344'] 
                color_list = []
                
                # wc.layout_ contains: (word, font_size, position, orientation, color)
                for item in wc.layout_:
                    freq_ignore = 0
                    if len(item) == 5:
                        (word, fontsize, position, orientation, color) = item
                    elif len(item) == 6: # Just in case some versions differ and include frequency
                        (word, freq_ignore, fontsize, position, orientation, color) = item
                    else: 
                         continue
                    
                    # CORRECTION: Sometimes word is returned as (word, score) tuple by WordCloud
                    if isinstance(word, tuple):
                        word = word[0]
                    
                    # Clean punctuation just in case
                    word = str(word).strip("('),")

                    if position is None:
                        continue
                        
                    word_list.append(word)
                    freq_list.append(word_counts.get(word, '?')) # Show Real Count
                    fontsize_list.append(fontsize)
                    position_x_list.append(position[1]) # x
                    position_y_list.append(450 - position[0]) # y (invert because image origin is top-left)
                    color_list.append(random.choice(colors_pool))
                
                # 3. Create Plotly Scatter
                fig_wc = go.Figure()
                
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
                    hovertext=[f"Word: {w}<br>Count: {f}" for w, f in zip(word_list, freq_list)]
                ))
                
                fig_wc.update_layout(
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=500
                ) 
                
                st.plotly_chart(fig_wc, use_container_width=True)
                
            except Exception as e:
                st.warning(f"Could not generate interactive wordcloud: {e}")
        else:
            st.info("No text data available for Wordcloud.")

# --- C. Risk Category Matrix ---
with st.container(border=True):
    st.subheader("Risk Category Matrix (Role vs Category)")
    if 'team_role' in df_master_filtered.columns and 'temuan_kategori' in df_master_filtered.columns:
        df_matrix = df_master_filtered.groupby(['team_role', 'temuan_kategori']).size().reset_index(name='Count')
        
        fig_matrix = px.density_heatmap(df_matrix, x='temuan_kategori', y='team_role', z='Count', 
                                        color_continuous_scale='Blues',
                                        title="<b>Risk Matrix</b><br><sup style='color:grey'>Heatmap of 'team_role' (Reporter) vs 'temuan_kategori'</sup>")
        fig_matrix.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font=dict(color='#00526A'))
        st.plotly_chart(fig_matrix, use_container_width=True)

# --- D. Finding Details Table ---
with st.container(border=True):
    st.subheader("Finding Details")
    cols_to_show = ['tanggal', 'temuan_kategori', 'temuan.nama', 'temuan.kondisi.lemma', 'temuan.tempat', 'temuan_status']
    # Filter columns that actually exist
    cols_to_show = [c for c in cols_to_show if c in df_exploded_filtered.columns]
    
    st.dataframe(df_exploded_filtered[cols_to_show], use_container_width=True)
