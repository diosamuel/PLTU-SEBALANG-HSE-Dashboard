import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constants
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/IZAT RAPIH - Experiment Ketiga.csv')
MAP_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/map_izat.csv')

# --- GLOBAL COLOR PALETTE (High Contrast) ---
HSE_COLOR_MAP = {
    "Positive": "#1B5E20",         # Deep Emerald Green (Safe/Success)
    "Unsafe Action": "#B71C1C",    # Crimson Red (High Urgency/Danger)
    "Unsafe Condition": "#F57F17", # Amber/Golden-Yellow (Caution - visible on light blue)
    "Near Miss": "#1A237E"         # Deep Indigo (Critical/Close Call)
}

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

@st.cache_data
def load_data():
    """
    Loads and preprocesses the main dataset and spatial data.
    """
    try:
        df = pd.read_csv(DATA_PATH)
        df_map = pd.read_csv(MAP_DATA_PATH)
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'], dayfirst=True, errors='coerce')
    
    if 'tanggal' in df.columns:
        df['deadline_sla'] = df['tanggal'] + pd.Timedelta(days=7)

    cols_to_strip = ['kode_temuan', 'nama_lokasi', 'temuan_status', 'temuan_kategori', 'temuan.nama']
    for col in cols_to_strip:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Filter out findings with "p2k3" in temuan.nama (Global Rule)
    if 'temuan.nama' in df.columns:
        df = df[~df['temuan.nama'].str.lower().str.contains('p2k3', na=False)]

    # Process Map Data
    if 'latlong' in df_map.columns:
        # Split and coerce to numeric, turning errors (like 'belt conveyor') into NaN
        coords = df_map['latlong'].str.split(',', expand=True)
        if coords.shape[1] >= 2:
            df_map['lat'] = pd.to_numeric(coords[0], errors='coerce')
            df_map['lon'] = pd.to_numeric(coords[1], errors='coerce')
        else:
            df_map['lat'] = None
            df_map['lon'] = None
            
    # Standardize join keys for merging
    if 'Tempat' in df_map.columns:
        df_map['Tempat'] = df_map['Tempat'].astype(str).str.strip()
    
    df_exploded = df.copy()

    if 'kode_temuan' in df.columns:
        df_master = df.drop_duplicates(subset='kode_temuan').copy()
    else:
        df_master = df.copy()
        
    # Perform Left Join if keys exist
    if 'nama_lokasi' in df_master.columns and 'Tempat' in df_map.columns:
        df_master = df_master.merge(df_map, left_on='nama_lokasi', right_on='Tempat', how='left')

    return df_exploded, df_master, df_map

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
