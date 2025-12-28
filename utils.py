import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constants
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/IZAT RAPIH - Experiment Ketiga.csv')
MAP_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/location_name_mapped-coords.csv')

def load_css():
    st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #CBECF5 0%, #FFFFFF 100%);
        color: #00526A;
    }
    
    /* Text Color & Visibility */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #00526A !important;
        text-shadow: none !important;
    }
    
    /* Sidebar Styling - Solid Background for readability */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #CBECF5;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border: 1px solid #CBECF5;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    /* Chart Containers */
    .plot-container {
        background: transparent !important;
    }
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

    df_exploded = df.copy()

    if 'kode_temuan' in df.columns:
        df_master = df.drop_duplicates(subset='kode_temuan').copy()
    else:
        df_master = df.copy()

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
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Logo_PLN.svg", width=100)
    st.sidebar.title("HSE Filter")

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
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

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
        selected_role = st.sidebar.selectbox("Team Role", roles)
        if selected_role != 'All':
            df_master_filtered = df_master_filtered[df_master_filtered['team_role'] == selected_role]

    # Sync Exploded DF with filtered Master IDs
    if not df_master_filtered.empty:
        valid_ids = df_master_filtered['kode_temuan'].unique()
        df_exploded_filtered = df_exploded[df_exploded['kode_temuan'].isin(valid_ids)]
    else:
        df_exploded_filtered = pd.DataFrame(columns=df_exploded.columns)
            
    return df_master_filtered, df_exploded_filtered
