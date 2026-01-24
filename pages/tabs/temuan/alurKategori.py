import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from constants import HSE_COLOR_MAP
from utils import hex_to_rgba


def alurKategori(df_exploded_filtered: pd.DataFrame) -> None:
    """Render tab 'Alur Kategori Temuan' (Sankey: Kategori → Objek → Lokasi)."""
    if df_exploded_filtered is None or df_exploded_filtered.empty:
        st.info("Tidak ada data tersedia.")
        return

    cols = ['temuan_kategori', 'temuan_nama_spesifik', 'nama_lokasi']
    cols = [c for c in cols if c in df_exploded_filtered.columns]

    limit_options = [10, 20, 50, "All"]
    max_items = st.selectbox("Total Temuan", limit_options, index=0, key="sankey_limit")

    if len(cols) < 2:
        st.warning("Kolom data tidak cukup untuk alur Sankey.")
        return

    df_sankey = df_exploded_filtered[cols].dropna().copy()

    if max_items != "All":
        if len(cols) > 1:
            parent_col = cols[1]
            top_parents = df_sankey[parent_col].value_counts().head(max_items).index
            df_sankey = df_sankey[df_sankey[parent_col].isin(top_parents)]

        if len(cols) > 2:
            loc_col = cols[2]
            top_locs = df_sankey[loc_col].value_counts().head(max_items).index
            df_sankey[loc_col] = df_sankey[loc_col].apply(lambda x: x if x in top_locs else 'Others')

    unique_labels: list[str] = []
    for c in cols:
        unique_labels.extend(df_sankey[c].unique().tolist())
    unique_labels = list(set(unique_labels))
    label_map = {label: i for i, label in enumerate(unique_labels)}

    color_map = HSE_COLOR_MAP.copy()
    color_map['Safe'] = HSE_COLOR_MAP['Positive']
    color_map['Others'] = '#B0BEC5'
    default_node_color = "#00526A"

    node_colors = []
    for label in unique_labels:
        if label in color_map:
            node_colors.append(color_map[label])
        else:
            node_colors.append(default_node_color)

    source: list[int] = []
    target: list[int] = []
    value: list[int] = []
    link_colors: list[str] = []

    parent_to_cat_map = {}
    if len(cols) > 1:
        try:
            p_to_c = df_sankey.groupby(cols[1])[cols[0]].agg(lambda x: x.mode()[0])
            parent_to_cat_map = p_to_c.to_dict()
        except Exception:
            parent_to_cat_map = {}

    for i in range(len(cols) - 1):
        src_col = cols[i]
        tgt_col = cols[i + 1]
        link_df = df_sankey.groupby([src_col, tgt_col]).size().reset_index(name='Count')
        link_df = link_df.sort_values('Count', ascending=False)

        for _, row in link_df.iterrows():
            src_idx = label_map[row[src_col]]
            tgt_idx = label_map[row[tgt_col]]
            source.append(src_idx)
            target.append(tgt_idx)
            value.append(int(row['Count']))

            src_label = row[src_col]
            origin_cat = src_label
            if src_col == cols[1]:
                origin_cat = parent_to_cat_map.get(src_label, src_label)

            if origin_cat in color_map:
                base_color = color_map[origin_cat]
            elif origin_cat == 'Others':
                base_color = color_map['Others']
            else:
                base_color = default_node_color

            link_colors.append(hex_to_rgba(base_color, 0.4))

    node_in = {i: 0 for i in range(len(unique_labels))}
    node_out = {i: 0 for i in range(len(unique_labels))}

    for s, t, v in zip(source, target, value):
        node_out[s] += v
        node_in[t] += v

    formatted_labels = []
    for i, label in enumerate(unique_labels):
        val = max(node_in[i], node_out[i])
        formatted_labels.append(f"<b>{label}</b>: {val}")

    fig_sankey = go.Figure(data=[go.Sankey(
        textfont=dict(color="#00526A", size=12, family="Source Sans Pro"),
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="white", width=0.5),
            label=formatted_labels,
            color=node_colors,
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
        ),
    )])

    fig_sankey.update_layout(
        title=dict(
            text="<b>Analisis Alur Kategori Temuan</b><br><sup style='color:grey'>Melacak pergerakan temuan dari Kategori ke Objek ke Lokasi.</sup>",
            font=dict(color="#00526A"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#00526A"),
        height=700,
    )
    st.plotly_chart(fig_sankey, use_container_width=True)
