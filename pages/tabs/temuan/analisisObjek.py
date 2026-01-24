import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from constants import CUSTOM_SCALE, HSE_COLOR_MAP


def analisisObjek(df_exploded_filtered: pd.DataFrame) -> None:
    """Render tab 'Analisis Objek' (Pareto + Treemap) for the given dataframe."""
    selected_parent = "Semua"
    if df_exploded_filtered is None or df_exploded_filtered.empty:
        st.info("Tidak ada data tersedia.")
        return

    if 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        df_exploded_filtered = df_exploded_filtered.copy()
        df_exploded_filtered['temuan_parent'] = df_exploded_filtered['temuan_nama_spesifik'].apply(
            lambda x: str(x).split()[0].lower().strip() if pd.notna(x) and str(x).strip() else None
        )
    
    c_drill, c_limit, c_check = st.columns([1.5, 1, 1])
    with c_drill:
        if 'temuan_parent' in df_exploded_filtered.columns:
            # Get unique parent categories (first words), exclude None/empty
            parents = df_exploded_filtered['temuan_parent'].dropna().unique()
            parents = [p for p in parents if p and p.strip()]
            parent_options = ["Semua"] + sorted(set(parents))
            selected_parent = st.selectbox("Filter per Nama Temuan:", parent_options)
    with c_limit:
        limit_options = [10, 20, 50, "Semua"]
        max_items = st.selectbox("Tampilkan total Objek Teratas:", limit_options, index=1)
    with c_check:
        st.write("") # Spacer for alignment
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        breakdown_cat = st.checkbox("Rincian per Temuan Kategori", value=False)
        
    if 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        # Filter data based on parent selection
        if selected_parent != "Semua":
            df_analysis = df_exploded_filtered[df_exploded_filtered['temuan_parent'] == selected_parent]
        else:
            df_analysis = df_exploded_filtered
        col_pareto, col_treemap = st.columns(2)
        with col_pareto:
            if selected_parent == "Semua":
                col_analysis = 'temuan_parent'
                chart_title = "<b>Temuan Teratas</b>"
            else:
                col_analysis = 'temuan_nama_spesifik'
                chart_title = f"<b>Detail '{selected_parent.upper()}'</b><br><sup style='color:grey'>Semua temuan yang dimulai dengan '{selected_parent}'.</sup>"
            df_obj_pareto = df_analysis[col_analysis].value_counts().reset_index()
            df_obj_pareto.columns = ['Object', 'Count']
            
            if not df_obj_pareto.empty:
                df_obj_pareto['Cumulative Percentage'] = df_obj_pareto['Count'].cumsum() / df_obj_pareto['Count'].sum() * 100
                if max_items != "Semua":
                    df_plot = df_obj_pareto.head(max_items)
                else:
                    df_plot = df_obj_pareto
                fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                fig_pareto.add_trace(
                    go.Bar(x=df_plot['Object'], y=df_plot['Count'], 
                           name="Jumlah Temuan", marker_color='#00526A',
                           text=df_plot['Count'], textposition='outside'),
                    secondary_y=False
                )
                fig_pareto.add_trace(
                    go.Scatter(x=df_plot['Object'], y=df_plot['Cumulative Percentage'], 
                               name="Persentase Kumulatif Temuan %", mode='lines+markers', 
                               line=dict(color='#FF4B4B')),
                    secondary_y=True
                )
                annotations = []
                for index, row in df_plot.iterrows():
                    y_offset = 10 if index % 2 == 0 else 30
                    annotations.append(dict(
                        x=row['Object'], 
                        y=row['Cumulative Percentage'],
                        text=f"{row['Cumulative Percentage']:.1f}%",
                        showarrow=False,
                        yshift=y_offset,
                        font=dict(color='#FF4B4B', size=9),
                        bgcolor="rgba(255,255,255,0.9)",
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
                    yaxis=dict(title="Jumlah Temuan", gridcolor='rgba(0,0,0,0.1)'),
                    yaxis2=dict(title="Persentase Kumulatif Temuan (%)", range=[0, 115], showgrid=False),
                    height=500,
                    margin=dict(t=80, l=10, r=10, b=10)
                )
                for ann in annotations:
                    ann['xref'] = 'x'
                    ann['yref'] = 'y2'
                    fig_pareto.add_annotation(ann)
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.info("Tidak ada data untuk Analisis Pareto.")
        with col_treemap:
            if 'temuan_nama_spesifik' in df_analysis.columns and 'temuan_parent' in df_analysis.columns:
                if selected_parent == "Semua":
                    target_cols = ['temuan_parent', 'temuan_nama_spesifik']
                    if breakdown_cat and 'temuan_kategori' in df_analysis.columns:
                        target_cols.append('temuan_kategori')
                    path = [px.Constant("Semua Temuan")] + target_cols
                    df_obj_tree = df_analysis.groupby(target_cols).size().reset_index(name='Count')
                    
                    if max_items != "Semua":
                        top_parents = df_obj_tree.groupby('temuan_parent')['Count'].sum().nlargest(max_items).index
                        df_obj_tree = df_obj_tree[df_obj_tree['temuan_parent'].isin(top_parents)]
                else:
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
            if breakdown_cat:
                 color_params = dict(color='temuan_kategori', color_discrete_map=HSE_COLOR_MAP)
            else:
                 color_params = dict(color='Count', color_continuous_scale=CUSTOM_SCALE)
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
            if not df_obj_tree.empty and 'Count' in df_obj_tree.columns:
                max_count = df_obj_tree['Count'].max()
                min_count = df_obj_tree['Count'].min()
                threshold = (max_count + min_count) / 2
                
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
                margin=dict(t=80, l=10, r=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("Kolom 'temuan_nama_spesifik' tidak ditemukan.")