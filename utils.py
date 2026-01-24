import pandas as pd
import streamlit as st
import os
from sqlalchemy import create_engine, text
from datetime import datetime
from constants import flat_colors, HSE_COLOR_MAP
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def render_wordcloud(frequency_dict, color_scheme='blue', title=""):
    if not frequency_dict:
        st.info("Tidak ada data untuk wordcloud")
        return

    color = flat_colors.get(color_scheme, '#1f77b4')

    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            mode='RGB',               
            color_func=lambda *args, **kwargs: color,
            relative_scaling=0.5,
            min_font_size=10,
            max_font_size=100,
            prefer_horizontal=0.7,
            collocations=False,
            margin=10
        ).generate_from_frequencies(frequency_dict)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        plt.tight_layout(pad=0)

        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    except Exception as e:
        st.error(f"Error generating wordcloud: {e}")

def hex_to_rgba(hex_color, opacity=0.4):
    """Convert hex color to rgba with specified opacity"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {opacity})"
    return f"rgba(0, 82, 106, {opacity})"


# --- DATABASE CONNECTION ---
def get_db_engine():
    """
    Establishes a connection to the PostgreSQL Data Warehouse
    using credentials stored in .streamlit/secrets.toml
    """
    try:
        if "postgres" in st.secrets:
            db_config = st.secrets["postgres"]
            db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        else:
            db_url = ""
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.error(f"Failed to configure database engine: {e}")
        return None

@st.cache_data(ttl=3600)
def load_data():
    """
    Loads data from the PostgreSQL Data Warehouse and preprocesses it 
    to match the legacy CSV format expected by the Streamlit app.
    """
    try:
        engine = get_db_engine()
        if not engine:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        query = """
SELECT 
  -- Fact Table Keys
  f.kode_temuan, 
  -- Create Date (tanggal pembuatan)
  CASE WHEN dd_create."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_create."year" AS int), 
    CAST(dd_create."month" AS int), 
    CAST(dd_create."day" AS int), 
    CAST(dd_create.hours AS int), 
    CAST(dd_create.minutes AS int), 
    0.0
  ) ELSE NULL END AS tanggal, 
  dd_create.day_name AS create_day_name, 
  -- Close Date (tanggal penutupan)
  CASE WHEN dd_close."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_close."year" AS int), 
    CAST(dd_close."month" AS int), 
    CAST(dd_close."day" AS int), 
    CAST(dd_close.hours AS int), 
    CAST(dd_close.minutes AS int), 
    0.0
  ) ELSE NULL END AS close_at, 
  dd_close.day_name AS close_day_name, 
  -- Open Date (tanggal dibuka)
  CASE WHEN dd_open."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_open."year" AS int), 
    CAST(dd_open."month" AS int), 
    CAST(dd_open."day" AS int), 
    CAST(dd_open.hours AS int), 
    CAST(dd_open.minutes AS int), 
    0.0
  ) ELSE NULL END AS open_at, 
  dd_open.day_name AS open_day_name, 
  -- Update Date (tanggal update terakhir)
  CASE WHEN dd_update."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_update."year" AS int), 
    CAST(dd_update."month" AS int), 
    CAST(dd_update."day" AS int), 
    CAST(dd_update.hours AS int), 
    CAST(dd_update.minutes AS int), 
    0.0
  ) ELSE NULL END AS update_at, 
  dd_update.day_name AS update_day_name, 
  -- Target Date (tanggal target penyelesaian)
  CASE WHEN dd_target."year" IS NOT NULL THEN MAKE_TIMESTAMP(
    CAST(dd_target."year" AS int), 
    CAST(dd_target."month" AS int), 
    CAST(dd_target."day" AS int), 
    CAST(dd_target.hours AS int), 
    CAST(dd_target.minutes AS int), 
    0.0
  ) ELSE NULL END AS target_at, 
  dd_target.day_name AS target_day_name, 
  dc.creator_id, 
  dc.creator_name, 
  dc.creator_kode_jabatan, 
  dc.nama_perusahaan AS creator_perusahaan, 
  dc.creator_departemen_dan_role, 
  dc.creator_role, 
  dc.creator_departemen, 
  dp.pic_id, 
  dp.pic_name, 
  dp.pic_departemen, 
  dt.raw_judul, 
  dt.raw_kondisi, 
  dt.raw_rekomendasi, 
  dt.temuan_nama, 
  dt.temuan_kondisi, 
  dt.temuan_rekomendasi, 
  dt.temuan_kategori, 
  dt.temuan_status, 
  dt.temuan_nama_spesifik, 
  dt.note AS temuan_note, 
  dt.keterangan_lokasi, 
  COALESCE(loc.nama_lokasi, f.tempat_id) AS nama_lokasi, 
  loc.lat, 
  loc.long AS lon, 
  loc.zone AS zona 
FROM 
  public.fact_k3 f -- Temuan Dimension
  LEFT JOIN public.dim_temuan dt ON f.kode_temuan = dt.kode_temuan -- Creator Dimension
  LEFT JOIN public.dim_creator dc ON f.creator_id = dc.creator_id -- PIC Dimension
  LEFT JOIN public.dim_pic dp ON f.kode_temuan = dp.kode_temuan -- Tempat/Lokasi Dimension
  LEFT JOIN public.dim_tempat loc ON UPPER(f.tempat_id) = UPPER(loc.nama_lokasi) -- Create Date Dimension
  LEFT JOIN public.dim_create_date dd_create ON f.kode_temuan = dd_create.kode_temuan -- Close Date Dimension
  LEFT JOIN public.dim_close_date dd_close ON f.kode_temuan = dd_close.kode_temuan -- Open Date Dimension
  LEFT JOIN public.dim_open_date dd_open ON f.kode_temuan = dd_open.kode_temuan -- Update Date Dimension
  LEFT JOIN public.dim_update_date dd_update ON f.kode_temuan = dd_update.kode_temuan -- Target Date Dimension
  LEFT JOIN public.dim_target_date dd_target ON f.kode_temuan = dd_target.kode_temuan
        """
        
        # Execute query using raw DBAPI connection for pandas compatibility
        with engine.connect() as conn:
            raw_conn = conn.connection
            df_master = pd.read_sql(query, raw_conn)
        
        df_exploded = df_master.copy()
        df_map = df_master[['nama_lokasi', 'lat', 'lon']]

        return df_exploded, df_master, df_map

    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def load_css():
    st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

def set_header_title(title):
    st.markdown(f"""
    <style>
    /* Mobile/Tablet Adjustment */
    @media (max-width: 640px) {{
        header[data-testid="stHeader"]::before {{
            content: "{title}";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 1rem;
            font-weight: 700;
            color: #00526A;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 60%;
        }}
    }}
    /* Desktop */
    @media (min-width: 641px) {{
        header[data-testid="stHeader"]::before {{
            content: "{title}";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.4rem;
            font-weight: 700;
            color: #00526A;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def filter_by_date(df, start_date, end_date):
    if 'tanggal' not in df.columns:
        return df
    # Ensure start_date and end_date are datetime.date objects
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
        
    mask = (df['tanggal'].dt.date >= start_date) & (df['tanggal'].dt.date <= end_date)
    return df.loc[mask]

def calculate_kpi(df_master):
    if df_master.empty:
        return 0, 0, 0, 0

    total_findings = df_master['kode_temuan'].nunique()
    
    if 'temuan_status' in df_master.columns:
        closed_count = df_master[df_master['temuan_status'].str.lower() == 'closed'].shape[0]
        closing_rate = (closed_count / total_findings) * 100 if total_findings > 0 else 0
    else:
        closing_rate = 0

    mttr = 0 
    participation = 0
    if 'creator_name' in df_master.columns:
        participation = df_master['creator_name'].nunique()
        
    return total_findings, closing_rate, mttr, participation

def render_sidebar(df_master, df_exploded):
    """
    Renders the sidebar filters and returns filtered dataframes.
    Also injects the global CSS.
    """
    load_css()
    
    # Reverted to Wikimedia Logo as requested
    st.sidebar.image("./asset/logo-pln.png", width=200)        
    st.sidebar.title("Filter")

    # Date Filter
    if not df_master.empty and 'tanggal' in df_master.columns:
        min_dt = df_master['tanggal'].min()
        max_dt = df_master['tanggal'].max()
        
        # Handle Nat/None
        if pd.isnull(min_dt): min_dt = datetime.today()
        if pd.isnull(max_dt): max_dt = datetime.today()
        
        min_date = min_dt.date()
        max_date = max_dt.date()
    else:
        min_date = datetime.today().date()
        max_date = datetime.today().date()

    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    granularity = st.sidebar.radio("Periode", ["Bulanan", "Mingguan"], horizontal=True)

    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)

    # Apply Date Filter
    df_master_filtered = filter_by_date(df_master, start_date, end_date)
    
    # 1. Kategori Temuan
    if 'temuan_kategori' in df_master_filtered.columns:
        cats = ['All'] + sorted(df_master_filtered['temuan_kategori'].astype(str).unique().tolist())
        sel_cats = st.sidebar.multiselect("Kategori Temuan", cats)
        if sel_cats and 'All' not in sel_cats:
            df_master_filtered = df_master_filtered[df_master_filtered['temuan_kategori'].isin(sel_cats)]
            
    # 2. Status Temuan
    if 'temuan_status' in df_master_filtered.columns:
        statuses = ['All'] + sorted(df_master_filtered['temuan_status'].astype(str).unique().tolist())
        sel_stats = st.sidebar.multiselect("Status Temuan", statuses)
        if sel_stats and 'All' not in sel_stats:
            df_master_filtered = df_master_filtered[df_master_filtered['temuan_status'].isin(sel_stats)]
            
    # 3. Area/Lokasi
    if 'nama_lokasi' in df_master_filtered.columns:
        locs = ['All'] + sorted(df_master_filtered['nama_lokasi'].astype(str).unique().tolist())
        sel_locs = st.sidebar.multiselect("Area/Lokasi", locs)
        if sel_locs and 'All' not in sel_locs:
            df_master_filtered = df_master_filtered[df_master_filtered['nama_lokasi'].isin(sel_locs)]

    if 'creator_departemen' in df_master.columns:
        depts = ['All'] + sorted(df_master_filtered['creator_departemen'].dropna().astype(str).unique().tolist())
        selected_dept = st.sidebar.selectbox("Department", depts)
        if selected_dept != 'All':
            df_master_filtered = df_master_filtered[df_master_filtered['creator_departemen'] == selected_dept]

    if not df_master_filtered.empty:
        valid_ids = df_master_filtered['kode_temuan'].unique()
        df_exploded_filtered = df_exploded[df_exploded['kode_temuan'].isin(valid_ids)]
    else:
        df_exploded_filtered = pd.DataFrame(columns=df_exploded.columns)
            
    return df_master_filtered, df_exploded_filtered, granularity
