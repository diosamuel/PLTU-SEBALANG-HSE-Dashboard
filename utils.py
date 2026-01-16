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
            # db_url = "postgresql://postgres.bdxkbsrnhkfjlfnxeixl:akuharusbisa@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
            db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        else:
            # Fallback for manual testing if secrets aren't set up yet
            # Using credentials provided in migration plan
            
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
        
        # --- SQL QUERY: Star Schema Denormalization ---
        # Fully denormalized query joining all dimension tables from DDL
        query = """
        SELECT 
            -- Fact Table Keys
            f.kode_temuan,
            
            -- ============================================
            -- 1. DATE DIMENSIONS (Reconstructed Timestamps)
            -- ============================================
            
            -- Create Date (tanggal pembuatan)
            CASE WHEN dd_create."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(
                    CAST(dd_create."year" AS int),
                    CAST(dd_create."month" AS int),
                    CAST(dd_create."day" AS int),
                    CAST(dd_create.hours AS int),
                    CAST(dd_create.minutes AS int),
                    0.0
                 )
                 ELSE NULL 
            END AS tanggal,
            dd_create.day_name AS create_day_name,
            
            -- SLA Deadline (+7 Days from Create Date)
            CASE WHEN dd_create."year" IS NOT NULL 
                 THEN (
                    MAKE_TIMESTAMP(
                        CAST(dd_create."year" AS int),
                        CAST(dd_create."month" AS int),
                        CAST(dd_create."day" AS int),
                        CAST(dd_create.hours AS int),
                        CAST(dd_create.minutes AS int),
                        0.0
                    ) + INTERVAL '7 days'
                 )
                 ELSE NULL 
            END AS deadline_sla,
            
            -- Close Date (tanggal penutupan)
            CASE WHEN dd_close."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(
                    CAST(dd_close."year" AS int),
                    CAST(dd_close."month" AS int),
                    CAST(dd_close."day" AS int),
                    CAST(dd_close.hours AS int),
                    CAST(dd_close.minutes AS int),
                    0.0
                 )
                 ELSE NULL 
            END AS close_at,
            dd_close.day_name AS close_day_name,
            
            -- Open Date (tanggal dibuka)
            CASE WHEN dd_open."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(
                    CAST(dd_open."year" AS int),
                    CAST(dd_open."month" AS int),
                    CAST(dd_open."day" AS int),
                    CAST(dd_open.hours AS int),
                    CAST(dd_open.minutes AS int),
                    0.0
                 )
                 ELSE NULL 
            END AS open_at,
            dd_open.day_name AS open_day_name,
            
            -- Update Date (tanggal update terakhir)
            CASE WHEN dd_update."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(
                    CAST(dd_update."year" AS int),
                    CAST(dd_update."month" AS int),
                    CAST(dd_update."day" AS int),
                    CAST(dd_update.hours AS int),
                    CAST(dd_update.minutes AS int),
                    0.0
                 )
                 ELSE NULL 
            END AS update_at,
            dd_update.day_name AS update_day_name,
            
            -- Target Date (tanggal target penyelesaian)
            CASE WHEN dd_target."year" IS NOT NULL 
                 THEN MAKE_TIMESTAMP(
                    CAST(dd_target."year" AS int),
                    CAST(dd_target."month" AS int),
                    CAST(dd_target."day" AS int),
                    CAST(dd_target.hours AS int),
                    CAST(dd_target.minutes AS int),
                    0.0
                 )
                 ELSE NULL 
            END AS target_at,
            dd_target.day_name AS target_day_name,

            -- ============================================
            -- 2. CREATOR DIMENSION (Pelapor)
            -- ============================================
            dc.creator_id,
            dc.creator_name,
            dc.creator_kode_jabatan,
            dc.nama_perusahaan AS creator_perusahaan,
            dc.creator_departemen_dan_role,
            dc.creator_role,
            dc.creator_departemen,

            -- ============================================
            -- 3. PIC DIMENSION (Person In Charge)
            -- ============================================
            dp.pic_sk,
            dp.pic_id,
            dp.pic_name,
            dp.pic_departemen,

            -- ============================================
            -- 4. TEMUAN DIMENSION (Finding Details)
            -- ============================================
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
            
            -- ============================================
            -- 5. TEMPAT/LOKASI DIMENSION (Geospatial)
            -- ============================================
            -- Fallback: Use fact table tempat_id if join to dim_tempat fails
            COALESCE(loc.nama_lokasi, f.tempat_id) AS nama_lokasi,
            loc.lat,
            loc.long AS lon,
            loc.zone AS zona

        FROM public.fact_k3 f
        
        -- Temuan Dimension
        LEFT JOIN public.dim_temuan dt 
            ON f.kode_temuan = dt.kode_temuan
        
        -- Creator Dimension
        LEFT JOIN public.dim_creator dc 
            ON f.creator_id = dc.creator_id
        
        -- PIC Dimension
        LEFT JOIN public.dim_pic dp 
            ON f.pic_sk = dp.pic_sk
        
        -- Tempat/Lokasi Dimension
        LEFT JOIN public.dim_tempat loc 
            ON UPPER(f.tempat_id) = UPPER(loc.nama_lokasi)
        
        -- Create Date Dimension
        LEFT JOIN public.dim_create_date_dup dd_create 
            ON f.kode_temuan = dd_create.kode_temuan
        
        -- Close Date Dimension
        LEFT JOIN public.dim_close_date_dup dd_close 
            ON f.kode_temuan = dd_close.kode_temuan
        
        -- Open Date Dimension
        LEFT JOIN public.dim_open_date_dup dd_open 
            ON f.kode_temuan = dd_open.kode_temuan
        
        -- Update Date Dimension
        LEFT JOIN public.dim_update_date_dup dd_update 
            ON f.kode_temuan = dd_update.kode_temuan
        
        -- Target Date Dimension
        LEFT JOIN public.dim_target_date_dup dd_target 
            ON f.kode_temuan = dd_target.kode_temuan
        """
        
        # Execute query using raw DBAPI connection for pandas compatibility
        with engine.connect() as conn:
            # Get underlying DBAPI connection that pandas expects
            raw_conn = conn.connection
            df_master = pd.read_sql(query, raw_conn)

        # --- PYTHON POST-PROCESSING ---
        
        # 1. Enforce Datetime Types for all date columns
        date_columns = ['tanggal', 'deadline_sla', 'close_at', 'open_at', 'update_at', 'target_at']
        for col in date_columns:
            if col in df_master.columns:
                df_master[col] = pd.to_datetime(df_master[col], errors='coerce')
        
        # 2. String Cleaning (Strip whitespace for key columns)
        cols_to_strip = [
            'temuan_status', 'temuan_kategori', 'temuan_nama', 'temuan_nama_spesifik',
            'temuan_kondisi', 'temuan_rekomendasi', 'creator_name', 'creator_departemen',
            'pic_name', 'pic_departemen', 'nama_lokasi', 'zona'
        ]
        for col in cols_to_strip:
            if col in df_master.columns:
                df_master[col] = df_master[col].astype(str).str.strip()
                # Replace 'None' and 'nan' strings with actual NaN
                df_master[col] = df_master[col].replace(['None', 'nan', 'NaN', ''], pd.NA)
        
        # 3. Global Filter (Exclude P2K3)
        if 'temuan_nama' in df_master.columns:
            df_master = df_master[~df_master['temuan_nama'].astype(str).str.lower().str.contains('p2k3', na=False)]

        # 4. Create exploded dataframe (for multi-value analysis)
        df_exploded = df_master.copy()

        # 5. Extract Map Data (unique locations with coordinates)
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
        padding-left: 1rem !important; 
        padding-right: 1rem !important;
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
    .metric-card h3 { font-size: 0.9rem !important; margin: 0 !important; opacity: 0.8;  }
    .metric-card h1 { font-size: 2rem !important; margin: 0 !important; font-weight: 700;  }
    .metric-card p { font-size: 0.7rem !important; margin: 0 !important; opacity: 0.7;  }
    
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

    # Existing Department Filter (Combined with above logic flow)
    if 'creator_departemen' in df_master.columns:
        # Use filtered values or original? Usually dependent filters are better.
        depts = ['All'] + sorted(df_master_filtered['creator_departemen'].dropna().astype(str).unique().tolist())
        # Use index=0 (All)
        selected_dept = st.sidebar.selectbox("Department", depts)
        if selected_dept != 'All':
            df_master_filtered = df_master_filtered[df_master_filtered['creator_departemen'] == selected_dept]

    # Sync Exploded DF with filtered Master IDs
    if not df_master_filtered.empty:
        valid_ids = df_master_filtered['kode_temuan'].unique()
        df_exploded_filtered = df_exploded[df_exploded['kode_temuan'].isin(valid_ids)]
    else:
        df_exploded_filtered = pd.DataFrame(columns=df_exploded.columns)
            
    return df_master_filtered, df_exploded_filtered, granularity
