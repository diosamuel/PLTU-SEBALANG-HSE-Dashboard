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
df_master_filtered, df_exploded_filtered, _ = render_sidebar(df_master, df_exploded)

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

# --- B. Condition Wordcloud (Split: Adjectives & Nouns) ---
with st.container():
    st.subheader("Condition Wordcloud")
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

# --- C. Risk Category Matrix ---
with st.container():
    st.subheader("Risk Category Matrix (Role vs Category)")
    
    if 'team_role' in df_master_filtered.columns and 'temuan_kategori' in df_master_filtered.columns:
        # 1. Create the base matrix
        df_matrix = df_master_filtered.groupby(['team_role', 'temuan_kategori']).size().reset_index(name='Count')
        
        # 2. View Options
        c_view, _ = st.columns([1, 2])
        matrix_view = c_view.radio("View Layout:", ["Scrollable", "Fit to Screen"], horizontal=True, label_visibility="collapsed")
        
        # 3. Define Scale
        custom_scale = [
            [0.0, 'rgba(0,0,0,0)'],       
            [0.0001, '#96B3D2'],          
            [1.0, '#00526A']              
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
            margin=dict(t=30, l=150, r=10, b=30), # Increased left margin for labels
            font=dict(color="#00526A")
        )
        # Add gaps
        fig_matrix.update_traces(xgap=3, ygap=3)

        if matrix_view == "Scrollable":
            # Split Layout: Scrollable Chart vs Fixed Legend
            c_scroll, c_fixed = st.columns([6, 1])
            
            with c_scroll:
                # Dynamic height calculation
                unique_roles = df_matrix['team_role'].nunique()
                # 40px per row, min 400px
                dynamic_height = max(400, unique_roles * 40)
                
                # Hide legend on the main scrolling chart
                fig_matrix.update_traces(showscale=False)
                fig_matrix.update_layout(
                    height=dynamic_height,
                    yaxis=dict(autorange="reversed", automargin=True),
                    margin=dict(r=10), # Reduce right margin since legend is gone
                    coloraxis_showscale=False # Explicitly hide colorbar if managed by coloraxis
                )
                
                import streamlit.components.v1 as components
                html_code = fig_matrix.to_html(include_plotlyjs='cdn', full_html=False)
                components.html(html_code, height=450, scrolling=True)
            
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
                            title="Count",
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
# --- D. Finding Details Table ---
with st.container():
    st.subheader("Finding Details")
    
    cols_to_show = ['tanggal', 'temuan_kategori', 'temuan.nama', 'temuan.kondisi.lemma', 'temuan.tempat', 'temuan_status']
    cols_to_show = [c for c in cols_to_show if c in df_exploded_filtered.columns]
    
    # Render dataframe directly to follow standard Streamlit appearance
    st.dataframe(df_exploded_filtered[cols_to_show], use_container_width=True)