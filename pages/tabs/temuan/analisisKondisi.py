import pandas as pd
import streamlit as st

from utils import render_wordcloud


def analisisKondisi(df_exploded_filtered: pd.DataFrame) -> None:
    """Render tab 'Analisis Kondisi' (wordcloud kondisi + objek)."""
    st.caption("Visualisasi kata yang paling sering muncul berdasarkan data temuan")

    word_limit = st.selectbox(
        "Tampilkan Jumlah Kata:", [10, 20, 30, 50], index=1, key="wordcloud_limit"
    )

    kata_sifat_data: dict[str, int] = {}
    if df_exploded_filtered is not None and 'temuan_kondisi' in df_exploded_filtered.columns:
        kondisi_series = df_exploded_filtered['temuan_kondisi'].dropna().astype(str)
        if len(kondisi_series) > 0:
            kata_sifat_data = kondisi_series.value_counts().head(word_limit).to_dict()

    kata_benda_data: dict[str, int] = {}
    if df_exploded_filtered is not None and 'temuan_nama_spesifik' in df_exploded_filtered.columns:
        nama_series = df_exploded_filtered['temuan_nama_spesifik'].dropna().astype(str)
        if len(nama_series) > 0:
            kata_benda_data = nama_series.value_counts().head(word_limit).to_dict()

    wc_col1, wc_col2 = st.columns(2)

    with wc_col1:
        st.markdown("**Kondisi Temuan**")
        st.caption("Kondisi yang paling sering dilaporkan dalam temuan.")
        if kata_sifat_data:
            st.caption(f"{len(kata_sifat_data)} kata unik")
            render_wordcloud(kata_sifat_data, 'red')
        else:
            st.info("Tidak ada data kondisi temuan yang valid")

    with wc_col2:
        st.markdown("**Objek Temuan**")
        st.caption("Nama temuan yang paling sering ditemukan.")
        if kata_benda_data:
            st.caption(f"{len(kata_benda_data)} objek unik")
            render_wordcloud(kata_benda_data, 'green')
        else:
            st.info("Tidak ada data objek temuan yang valid")
