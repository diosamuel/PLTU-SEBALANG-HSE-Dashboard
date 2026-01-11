import pandas as pd
import streamlit as st
import os
from sqlalchemy import create_engine, text
from datetime import datetime

# --- GLOBAL COLOR PALETTE (High Contrast) ---
HSE_COLOR_MAP = {
    "Positive": "#1B5E20",         # Deep Emerald Green
    "Unsafe Action": "#B71C1C",    # Crimson Red
    "Unsafe Condition": "#F57F17", # Amber/Golden-Yellow
    "Near Miss": "#1A237E"         # Deep Indigo
}

# --- DATABASE CONNECTION ---
def get_db_engine():
    """
    Establishes a connection to the PostgreSQL Data Warehouse
    using credentials stored in .streamlit/secrets.toml
    """
    try:
        # Check if secrets exist, otherwise try environment variables or fail gracefully
        if "postgres" in st.secrets:
            db_config = st.secrets["postgres"]
            db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        else:
            # Fallback for manual testing if secrets aren't set up yet
            # Using credentials provided in migration plan
            db_url = "postgresql+psycopg2://postgres.hmdbqxhdvebwheyucmvo:bkQXObqSKo4dUtwr@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
            
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
        
        # --- SQL QUERY: Star Schema Reconstruction ---
        # 1. Reconstructs timestamps using MAKE_TIMESTAMP
        # 2. Calculates SLA dynamically (Create Date + 7 Days)
        # 3. Renames 'long' -> 'lon' for Map compatibility
        query = """
        SELECT 
            f.kode_temuan,
            
            -- 1. Reconstruct Create Date (Handle potential NULLs safely)
            CASE WHEN dd_create."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(dd_create."year", dd_create."month", dd_create."day", dd_create.hours, dd_create.minutes, 0.0)
                 ELSE NULL 
            END AS tanggal,

            -- 2. Calculate SLA (+7 Days logic)
            CASE WHEN dd_create."year" IS NOT NULL 
                 THEN (MAKE_TIMESTAMP(dd_create."year", dd_create."month", dd_create."day", dd_create.hours, dd_create.minutes, 0.0) + INTERVAL '7 days')
                 ELSE NULL 
            END AS deadline_sla,
            
            -- 3. Reconstruct Close Date (NULL if ticket is Open)
            CASE WHEN dd_close."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(dd_close."year", dd_close."month", dd_close."day", dd_close.hours, dd_close.minutes, 0.0)
                 ELSE NULL 
            END AS close_at,

            -- 4. Personnel Info
            dc.creator_name,
            dc.creator_nid,
            dc.role,
            dc.departemen AS team_role,
            dp.pic_name AS nama_pic,
            dp.pic_nama_departemen AS nama_departement_pic,

            -- 5. Finding Details
            dt.temuan_kategori,
            dt.temuan_status,
            dt.temuan_kondisi, 
            dt.temuan_kondisi AS "temuan.kondisi.lemma", -- Alias for Wordcloud
            dt.temuan_nama,     
            dt.temuan_nama AS "temuan.nama", -- Alias for backward compatibility
            dt.temuan_rekomendasi,
            
            -- 6. Geospatial (Rename 'long' to 'lon')
            loc.nama_lokasi,
            loc.lat,
            loc.long AS lon,
            loc.zona

        FROM public.fact_k3 f
        LEFT JOIN public.dim_temuan dt ON CAST(f.kode_temuan AS VARCHAR) = CAST(dt.kode_temuan AS VARCHAR)
        LEFT JOIN public.dim_creator dc ON CAST(f.creator_nid AS VARCHAR) = CAST(dc.creator_nid AS VARCHAR)
        LEFT JOIN public.dim_pic_id dp ON CAST(f.pic_id AS VARCHAR) = CAST(dp.pic_sk AS VARCHAR)
        LEFT JOIN public.dim_tempat_id loc ON CAST(f.tempat_id AS VARCHAR) = CAST(loc.nama_lokasi AS VARCHAR)
        LEFT JOIN public.dim_create_date_id dd_create ON CAST(f.create_id AS VARCHAR) = CAST(dd_create.create_date_sk AS VARCHAR)
        LEFT JOIN public.dim_close_date_id dd_close ON CAST(f.close_id AS VARCHAR) = CAST(dd_close.close_date_sk AS VARCHAR)
        """
        
        with engine.connect() as conn:
            df_master = pd.read_sql(text(query), conn)

        # --- PYTHON POST-PROCESSING ---
        
        # 1. Enforce Datetime Types
        df_master['tanggal'] = pd.to_datetime(df_master['tanggal'], errors='coerce')
        df_master['deadline_sla'] = pd.to_datetime(df_master['deadline_sla'], errors='coerce')
        
        # 2. String Cleaning (Strip whitespace)
        cols_to_strip = ['temuan_status', 'temuan_kategori', 'temuan.nama']
        for col in cols_to_strip:
            if col in df_master.columns:
                df_master[col] = df_master[col].astype(str).str.strip()
        
        # 3. Global Filter (Exclude P2K3)
        if 'temuan.nama' in df_master.columns:
            df_master = df_master[~df_master['temuan.nama'].str.lower().str.contains('p2k3', na=False)]

        # 4. Explode Logic (Crucial for Pareto Charts)
        # The DB has 1 row per finding. If temuan_nama = "Helmet, Shoes", we split it into 2 rows.
        df_exploded = df_master.copy()
        
        if df_exploded['temuan.nama'].str.contains(',').any():
            df_exploded['temuan.nama'] = df_exploded['temuan.nama'].str.split(',')
            df_exploded = df_exploded.explode('temuan.nama')
            df_exploded['temuan.nama'] = df_exploded['temuan.nama'].str.strip()
            
        # 5. Recreate 'Parent' Category (Heuristic: First word of object name)
        df_exploded['temuan.nama.parent'] = df_exploded['temuan.nama'].apply(
            lambda x: str(x).split()[0] if x else None
        )

        # 6. Extract Map Data
        df_map = df_master[['nama_lokasi', 'lat', 'lon']].drop_duplicates().dropna()

        return df_exploded, df_master, df_map

    except Exception as e:
        st.error(f"⚠️ Database Connection Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def load_css():
    st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #CBECF5 0%, #FFFFFF 100%);
        color: #00526A;
    }
    
    /* COMPACT LAYOUT OVERRIDES */
    .block-container {
        padding-top: 1rem !important; /* Reduce top padding drastically */
        padding-bottom: 1rem !important;
        padding-left: 2rem !important; 
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Text Color & Visibility */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        color: #00526A !important;
        text-shadow: none !important;
    }
    
    /* Headers */
    h1 { font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }
    h3 { font-size: 1.2rem !important; margin-bottom: 0 !important; }
    p { font-size: 0.9rem !important; }

    /* Gap Reduction */
    .element-container { margin-bottom: 0.5rem !important; }
    
    /* Sidebar Styling - Solid Background for readability */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #CBECF5;
    }
    
    /* Metric Cards - Compact */
    .metric-card {
        background: rgba(255, 255, 255, 0.6); /* Translucent White */
        padding: 5px 5px; /* Reduced vertical padding */
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.5);
        min-height: auto; /* Allow auto height for compactness */
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(10px); /* Frosted Glass Effect */
        margin-bottom: 5px;
    }
    .metric-card h3 { font-size: 0.9rem !important; margin: 0 !important; opacity: 0.8; line-height: 1.1; }
    .metric-card h2 { font-size: 1.4rem !important; margin: 0 !important; font-weight: 700; line-height: 1.1; }
    .metric-card p { font-size: 0.7rem !important; margin: 0 !important; opacity: 0.7; line-height: 1.1; }
    
    /* Chart Containers */
    .plot-container {
        background: transparent !important;
    }
    
    /* Input Elements (Selectbox, DateInput, etc) - Light Mode Translucent */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.7) !important;
        color: #00526A !important;
        border: 1px solid rgba(0, 82, 106, 0.2) !important;
        min-height: 38px;
    }
    
    /* Dataframe/Table */
    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.6) !important;
    }
    
    /* Scrollable Container */
    .scrollable-container {
        height: 400px; /* Fixed height to force scroll */
        max-height: 400px;
        overflow-y: scroll !important; /* Force scrollbar always */
        padding-right: 15px; /* Space for scrollbar */
        border: 1px solid rgba(0, 82, 106, 0.1); /* Subtle border */
        border-radius: 10px;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent; 
    }
    ::-webkit-scrollbar-thumb {
        background: #888; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555; 
    }
    /* Filter Chips (Selected Options) */
    span[data-baseweb="tag"] {
        background-color: #00526A !important; /* Context: Primary Blue */
        border: 1px solid #00526A !important;
    }
    
    /* Text inside Filter Chips */
    span[data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    
    /* Remove Icon in Filter Chips */
    span[data-baseweb="tag"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* Reduce vertical spacing in main area */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
    </style>
    
    """, unsafe_allow_html=True)

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
    st.sidebar.image("https://kehatitenayan.web.id/static/media/PLN-NP.a8c9cf3c76844681aca8.png", width=200)
    
    # DB Status Indicator
    st.sidebar.success("✅ Terhubung: Supabase")
        
    st.sidebar.title("Filter HSE")

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

    granularity = st.sidebar.radio("Periode (Granularity)", ["Monthly", "Weekly"], horizontal=True)

    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)

    # Apply Date Filter
    df_master_filtered = filter_by_date(df_master, start_date, end_date)
    
    # --- New Filters (User Requested) ---
    
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

    # Existing Role Filter (Combined with above logic flow)
    if 'team_role' in df_master.columns:
        # Use filtered values or original? Usually dependent filters are better.
        roles = ['All'] + sorted(df_master_filtered['team_role'].astype(str).unique().tolist())
        # Use index=0 (All)
        selected_role = st.sidebar.selectbox("Department", roles)
        if selected_role != 'All':
            df_master_filtered = df_master_filtered[df_master_filtered['team_role'] == selected_role]

    # Sync Exploded DF with filtered Master IDs
    if not df_master_filtered.empty:
        valid_ids = df_master_filtered['kode_temuan'].unique()
        df_exploded_filtered = df_exploded[df_exploded['kode_temuan'].isin(valid_ids)]
    else:
        df_exploded_filtered = pd.DataFrame(columns=df_exploded.columns)
            
    return df_master_filtered, df_exploded_filtered, granularity
