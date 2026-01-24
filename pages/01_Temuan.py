import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from utils import load_data, render_sidebar, set_header_title,render_wordcloud,hex_to_rgba
from constants import HSE_COLOR_MAP, CUSTOM_SCALE
from plotly.subplots import make_subplots
from pages.tabs.temuan.analisisObjek import analisisObjek
from pages.tabs.temuan.analisisKondisi import analisisKondisi
from pages.tabs.temuan.alurKategori import alurKategori
# Page Config
st.set_page_config(page_title="Analisis Temuan", page_icon=None, layout="wide")
df_exploded, df_master, _ = load_data()
df_master_filtered, df_exploded_filtered, _ = render_sidebar(df_master, df_exploded)

set_header_title("Analisis Temuan")
tabAnalisisObjek, tabAnalisisKondisi, tabAlurKategori = st.tabs(["Analisis Objek", "Analisis Kondisi", "Alur Kategori Temuan"])

with tabAnalisisObjek:

    analisisObjek(df_exploded_filtered)

with tabAnalisisKondisi:
    analisisKondisi(df_exploded_filtered)

with tabAlurKategori:
    alurKategori(df_exploded_filtered)
