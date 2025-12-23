import streamlit as st
import sys
import pandas as pd
from pathlib import Path
import sqlite3
from dash import Dash, dcc, html, dash_table
import plotly.express as px
import traceback
import streamlit.components.v1 as components
from tracking_script import inject_tracking_script
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import datetime
import random
import time

# --- KONFIGURASI TEMA DAN LAYOUT ---
st.set_page_config(
    page_title="Dashboard Kesehatan Kalsel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Kustom untuk Styling yang Diminta
st.markdown(
    """
    <style>
    /* Import Poppins dari Google Fonts dan gunakan sebagai font global */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    /* Target: main content area */
    .stApp {
        background-color: #720709; 
        min-height: 100vh;
    }

    /* Warna untuk Card 2 (Kab/Kota) */
    .card-kabkota {
        background-color: #044335; /* Hijau Gelap */
        height: 1200px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: -40px !important;
        margin-right: -70px !important;
        border-radius: 20px;        
    }
    
    .card-dashboard {
        height: 120px;
        width: 97%;
        border-radius: 20px;
        margin-top: 20px;
        background-image: linear-gradient(to right, #00776b, #0B634F, #044335 60%); /* Hijau Gelap */
        display: flex;
        align-items: center;
        background-size: 400% 400%;
        animation: moveGradient 5s ease infinite;
        position: fixed;
        top: 0;
        left: 15px; /* Mepet kiri */
        z-index: 1000;
        padding: 10px 15px;
        box-sizing: border-box;
        flex-shrink: 0;
    }
    /* DEFINISI ANIMASI GRADASI BERGERAK (Untuk Card Dashboard) */
    @keyframes moveGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    h2.main-title {
        font-size: 2.5rem !important; 
        font-weight: bold !important;
        color: white !important;
        margin: 0 !important;        
        padding: 0 !important;
        line-height: 1.0 !important;
    }

    h4.sub-title { 
        font-size: 1.25rem !important; 
        font-weight: 500 !important;
        color: #ffb74d !important;    
        margin: -5px 0 0 0 !important;         
        padding: 0 !important;
        line-height: 1.0 !important;
    }

    /* Terapkan Poppins sebagai font utama di seluruh komponen yang kita kendalikan */
    body, .stApp, .card-dashboard, .trend-chart-container, .sidebar-title, .item-text {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Buat Sidebar menggunakan native Streamlit component, dengan gaya custom */    
    [data-testid="stSidebar"] {    
        background-color: transparent !important;    
    }
        
    [data-testid="stSidebar"] > div:first-child {    
        top: 150px;
        width: 327px;    
        height: calc(100vh - 150px);    
        background-color: #044335;    
        border-radius: 0px 20px 20px 0px;    
        padding-top: 0px;        
    }
    
    /* Lebih spesifik untuk memastikan style tidak tertimpa oleh Streamlit */
    [data-testid="stSidebar"] .sidebar-title {
        color: #ffffff !important;
        font-size: 1.7rem;
    }
    
    /* Styling untuk radio button tahun di sidebar */
    div[role="radiogroup"] {
        padding-left: 110px !important;
    }

    /* Style each radio item's label */
    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
        margin-bottom: 10px !important; 
    }

    /* Style the radio input button itself */
    div[role="radiogroup"] input[type="radio"] {
        width: 50px !important;
        height: 50px !important;
        cursor: pointer !important;
        accent-color: #4dd0e1 !important; 
        margin-right: 35px !important; 
    }
    
    /* Buat Grafik tren */
    .trend-chart-container {
        background-color: white;
        border-radius: 5px;
        padding: 5px;
            width: 100%;
            max-width: 100%;
        margin-bottom: 25px;
            margin-left: 0;
        margin-top: 9px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    }

    /* Pastikan Plotly chart berada di dalam kartu putih dan bersih */
    .trend-chart-container .plotly-graph-div,
    .trend-chart-container .js-plotly-plot {
        background-color: transparent !important; /* biarkan kartu putih sebagai background */
        width: 100% !important;
        height: auto !important;
    }

    /* Responsif: sedikit padding pada layar kecil */
    @media (max-width: 768px) {
        .trend-chart-container { padding: 8px; }
    }
    /* Catatan: selector untuk judul chart/metric/tabel dihilangkan karena
       markup saat ini tidak menggunakan elemen-elemen tersebut. Jika nanti
       ditambahkan kembali, styling ini bisa dikembalikan. */

    </style>
    """,
    unsafe_allow_html=True
)

# --- KONFIGURASI JALUR DATA DAN DB ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Tambahkan root project ke sys.path agar bisa import modul ETL
sys.path.append(str(PROJECT_ROOT))

# Import modul ETL untuk update data UI/UX secara real-time
try:
    from src.etl_scripts import etl_uiux_metrics
except ImportError:
    etl_uiux_metrics = None

# Sumber: Data Mart
MART_PATH = DATA_ROOT / "04_data_mart"
MART_DB_FILE = MART_PATH / "mart_health_summary.db"

# --- VERIFIKASI ---
print(f"PROJECT_ROOT ditentukan sebagai: {PROJECT_ROOT.resolve()}")
print(f"Path Data Mart yang dihasilkan: {MART_DB_FILE.resolve()}")
 
# --- FUNGSI UTAMA DASHBOARD ---
def main_app():
    # Import tracking
    from tracking_script import inject_tracking_script
    import streamlit.components.v1 as components  # Sudah ada di import atas, tapi pastikan
    
    # Inject tracking script - GUNAKAN components.html
    tracking_html = inject_tracking_script()
    components.html(tracking_html, height=0)  # GANTI dari st.markdown
        
    # --- Sidebar (Pindah ke sini untuk kontrol terpusat) ---
    with st.sidebar:
        st.markdown('<h2 class="sidebar-title" style="padding-left:20px; margin-top: -20px; ">Pilih Dashboard</h2>', unsafe_allow_html=True)
        page = st.radio(
            "Pilih Dashboard",
            ("Dashboard Kesehatan", "UI/UX Analytics"),
            label_visibility="collapsed"
        )

    if page == "UI/UX Analytics":
        render_uiux_dashboard()
        return # Hentikan eksekusi agar tidak melanjutkan ke kode dashboard kesehatan

    # === KODE UNTUK DASHBOARD KESEHATAN ===
    # Mapping id_tahun ke tahun (definisikan di awal fungsi main_app)
    year_to_id = {
        2017: 1, 2018: 2, 2019: 3, 2020: 4,
        2022: 5, 2023: 6, 2024: 7, 2021: 8
    }

    # Mapping id_wilayah ke nama wilayah
    wilayah_mapping = {
        1: 'Tanah Laut', 2: 'Kota Baru', 3: 'Banjar',
        4: 'Barito Kuala', 5: 'Tapin', 6: 'Hulu Sungai Selatan',
        7: 'Hulu Sungai Tengah', 8: 'Hulu Sungai Utara',
        9: 'Tabalong', 10: 'Balangan', 11: 'Kota Banjarmasin',
        12: 'Kota Banjar Baru'
    }
        
    # --- Fixed header (separate) ---
    st.markdown(
        """
        <div class="card-dashboard">
            <img 
                src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAIABJREFUeJzs3XlY1VW7N/Dv3pvNIFsQAXEEHFAEp3IAJ0DUisISTdOsJEUt7TEfS4PKzOrNTNOsNKdQK7WcywEtwVBztjQUNExBMSccEJAZ3j/Ink4Wwl7rt397+H6uq+uc6xzWvW5UWPdeI0BERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERGTZNGonYCa8AIQBCAbQGkBTAJ4AnAHYq5cWERFZsGIA+QCuAjgD4CSA/QB2AriiYl4AbLsAqAtgKIBnAHSGbf9ZEBGR6VQAOADgCwCrANxQIwlbHPQaAngZwGhUfsInIiJSSx6AhQA+AHDRlB3rTNmZyuwA/AfAegCh4NQ+ERGpzx5ANwDP//G/7wVQZoqObWUGwA/A1wDuUzsRIiKiKhwB8ASA35TuSKt0B2bgMQCHwcGfiIjMX0cAPwHop3RH1r4EMBzAlwCc1E6EiIiomhwADAZwCZUzAoqw5gIgBsBnsO7vkYiIrJMWQCSALAA/K9GBte4BeAzAOnDwJyIiy1YKYACATbIDW2MB0AKVUyYuaidCREQkQS4q76s5JTOotW0C1ANYDQ7+RERkPWoDWIHK4+zSWNsU+csAnlY7CSIiIskaAsgBsE9WQGtaAmiIyukRg9qJEBERKSAXQEtUng4QZk1LAC+Dgz8REVmv2gAmygpmLTMAdQGcA+/2JyIi65YHwBsSHhCylhmAJ8HBn4iIrJ8BwBAZgaxlBuAAgC4yAgUGBmL48OEIDw+Ht7c3nJ1ZVxARUc3l5+fj3LlzSEpKwrJly5Camior9D5UPiAkxBoKAC9UPqEo9L04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" 
                alt="Dashboard Icon" 
                style="width: 120px; height: 120px; margin-left: 20px; object-fit: contain; margin-right: 20px;">
            <div style=" display: flex; flex-grow: 1; flex-direction: column; justify-content: center; line-height: 1.0; padding: 0; ">
                <h2 class="main-title">Dashboard Kesehatan</h2>
                <h4 class="sub-title">Provinsi Kalimantan Selatan</h4>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
        
    # --- Sidebar (Menggunakan st.sidebar untuk interaktivitas) ---
    with st.sidebar:
        st.markdown('<h2 class="sidebar-title" style="padding-left:20px; margin-top: -20px; ">Tahun</h2>', unsafe_allow_html=True)
        selected_year = st.radio(
            "Pilih Tahun", 
            options=[2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017],
            index=0,
            key='selected_year',
            label_visibility='collapsed'
        )

    # === LAYOUT RESPONSIF DENGAN KOLOM STREAMLIT ===
    chart_col, right_col = st.columns([2.4, 1], gap="medium")

    # === Grafi Tren di kolom tengah (sekitar 50% layar) ===
    with chart_col:
        # --- Ambil data dari mart_workload_ratio dan buat grafik tren ---
        try:
            if not MART_DB_FILE.exists():
                st.warning(f"Data Mart tidak ditemukan di: {MART_DB_FILE}")
            else:
                query = """
                SELECT
                    tahun,
                    SUM(COALESCE(total_workforce,0)) AS total_workforce,
                    SUM(COALESCE(total_cases,0)) AS total_cases
                FROM mart_workload_ratio
                GROUP BY tahun
                ORDER BY tahun;
                """

                with sqlite3.connect(MART_DB_FILE) as conn:
                    df_trend = pd.read_sql_query(query, conn)

                if df_trend.empty:
                    st.info("Tidak ada data di tabel `mart_workload_ratio` untuk ditampilkan.")
                else:
                    df_trend['total_workforce'] = pd.to_numeric(df_trend['total_workforce'], errors='coerce').fillna(0)
                    df_trend['total_cases'] = pd.to_numeric(df_trend['total_cases'], errors='coerce').fillna(0)

                    custom_ticks = [0, 100, 500, 10000, 15000, 50000, 100000]

                    def transform_value(v, ticks):
                        if v <= ticks[0]:
                            return 0.0
                        for i in range(len(ticks) - 1):
                            t0, t1 = ticks[i], ticks[i+1]
                            if t0 <= v <= t1:
                                return i + (v - t0) / (t1 - t0)
                        return float(len(ticks) - 1)

                    df_trend['workforce_trans'] = df_trend['total_workforce'].apply(lambda x: transform_value(x, custom_ticks))
                    df_trend['cases_trans'] = df_trend['total_cases'].apply(lambda x: transform_value(x, custom_ticks))

                    fig = px.line(df_trend, x='tahun', y=['workforce_trans', 'cases_trans'], markers=True)
                    fig.data[0].name = 'Total Tenaga Kesehatan'
                    fig.data[0].line.color = '#1f77b4'
                    fig.data[0].line.shape = 'spline'
                    fig.data[0].fill = 'tozeroy'
                    fig.data[0].fillcolor = 'rgba(31,119,180,0.18)'

                    fig.data[1].name = 'Total Kasus Penyakit'
                    fig.data[1].line.color = '#8c8c8c'
                    fig.data[1].line.shape = 'spline'
                    fig.data[1].fill = 'tozeroy'
                    fig.data[1].fillcolor = 'rgba(140,140,140,0.12)'

                    tick_positions = list(range(len(custom_ticks)))
                    tick_labels = [f"{v:,}" for v in custom_ticks]

                    fig.update_layout(
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                        margin=dict(l=20, r=20, t=10, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )

                    num_intervals = max(1, len(tick_positions) - 1)
                    px_per_interval = 50
                    chart_height = num_intervals * px_per_interval + 100
                    fig.update_layout(height=chart_height)

                    min_year = int(df_trend['tahun'].min())
                    max_year = int(df_trend['tahun'].max())
                    x_pad = 0.2 
                    
                    fig.update_xaxes(tickmode='linear', tick0=min_year, dtick=1, range=[min_year - x_pad, max_year + x_pad], title_text='Tahun', title_standoff=30, showgrid=False, zeroline=False)
                    fig.update_yaxes(range=[0, tick_positions[-1]], tickmode='array', tickvals=tick_positions, ticktext=tick_labels, title_text='Jumlah', title_standoff=30)
                    fig.update_layout(margin=dict(l=78, r=20, t=0, b=35))
                    fig.data[0].customdata = df_trend['total_workforce']
                    fig.data[1].customdata = df_trend['total_cases']
                    fig.data[0].hovertemplate = 'Tahun: %{x}<br>Total Tenaga Kesehatan: %{customdata:,}<extra></extra>'
                    fig.data[1].hovertemplate = 'Tahun: %{x}<br>Total Kasus: %{customdata:,}<extra></extra>'                   
                    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')                    
                    card_html = f"""
                    <div style="background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; box-sizing: border-box;" class="trend-chart-container">
                        <h2 style="color:#044335; font-size:1.7rem; margin-left: 20px; margin-top: 10px; font-family: 'Poppins', sans-serif !important; ">Grafik Tren</h2>
                        <style>
                            /* Pastikan elemen Plotly transparan supaya wrapper putih terlihat */
                            .plotly-graph-div, .js-plotly-plot {{ font-family: 'Poppins', sans-serif !important; background-color: transparent !important; width:100% !important; height:auto !important; margin:0; }}
                            body {{ background-color: transparent !important; margin:0; padding:0; }}
                        </style>
                        {fig_html}
                    </div>
                    """
                    components.html(card_html, height=chart_height + 130, scrolling=False)
        except Exception as e:
            st.error(f"Gagal membuat grafik tren: {e}")

        st.markdown('<h3 style="background-color: #DAA520; color: white; text-align: center; border-radius: 10px; padding: 10px;">Analisis Berdasarkan Wilayah</h3>', unsafe_allow_html=True)

        # === Summary Cards dan Donut Chart ===
        # Tahun yang dipilih diambil dari widget radio di sidebar (st.session_state.selected_year)
        selected_year = st.session_state.selected_year

        try:
            # Query data untuk tahun yang dipilih
            query_summary = """
            SELECT
                SUM(COALESCE(total_workforce,0)) AS total_workforce,
                SUM(COALESCE(total_cases,0)) AS total_cases
            FROM mart_workload_ratio
            WHERE tahun = ?
            """
            
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_summary = pd.read_sql_query(query_summary, conn, params=(selected_year,))
            
            if not df_summary.empty:
                total_workforce = int(df_summary['total_workforce'].iloc[0])
                total_cases = int(df_summary['total_cases'].iloc[0])
                
                # Hitung persentase
                total = total_workforce + total_cases
                if total > 0:
                    pct_cases = (total_cases / total) * 100
                    pct_workforce = (total_workforce / total) * 100
                else:
                    pct_cases = 0
                    pct_workforce = 0
                
                # HTML untuk Cards dan Donut Chart
                summary_html = f"""
                <div style="display: flex; gap: 20px; margin-top: 20px; width: 100%;">
                    <!-- Kolom Kiri: 2 Cards -->
                    <div style="flex: 1; display: flex; flex-direction: column; gap: 20px;">
                        <!-- Card 1: Total Kasus Penyakit -->
                        <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%); 
                                    border-radius: 15px; padding: 25px; 
                                    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                                    display: flex; align-items: center; gap: 20px;">
                            <div style="font-size: 3.5rem;">📋</div>
                            <div>
                                <div style="color: white; font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', sans-serif;">
                                    {total_cases:,}
                                </div>
                                <div style="color: white; font-size: 1rem; font-family: 'Poppins', sans-serif;">
                                    Total Kasus Penyakit
                                </div>
                            </div>
                        </div>
                        
                        <!-- Card 2: Total Tenaga Kesehatan -->
                        <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%); 
                                    border-radius: 15px; padding: 25px; 
                                    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                                    display: flex; align-items: center; gap: 20px;">
                            <div style="font-size: 3.5rem;">👥</div>
                            <div>
                                <div style="color: white; font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', sans-serif;">
                                    {total_workforce:,}
                                </div>
                                <div style="color: white; font-size: 1rem; font-family: 'Poppins', sans-serif;">
                                    Total Tenaga Kesehatan
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Kolom Kanan: Donut Chart -->
                    <div style="flex: 1; background-color: white; border-radius: 15px; 
                                padding: 1px; box-shadow: 0 8px 20px rgba(0,0,0,0.12);">
                        <h4 style="color: #044335; text-align: center; margin-bottom: -10px; 
                                   font-family: 'Poppins', sans-serif;">
                            Rasio Kasus Penyakit VS Tenaga Kesehatan
                        </h4>
                        <div id="donut-chart-{selected_year}" style= "height: 90%; margin-top: 5px;"></div>
                    </div>
                </div>
                
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <script>
                    var data = [{{
                        values: [{total_cases}, {total_workforce}],
                        labels: ['Kasus Penyakit', 'Tenaga Kesehatan'],
                        type: 'pie',
                        hole: 0.6,
                        marker: {{
                            colors: ['#4dd0e1', '#7e57c2']
                        }},
                        textinfo: 'none',
                        hovertemplate: '%{{label}}<br>%{{value:,}}<br>%{{percent}}<extra></extra>'
                    }}];
                    
                    var layout = {{
                        showlegend: true,
                        legend: {{
                            orientation: 'h',
                            x: 0.5,
                            xanchor: 'center',
                            y: -0.1
                        }},
                        margin: {{l: 20, r: 20, t: 20, b: 60}},
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: {{
                            family: 'Poppins, sans-serif'
                        }},
                        annotations: [{{
                            text: '100%',
                            x: 0.5,
                            y: 0.5,
                            font: {{
                                size: 32,
                                family: 'Poppins, sans-serif',
                                color: '#044335'
                            }},
                            showarrow: false
                        }}]
                    }};
                    
                    Plotly.newPlot('donut-chart-{selected_year}', data, layout, {{responsive: true}});
                </script>
                """
                
                components.html(summary_html, height=290, scrolling=False)
        except Exception as e:
            st.error(f"Gagal membuat summary cards: {e}")
                   
        # === Stacked Bar Chart: Kasus Penyakit per Wilayah ===
        try:
            # Query data kasus penyakit per wilayah dan jenis penyakit
            query_cases = """
            SELECT
                nama_wilayah,
                nama_penyakit,
                SUM(COALESCE(total_cases,0)) AS total_cases
            FROM mart_annual_case_summary
            WHERE tahun = ?
            GROUP BY nama_wilayah, nama_penyakit
            ORDER BY nama_wilayah
            """
            
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_cases = pd.read_sql_query(query_cases, conn, params=(selected_year,))
            
            if not df_cases.empty:
                # Pivot data untuk stacked bar chart
                df_pivot = df_cases.pivot(index='nama_wilayah', columns='nama_penyakit', values='total_cases').fillna(0)
                
                # Definisi warna untuk setiap penyakit
                colors = {
                    'Jumlah Kasus Penyakit - HIV/AIDS Kasus Baru': "#E60A0A",
                    'Jumlah Kasus Penyakit - Malaria (Suspek)': '#ffb74d',
                    'Jumlah Kasus Penyakit - TB Paru': '#4dd0e1',
                    'Jumlah Kasus Penyakit - Pneumonia': '#e57373',
                    'Jumlah Kasus Penyakit - Kusta': '#64b5f6',
                    'Jumlah Kasus Penyakit - Tetanus Neonatorum': '#999999',
                    'Jumlah Kasus Penyakit - Campak': '#ba68c8',
                    'Jumlah Kasus Penyakit - Diare': '#f06292',
                    'Jumlah Kasus Penyakit - Demam Berdarah Dengue (DBD)': '#fff176',
                    'Jumlah Kasus Penyakit - HIV/AIDS Kasus Kumulatif': '#a1887f',
                    'Jumlah Kasus Penyakit - Infeksi Menular Seksual (IMS)': '#90a4ae',
                    'Jumlah Kasus Penyakit - Angka Penemuan TBC': '#4db6ac',
                    'Jumlah Kasus Penyakit - Angka Keberhasilan Pengobatan TBC': '#ffb300',
                    'Jumlah Kasus Penyakit - Penemuan Kasus Baru Kusta per 100.000 Penduduk': '#9575cd',
                    'Jumlah Kasus Penyakit - Angka Kesakitan Malaria per 1.000 Penduduk': '#7986cb',
                    'Jumlah Kasus Penyakit - Angka Kesakitan DBD per 100.000 Penduduk': '#ff8a65'
                }
                
                # Buat figure stacked bar chart
                fig_bar = go.Figure()
                
                for penyakit in df_pivot.columns:
                    short_name = penyakit.replace('Jumlah Kasus Penyakit - ', '')
                    fig_bar.add_trace(go.Bar(
                        name=short_name,
                        x=df_pivot.index,
                        y=df_pivot[penyakit],
                        marker_color=colors.get(penyakit, '#cccccc'),
                        hovertemplate='%{x}<br>' + short_name + ': %{y:,}<extra></extra>'
                    ))
                
                # Update layout
                fig_bar.update_layout(
                    barmode='stack',
                    title=dict(
                        text=f'Kasus Penyakit Tahun {selected_year}',
                        font=dict(size=20, family='Poppins, sans-serif', color='#044335'),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=dict(
                        title='',
                        tickangle=-45,
                        tickfont=dict(size=11, family='Poppins, sans-serif')
                    ),
                    yaxis=dict(
                        title=dict(
                            text='Jumlah Kasus',
                            font=dict(size=14, family='Poppins, sans-serif')  # Ubah titlefont menjadi title.font
                        ),
                        tickfont=dict(size=12, family='Poppins, sans-serif')
                    ),
                    legend=dict(
                        orientation='v',
                        yanchor='top',
                        y=1,
                        xanchor='left',
                        x=1.02,
                        font=dict(size=10, family='Poppins, sans-serif'),
                        bgcolor='rgba(255,255,255,0.8)'
                    ),
                    plot_bgcolor='rgba(245,245,245,0.5)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=60, r=200, t=80, b=120),
                    height=500,
                    font=dict(family='Poppins, sans-serif')
                )
                
                # Render dalam card putih
                bar_html = f"""
                <div style="background-color: #ffffff; border-radius: 15px; padding: 10px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; 
                            box-sizing: border-box; margin-top: 1px;">
                    <style>
                        .plotly-graph-div, .js-plotly-plot {{ 
                            font-family: 'Poppins', sans-serif !important; 
                            background-color: transparent !important; 
                            width:100% !important; 
                            height:auto !important; 
                        }}
                    </style>
                    {fig_bar.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>
                """
                
                components.html(bar_html, height=540, scrolling=False)
                
        except Exception as e:
            st.error(f"Gagal membuat chart kasus penyakit: {e}")
            import traceback
            st.error(traceback.format_exc())
           
        # === Stacked Bar Chart: Tenaga Kesehatan per Wilayah ===
        try:
            # Query data tenaga kesehatan per wilayah
            query_workforce = """
            SELECT
                id_wilayah,
                id_tenaga,
                nama_tenaga_kerja,
                SUM(COALESCE(total_tenaga_kerja,0)) AS total_tenaga_kerja
            FROM mart_annual_workforce_summary
            WHERE id_tahun = ?
            GROUP BY id_wilayah, id_tenaga, nama_tenaga_kerja
            ORDER BY id_wilayah
            """
            
            # Mapping id_tahun ke tahun
            year_to_id = {
                2017: 1,
                2018: 2,
                2019: 3,
                2020: 4,
                2022: 5,
                2023: 6,
                2024: 7,
                2021: 8
            }
            
            # Mapping id_wilayah ke nama wilayah
            wilayah_mapping = {
                1: 'Tanah Laut',
                2: 'Kota Baru',
                3: 'Banjar',
                4: 'Barito Kuala',
                5: 'Tapin',
                6: 'Hulu Sungai Selatan',
                7: 'Hulu Sungai Tengah',
                8: 'Hulu Sungai Utara',
                9: 'Tabalong',
                10: 'Balangan',
                11: 'Kota Banjarmasin',
                12: 'Kota Banjar Baru'
            }
            
            id_tahun = year_to_id.get(selected_year, 7)  # Default 2024
            
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_workforce = pd.read_sql_query(query_workforce, conn, params=(id_tahun,))
            
            if not df_workforce.empty:
                # Map id_wilayah ke nama wilayah
                df_workforce['nama_wilayah'] = df_workforce['id_wilayah'].map(wilayah_mapping)
                
                # Pivot data untuk stacked bar chart
                df_pivot_workforce = df_workforce.pivot(
                    index='nama_wilayah', 
                    columns='nama_tenaga_kerja', 
                    values='total_tenaga_kerja'
                ).fillna(0)
                
                # Definisi warna untuk setiap jenis tenaga kesehatan
                workforce_colors = {
                    'Tenaga Kesehatan - Dokter': '#64b5f6',
                    'Tenaga Kesehatan - Perawat': '#ffb74d',
                    'Tenaga Kesehatan - Bidan': '#4dd0e1',
                    'Tenaga Kesehatan - Tenaga Kefarmasian': '#e57373',
                    'Tenaga Kesehatan - Tenaga Gizi': '#ba68c8',
                    'Tenaga Kesehatan - Tenaga Kesehatan Masyarakat': '#999999',
                    'Tenaga Kesehatan - Tenaga Kesehatan Lingkungan': '#9575cd',
                    'Tenaga Kesehatan - Ahli Teknologi Laboratorium Medik': '#a1887f',
                    'Jumlah Tenaga Medis': '#2d5016',
                    'Jumlah Tenaga Kesehatan Psikologi Klinis': '#f06292',
                    'Jumlah Tenaga Keterapian Fisik': '#90a4ae',
                    'Jumlah Tenaga Keteknisan Medis': '#4dd0e1',
                    'Jumlah Tenaga Teknik Biomedika': '#ffb300',
                    'Jumlah Tenaga Kesehatan Tradisional': '#7986cb'
                }
                
                # Buat figure stacked bar chart
                fig_workforce = go.Figure()
                
                for tenaga in df_pivot_workforce.columns:
                    short_name = tenaga.replace('Tenaga Kesehatan - ', '').replace('Jumlah ', '')
                    fig_workforce.add_trace(go.Bar(
                        name=short_name,
                        x=df_pivot_workforce.index,
                        y=df_pivot_workforce[tenaga],
                        marker_color=workforce_colors.get(tenaga, '#cccccc'),
                        hovertemplate='%{x}<br>' + short_name + ': %{y:,}<extra></extra>'
                    ))
                
                # Update layout
                fig_workforce.update_layout(
                    barmode='stack',
                    title=dict(
                        text=f'Tenaga Kesehatan Tahun {selected_year}',
                        font=dict(size=20, family='Poppins, sans-serif', color='#044335'),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=dict(
                        title='',
                        tickangle=-45,
                        tickfont=dict(size=11, family='Poppins, sans-serif')
                    ),
                    yaxis=dict(
                        title=dict(
                            text='Jumlah Tenaga Kesehatan',
                            font=dict(size=14, family='Poppins, sans-serif')
                        ),
                        tickfont=dict(size=12, family='Poppins, sans-serif')
                    ),
                    legend=dict(
                        orientation='v',
                        yanchor='top',
                        y=1,
                        xanchor='left',
                        x=1.02,
                        font=dict(size=10, family='Poppins, sans-serif'),
                        bgcolor='rgba(255,255,255,0.8)'
                    ),
                    plot_bgcolor='rgba(245,245,245,0.5)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=60, r=250, t=80, b=120),
                    height=500,
                    font=dict(family='Poppins, sans-serif')
                )
                
                # Render dalam card putih
                workforce_html = f"""
                <div style="background-color: #ffffff; border-radius: 15px; padding: 20px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; 
                            box-sizing: border-box; margin-top: 10px;">
                    <style>
                        .plotly-graph-div, .js-plotly-plot {{ 
                            font-family: 'Poppins', sans-serif !important; 
                            background-color: transparent !important; 
                            width:100% !important; 
                            height:auto !important; 
                        }}
                    </style>
                    {fig_workforce.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>
                """
                
                components.html(workforce_html, height=560, scrolling=False)
                
        except Exception as e:
            st.error(f"Gagal membuat chart tenaga kesehatan: {e}")
            import traceback
            st.error(traceback.format_exc())
            
        # === Scatter Plot Korelasi ===
        try:
            # Query data untuk scatter plot
            query_corr = """
            SELECT
                nama_wilayah,
                SUM(COALESCE(total_workforce, 0)) AS total_workforce,
                SUM(COALESCE(total_cases, 0)) AS total_cases
            FROM mart_workload_ratio
            WHERE tahun = ?
            GROUP BY nama_wilayah
            """
            
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_corr = pd.read_sql_query(query_corr, conn, params=(selected_year,))

            # Pastikan ada cukup data untuk korelasi
            if len(df_corr) < 3:
                st.warning(f"Tidak cukup data wilayah (hanya {len(df_corr)}) untuk menghitung korelasi yang bermakna pada tahun {selected_year}.")
            else:
                # Hitung korelasi
                correlation = df_corr['total_workforce'].corr(df_corr['total_cases'])
                
                # Interpretasi korelasi
                if abs(correlation) < 0.3:
                    interpretation = "Lemah"
                elif 0.3 <= abs(correlation) <= 0.7:
                    interpretation = "Sedang"
                else:
                    interpretation = "Kuat"

                # Buat scatter plot
                fig_corr = px.scatter(
                    df_corr,
                    x='total_workforce',
                    y='total_cases',
                    text='nama_wilayah',
                    trendline='ols',
                    trendline_color_override='#ff6b6b'
                )

                # Update traces untuk styling
                fig_corr.update_traces(
                    marker=dict(color='#4dd0e1', size=12),
                    textposition='top center',
                    textfont=dict(family='Poppins, sans-serif', size=10)
                )

                # Update layout
                fig_corr.update_layout(
                    title=dict(
                        text=f"Korelasi Tenaga Kesehatan vs Kasus ({selected_year})",
                        font=dict(size=20, family='Poppins, sans-serif', color='#044335'),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis_title="Total Tenaga Kesehatan",
                    yaxis_title="Total Kasus Penyakit",
                    height=500,
                    plot_bgcolor='rgba(245,245,245,0.5)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Poppins, sans-serif'),
                    margin=dict(l=60, r=40, t=80, b=80),
                    annotations=[
                        dict(
                            x=0.98,
                            y=0.98,
                            xref='paper',
                            yref='paper',
                            text=f"<b>Korelasi (r): {correlation:.2f}</b><br><i>({interpretation})</i>",
                            showarrow=False,
                            align='right',
                            bgcolor='rgba(255, 255, 255, 0.8)',
                            bordercolor='#044335',
                            borderwidth=1,
                            font=dict(family='Poppins, sans-serif')
                        )
                    ]
                )

                # Render dalam card putih
                corr_html = f"""
                <div style="background-color: #ffffff; border-radius: 15px; padding: 20px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; 
                            box-sizing: border-box; margin-top: 20px;">
                    <style>
                        .plotly-graph-div, .js-plotly-plot {{ font-family: 'Poppins', sans-serif !important; }}
                    </style>
                    {fig_corr.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>
                """
                components.html(corr_html, height=540, scrolling=False)

        except Exception as e:
            st.error(f"Gagal membuat scatter plot korelasi: {e}")
            st.error(traceback.format_exc())
        
    # === Kolom Kanan (sekitar 30% layar) ===                          
    with right_col:        
        # === Card Kabupaten/Kota dengan Dropdown dan Peta ===
        try:
            # Data koordinat untuk setiap wilayah di Kalimantan Selatan
            koordinat_wilayah = {
                'Tanah Laut': {'lat': -3.8333, 'lon': 115.1667, 'zoom': 9},
                'Kota Baru': {'lat': -3.2833, 'lon': 116.1500, 'zoom': 9},
                'Banjar': {'lat': -3.3167, 'lon': 115.0000, 'zoom': 9},
                'Barito Kuala': {'lat': -3.0667, 'lon': 114.6667, 'zoom': 9},
                'Tapin': {'lat': -2.8667, 'lon': 115.1333, 'zoom': 9},
                'Hulu Sungai Selatan': {'lat': -2.6167, 'lon': 115.2167, 'zoom': 9},
                'Hulu Sungai Tengah': {'lat': -2.6000, 'lon': 115.4000, 'zoom': 9},
                'Hulu Sungai Utara': {'lat': -2.5000, 'lon': 115.1667, 'zoom': 9},
                'Tabalong': {'lat': -1.8833, 'lon': 115.4333, 'zoom': 9},
                'Balangan': {'lat': -2.2833, 'lon': 115.6333, 'zoom': 9},
                'Kota Banjarmasin': {'lat': -3.3194, 'lon': 114.5908, 'zoom': 11},
                'Kota Banjar Baru': {'lat': -3.4544, 'lon': 114.8378, 'zoom': 11}
            }
            
            # Mapping nama wilayah ke id
            wilayah_to_id = {v: k for k, v in wilayah_mapping.items()}
            
            # Dropdown untuk memilih wilayah
            col1, col2 = st.columns([2, 1.3])
            with col1:
                st.markdown("""
                        <div style="background-color: #044335; border-radius: 15px 15px 0 0; padding: 20px 25px 15px 25px; margin-right: -199px; margin-bottom: -20px;">
                            <h4 style="color: white; font-family: Poppins; margin: 0; padding: 0;">Kabupaten/Kota</h4>
                        </div>
                    """, unsafe_allow_html=True
                    )
            with col2:
                st.markdown(
                    """
                    <style>
                    /* Styling untuk selectbox */
                    div[data-testid="stSelectbox"] > div > div {
                        background-color: white !important;
                        color: grey !important;
                        border-radius: 10px !important;
                        border: none !important;
                        margin-left: -20px !important;
                    }
                    
                    /* Input field selectbox */
                    div[data-testid="stSelectbox"] input {
                        color: grey !important;
                    }
                    
                    /* Selected value */
                    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
                        background-color: white !important;
                        color: grey !important;
                    }
                    
                    /* Dropdown arrow */
                    div[data-testid="stSelectbox"] svg {
                        fill: grey !important;
                    }
                    
                    /* Dropdown menu popup */
                    div[data-baseweb="popover"] {
                        background-color: white !important;
                    }
                    
                    div[data-baseweb="popover"] ul {
                        background-color: white !important;
                    }
                    
                    div[data-baseweb="popover"] li {
                        background-color: white !important;
                        color: grey !important;
                    }
                    
                    div[data-baseweb="popover"] li:hover {
                        background-color: #00776b !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                selected_wilayah = st.selectbox(
                    "Pilih Wilayah",
                    options=["Semua Wilayah"] + list(koordinat_wilayah.keys()),
                    index=1,  # Default ke tahun terbaru
                    key='selected_wilayah',
                    label_visibility='collapsed'
                )
                       
            # MODIFIKASI: Heat Map Beban Kerja
            id_wilayah_selected = wilayah_to_id.get(selected_wilayah, 3)
            id_tahun = year_to_id.get(selected_year, 7)
            
            # Query total kasus untuk wilayah terpilih
            query_wilayah_cases = """
            SELECT SUM(COALESCE(total_cases,0)) AS total_cases
            FROM mart_annual_case_summary
            WHERE tahun = ? AND nama_wilayah = ?
            """
            
            # Query total tenaga untuk wilayah terpilih
            query_wilayah_workforce = """
            SELECT SUM(COALESCE(total_tenaga_kerja,0)) AS total_workforce
            FROM mart_annual_workforce_summary
            WHERE id_tahun = ? AND id_wilayah = ?
            """
            
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_wilayah_cases = pd.read_sql_query(
                    query_wilayah_cases, 
                    conn, 
                    params=(selected_year, selected_wilayah)
                )
                df_wilayah_workforce = pd.read_sql_query(
                    query_wilayah_workforce, 
                    conn, 
                    params=(id_tahun, id_wilayah_selected)
                )
            
            total_cases_wilayah = int(df_wilayah_cases['total_cases'].iloc[0]) if not df_wilayah_cases.empty else 0
            total_workforce_wilayah = int(df_wilayah_workforce['total_workforce'].iloc[0]) if not df_wilayah_workforce.empty else 0
            
            # Query data beban kerja untuk semua wilayah (untuk heatmap)
            query_all_workload = """
            SELECT 
                nama_wilayah,
                SUM(COALESCE(total_workforce, 0)) as total_workforce,
                SUM(COALESCE(total_cases, 0)) as total_cases
            FROM mart_workload_ratio
            WHERE tahun = ?
            GROUP BY nama_wilayah
            """
            with sqlite3.connect(MART_DB_FILE) as conn:
                df_all_workload = pd.read_sql_query(query_all_workload, conn, params=(selected_year,))

            # Buat dictionary untuk lookup data beban kerja
            workload_data = {row['nama_wilayah']: row for _, row in df_all_workload.iterrows()}

            # Tentukan pusat peta
            if selected_wilayah == "Semua Wilayah":
                map_center = [-2.9, 115.4]  # Pusat Kalimantan Selatan
                map_zoom = 8
            else:
                coords = koordinat_wilayah[selected_wilayah]
                map_center = [coords['lat'], coords['lon']]
                map_zoom = coords['zoom']
            
            # Inisialisasi peta dengan zoom ke Kalimantan Selatan
            m = folium.Map(
                location=map_center,
                zoom_start=map_zoom,
                tiles='OpenStreetMap',
                scrollWheelZoom=False,
                dragging=True
            )
            
            # Tambahkan marker dan circle untuk setiap wilayah
            for wilayah, coords in koordinat_wilayah.items():
                data = workload_data.get(wilayah)
                lat, lon = coords['lat'], coords['lon']
                
                if data is not None and data['total_workforce'] > 0:
                    cases = data['total_cases']
                    workforce = data['total_workforce']
                    rasio_beban = cases / workforce

                    # Klasifikasi status dan warna
                    if rasio_beban <= 8:
                        status = "RENDAH"
                        icon_color = 'green'
                        fill_color = '#4ade80'
                        emoji = "🟢"
                    elif rasio_beban <= 12:
                        status = "SEDANG"
                        icon_color = 'orange'
                        fill_color = '#fbbf24'
                        emoji = "🟡"
                    else:
                        status = "TINGGI"
                        icon_color = 'red'
                        fill_color = '#ef4444'
                        emoji = "🔴"
                    
                    # Tambahkan Circle Marker (Heatmap)
                    folium.Circle(
                        location=[lat, lon],
                        radius=rasio_beban * 1000, # Scaling factor
                        color=fill_color,
                        fill=True,
                        fill_opacity=0.3,
                        stroke=False
                    ).add_to(m)

                else: # Jika data tidak ada atau workforce = 0
                    cases, workforce, rasio_beban = 0, 0, 0
                    status = "Data Tidak Tersedia"
                    icon_color = 'gray'
                    emoji = "⚪"

                # Buat popup
                popup_html = f"""
                <b>{wilayah}</b><br>
                Kasus: {int(cases):,}<br>
                Tenaga: {int(workforce):,}<br>
                Rasio: {rasio_beban:.1f}:1<br>
                Status: {emoji} {status}
                """
                
                # Tambahkan Marker Ikon
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=wilayah,
                    icon=folium.Icon(color=icon_color, icon='info-sign')
                ).add_to(m)
            
            # Tambahkan Legenda di bawah peta
            st.markdown(
                """
                <div style="background-color: black; padding: 10px; 
                            box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: -10px;
                            font-family: 'Poppins', sans-serif; font-size: 0.8rem;">
                    <h5 style="margin: 0 0 5px 0; color: white; text-align: center;">Legenda Beban Kerja</h5>
                    <div style="display: flex; justify-content: space-around;">
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <span style="color: #4ade80; font-size: 1.5rem;">●</span> Rendah (≤ 8:1)
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <span style="color: #fbbf24; font-size: 1.5rem;">●</span> Sedang (8-12:1)
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <span style="color: #ef4444; font-size: 1.5rem;">●</span> Tinggi (> 12:1)
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
            # Render peta
            st_folium(m, width=None, height=300, returned_objects=[])
            
            # Tampilkan peta dalam card putih
            st.markdown(
                """
                <div style="background-color: white; padding: 15px; margin-top: -35px; 
                            box-shadow: 0 8px 20px rgba(0,0,0,0.12); ">
                """,
                unsafe_allow_html=True
            )
                        
            # Card informasi statistik
            st.markdown(
                f"""
                <div style="background-color: #044335; border-radius: 0px 0px 15px 15px; padding: 20px; margin-top: -15px; margin-bottom: 15px;
                            box-shadow: 0 8px 20px rgba(0,0,0,0.12);">
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="background-color: #4dd0e1; width: 25px; height: 25px; 
                                        border-radius: 50%; display: flex; align-items:center; 
                                        justify-content: left; flex-shrink: 0; ">
                                <span style="font-size: 4px;"></span>
                            </div>
                            <div style="text-align: left;">
                                <div style="color: white; font-size: 1rem; font-weight: bold; 
                                            font-family: 'Poppins', sans-serif;">
                                    {total_cases_wilayah:,}
                                </div>
                                <div style="color: #ffb74d; font-size: 0.9rem; font-family: 'Poppins', sans-serif; margin-top: -6px;">
                                    Kasus Penyakit
                                </div>
                            </div>
                        </div>                                            
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="background-color: #7e57c2; width: 25px; height: 25px; 
                                        border-radius: 50%; display: flex; align-items: center; 
                                        justify-content: center; flex-shrink: 0;">
                                <span style="font-size: 4px;"></span>
                            </div>
                            <div style="text-align: left;">
                                <div style="color: white; font-size: 1rem; font-weight: bold; 
                                            font-family: 'Poppins', sans-serif;">
                                    {total_workforce_wilayah:,}
                                </div>
                                <div style="color: #ffb74d; font-size: 0.9rem; font-family: 'Poppins', sans-serif; margin-top: -6px;">
                                    Tenaga Kesehatan
                                </div>
                            </div>
                        </div>                        
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
         
            # ===  Pie Chart Kategori (Kasus Penyakit atau Tenaga Kesehatan) ===
            st.markdown(
                """
                <div style="position: relative; min-height: 2px;">
                    <div style="background-color: white; border-radius: 15px; padding: 2px; 
                                box-shadow: 0 8px 20px rgba(0,0,0,0.12); 
                                position: absolute;top: 0; left: 0; right: 0; 
                                height: 280px; z-index: 0;">
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
                  
            # Dropdown untuk memilih kategori
            col_cat1, col_cat2 = st.columns([1.5, 2])
            with col_cat1:
                st.markdown(
                    '<h4 style="color: #044335; font-family: Poppins; margin-left: 15px; padding-top: 15px;">Kategori</h4>',
                    unsafe_allow_html=True
                )
            with col_cat2:
                st.markdown(
                    """
                    <style>
                    /* Kurangi padding selectbox */
                    div[data-testid="stSelectbox"] {
                        margin-bottom: -1px !important;
                    }
                    /* Border selectbox */
                    div[data-testid="stSelectbox"] > div > div {
                        border: 2px solid black !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                kategori_pilihan = st.selectbox(
                    "Pilih Kategori",
                    options=['Kasus Penyakit', 'Tenaga Kesehatan'],
                    index=0,
                    key='kategori_chart',
                    label_visibility='collapsed'
                )
                
            # Query dan visualisasi berdasarkan kategori yang dipilih
            if kategori_pilihan == 'Kasus Penyakit':
                # Query untuk detail kasus penyakit per wilayah
                query_pie = """
                SELECT
                    REPLACE(
                        REPLACE(nama_penyakit, 'Jumlah Kasus Penyakit - ', ''),
                        'Jumlah Kasus Penyakit -', ''
                    ) AS nama_penyakit,
                    SUM(COALESCE(total_cases,0)) AS total
                FROM mart_annual_case_summary
                WHERE tahun = ? AND nama_wilayah = ?
                GROUP BY nama_penyakit
                ORDER BY total DESC
                LIMIT 10
                """
                
                with sqlite3.connect(MART_DB_FILE) as conn:
                    df_pie = pd.read_sql_query(
                        query_pie, 
                        conn, 
                        params=(selected_year, selected_wilayah)
                    )
                
                if not df_pie.empty and df_pie['total'].sum() > 0:
                    # Warna untuk pie chart kasus penyakit
                    pie_colors = ['#4dd0e1', '#7e57c2', '#e57373', '#64b5f6', '#ffb74d', 
                                '#ba68c8', '#4db6ac', '#90a4ae', '#f06292', '#fff176']
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=df_pie['nama_penyakit'],
                        values=df_pie['total'],
                        marker=dict(colors=pie_colors[:len(df_pie)]),
                        textinfo='percent',
                        textposition='inside',
                        hovertemplate='%{label}<br>%{value:,} kasus<br>%{percent}<extra></extra>',
                        hole=0
                    )])
                    
                    fig_pie.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation='v',
                            yanchor='middle',
                            y=0.5,
                            xanchor='left',
                            x=1.02,
                            font=dict(color='black', size=10, family='Poppins')
                        ),
                        margin=dict(l=15, r=150, t=10, b=20),
                        height=200,
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Poppins')
                    )
                    
                    st.plotly_chart(fig_pie, width='stretch')
                else:
                    st.info("Tidak ada data kasus penyakit untuk wilayah dan tahun ini.")

            else:  # Tenaga Kesehatan
                # Query untuk detail tenaga kesehatan per wilayah
                query_pie = """
                SELECT
                    REPLACE(
                        REPLACE(nama_tenaga_kerja, 'Tenaga Kesehatan - ', ''),
                        'Tenaga Kesehatan -', ''
                    ) AS nama_tenaga_kerja,
                    SUM(COALESCE(total_tenaga_kerja,0)) AS total
                FROM mart_annual_workforce_summary
                WHERE id_tahun = ? AND id_wilayah = ?
                GROUP BY nama_tenaga_kerja
                ORDER BY total DESC
                LIMIT 10
                """
                
                with sqlite3.connect(MART_DB_FILE) as conn:
                    df_pie = pd.read_sql_query(
                        query_pie, 
                        conn, 
                        params=(id_tahun, id_wilayah_selected)
                    )
                
                if not df_pie.empty and df_pie['total'].sum() > 0:
                    # Warna untuk pie chart tenaga kesehatan
                    pie_colors = ['#64b5f6', '#ffb74d', '#4dd0e1', '#e57373', '#ba68c8', 
                                '#999999', '#9575cd', '#a1887f', '#2d5016', '#f06292']
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=df_pie['nama_tenaga_kerja'],
                        values=df_pie['total'],
                        marker=dict(colors=pie_colors[:len(df_pie)]),
                        textinfo='percent',
                        textposition='inside',
                        hovertemplate='%{label}<br>%{value:,} tenaga<br>%{percent}<extra></extra>',
                        hole=0
                    )])
                    
                    fig_pie.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation='v',
                            yanchor='middle',
                            y=0.5,
                            xanchor='left',
                            x=1.02,
                            font=dict(color='black', size=10, family='Poppins')
                        ),
                        margin=dict(l=15, r=150, t=10, b=20),
                        height=200,
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Poppins')
                    )
                    
                    st.plotly_chart(fig_pie, width='stretch')
                else:
                    st.info("Tidak ada data tenaga kesehatan untuk wilayah dan tahun ini.")
        
            
        except Exception as e:
            st.error(f"Gagal membuat peta wilayah: {e}")
            import traceback
            st.error(traceback.format_exc())
        
        
        # === Card Metrik Beban Kerja ===
        try:
            # Ambil tahun dan wilayah yang dipilih
            selected_year_workload = st.session_state.selected_year
            selected_wilayah_workload = st.session_state.get('selected_wilayah', 'Kota Banjarmasin') # Default jika belum ada

            # Siapkan query berdasarkan pilihan wilayah
            if selected_wilayah_workload == "Semua Wilayah":
                query_workload = """
                SELECT
                    SUM(COALESCE(total_workforce, 0)) AS total_workforce,
                    SUM(COALESCE(total_cases, 0)) AS total_cases
                FROM mart_workload_ratio
                WHERE tahun = ?
                """
                params_workload = (selected_year_workload,)
            else:
                query_workload = """
                SELECT
                    total_workforce,
                    total_cases
                FROM mart_workload_ratio
                WHERE tahun = ? AND nama_wilayah = ?
                """
                params_workload = (selected_year_workload, selected_wilayah_workload)

            with sqlite3.connect(MART_DB_FILE) as conn:
                df_workload = pd.read_sql_query(query_workload, conn, params=params_workload)

            if not df_workload.empty and not df_workload.isnull().all().all():
                total_cases_workload = df_workload['total_cases'].iloc[0]
                total_workforce_workload = df_workload['total_workforce'].iloc[0]

                # Perhitungan Rasio dan Status
                rasio_pasien = total_cases_workload / total_workforce_workload if total_workforce_workload > 0 else 0
                jam_kerja = 40  # Asumsi dari UTS

                if rasio_pasien <= 8:
                    status = "NORMAL"
                    icon_status = "🟢"
                    color_status = "#4ade80"
                elif rasio_pasien <= 12:
                    status = "MODERATE"
                    icon_status = "🟡"
                    color_status = "#fbbf24"
                else:
                    status = "TINGGI"
                    icon_status = "🔴"
                    color_status = "#ef4444"

                rasio_text = f"{rasio_pasien:.1f} : 1" if total_workforce_workload > 0 else "N/A"

                # HTML untuk Card Metrik
                workload_card_html = f"""
                <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%); 
                            border-radius: 15px; padding: 25px; margin-top: 10px;
                            box-shadow: 0 8px 20px rgba(0,0,0,0.12); display: flex; 
                            font-family: 'Poppins', sans-serif; gap: 10px;">
                    <!-- Kolom 1: Rasio Pasien per Nakes -->
                    <div style="flex: 1; display: flex; align-items: center; gap: 10px;">                        
                        <div>
                            <div style="color: #ffb74d; font-size: 1.5rem; font-weight: bold;">{rasio_text}</div>
                            <div style="color: white; font-size: 0.9rem;">Rasio Pasien per Nakes</div>
                            <div style="color: white; font-size: 0.85rem; opacity: 0.8;">(Ideal: 6:1)</div>
                        </div>
                    </div>

                    <!-- Kolom 2: Jam Kerja Rata-rata -->
                    <div style="flex: 1; display: flex; align-items: center; gap: 10px; border-left: 1px solid rgba(255,255,255,0.2); border-right: 1px solid rgba(255,255,255,0.2); padding: 0 15px;">                        
                        <div>
                            <div style="color: #ffb74d; font-size: 1.5rem; font-weight: bold;">{jam_kerja} <span style="font-size: 1rem; font-weight: normal;">jam/minggu</span></div>
                            <div style="color: white; font-size: 0.9rem;">Jam Kerja Rata-rata</div>
                            <div style="color: white; font-size: 0.85rem; opacity: 0.8;">(Standar: 40 jam)</div>
                        </div>
                    </div>

                    <!-- Kolom 3: Status Beban Kerja -->
                    <div style="flex: 1; display: flex; align-items: center; gap: 10px; margin-left: 15px;">                        
                        <div>
                            <div style="font-size: 1.6rem; text-align: center; ">{icon_status}</div>
                            <div style="color: {color_status}; text-align: center; font-size: 1.4rem; font-weight: bold;">{status}</div>
                            <div style="color: white; font-size: 1.1rem; text-align: center;">Status Beban</div>
                        </div>
                    </div>
                </div>
                """
                components.html(workload_card_html, height=140)
            else:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%); 
                                border-radius: 15px; padding: 25px; 
                                box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                                color: white; font-family: 'Poppins', sans-serif; height: 100px; display: flex;
                                align-items: center; justify-content: center;">
                        Data beban kerja tidak tersedia untuk periode atau wilayah ini.
                    </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Gagal membuat Card Metrik Beban Kerja: {e}")
            st.error(traceback.format_exc())
 
        # === Gap Analysis Table ===
        try:
            # Ambil tahun dan wilayah yang dipilih
            selected_year_gap = st.session_state.selected_year
            selected_wilayah_gap = st.session_state.get('selected_wilayah', 'Kota Banjarmasin')

            # Jangan tampilkan jika "Semua Wilayah" dipilih
            if selected_wilayah_gap == "Semua Wilayah":
                st.info("Pilih satu kabupaten/kota untuk melihat analisis kesenjangan.")
            else:
                # 1. Query total kasus untuk menghitung kebutuhan
                query_total_cases = """
                SELECT SUM(COALESCE(total_cases, 0)) AS total_cases
                FROM mart_annual_case_summary
                WHERE tahun = ? AND nama_wilayah = ?
                """
                with sqlite3.connect(MART_DB_FILE) as conn:
                    df_total_cases = pd.read_sql_query(query_total_cases, conn, params=(selected_year_gap, selected_wilayah_gap))

                total_cases_gap = df_total_cases['total_cases'].iloc[0] if not df_total_cases.empty else 0

                if total_cases_gap == 0:
                    st.markdown("""
                        <div style="background-color: white; border-radius: 15px; padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 15px; text-align: center; font-family: 'Poppins', sans-serif; color: #044335;">
                            Tidak ada kasus penyakit yang tercatat untuk periode ini. Analisis kesenjangan tidak dapat dilakukan.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # 2. Query jumlah tenaga kesehatan aktual
                    id_tahun_gap = year_to_id.get(selected_year_gap)
                    id_wilayah_gap = wilayah_to_id.get(selected_wilayah_gap)

                    query_workforce_gap = """
                    SELECT
                        nama_tenaga_kerja,
                        SUM(COALESCE(total_tenaga_kerja, 0)) AS total_aktual
                    FROM mart_annual_workforce_summary
                    WHERE id_tahun = ? AND id_wilayah = ?
                    GROUP BY nama_tenaga_kerja
                    HAVING total_aktual > 0
                    """
                    with sqlite3.connect(MART_DB_FILE) as conn:
                        df_gap = pd.read_sql_query(query_workforce_gap, conn, params=(id_tahun_gap, id_wilayah_gap))

                    if df_gap.empty:
                        st.markdown("""
                            <div style="background-color: white; border-radius: 15px; padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 15px; text-align: center; font-family: 'Poppins', sans-serif; color: #044335;">
                                Data tenaga kesehatan tidak tersedia untuk wilayah ini.
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # 3. Perhitungan Kebutuhan dan Gap
                        total_workforce_aktual = df_gap['total_aktual'].sum()
                        kebutuhan_ideal_total = total_cases_gap / 6
                        
                        # Distribusi kebutuhan ideal proporsional dengan komposisi tenaga kerja aktual
                        df_gap['proporsi'] = df_gap['total_aktual'] / total_workforce_aktual if total_workforce_aktual > 0 else 0
                        df_gap['kebutuhan_ideal'] = df_gap['proporsi'] * kebutuhan_ideal_total
                        df_gap['gap'] = df_gap['total_aktual'] - df_gap['kebutuhan_ideal']

                        # 4. Buat Tabel HTML
                        table_rows_html = ""
                        for _, row in df_gap.iterrows():
                            jenis_tenaga = row['nama_tenaga_kerja'].replace('Tenaga Kesehatan - ', '').replace('Jumlah ', '')
                            jumlah_aktual = f"{int(row['total_aktual']):,} tenaga"
                            gap_value = int(round(row['gap']))

                            if gap_value < 0:
                                gap_color = "#ef4444" # Merah
                                gap_text = f"{gap_value:,}"
                            elif gap_value > 0:
                                gap_color = "#4ade80" # Hijau
                                gap_text = f"+{gap_value:,}"
                            else:
                                gap_color = "#999999" # Abu-abu
                                gap_text = "0"

                            table_rows_html += f"""
                            <tr>
                                <td>{jenis_tenaga}</td>
                                <td style="text-align: right;">{jumlah_aktual}</td>
                                <td style="text-align: right; color: {gap_color}; font-weight: bold;">{gap_text}</td>
                            </tr>
                            """

                        # 5. Buat Footer Card
                        total_gap = int(round(df_gap['gap'].sum()))
                        if total_gap < 0:
                            footer_bg = "#ef4444"
                            footer_text = f"🔴 Kekurangan Total: {abs(total_gap):,} tenaga"
                        else:
                            footer_bg = "#4ade80"
                            footer_text = f"🟢 Surplus Total: {total_gap:,} tenaga"

                        # 6. Gabungkan semua menjadi satu card HTML
                        gap_analysis_html = f"""
                        <div style="background-color: white; border-radius: 15px; padding: 20px; 
                                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 15px;
                                    font-family: 'Poppins', sans-serif;">
                            <h4 style="color: #044335; margin-top: 0; margin-bottom: 15px; font-weight: bold;">
                                📋 Gap Analisis - {selected_wilayah_gap}
                            </h4>
                            <div style="max-height: 250px; overflow-y: auto;">
                                <table style="width: 100%; border-collapse: collapse;">
                                    <thead>
                                        <tr>
                                            <th style="background-color: #044335; color: white; padding: 10px; text-align: left; font-weight: bold;">Jenis Tenaga</th>
                                            <th style="background-color: #044335; color: white; padding: 10px; text-align: right; font-weight: bold;">Aktual</th>
                                            <th style="background-color: #044335; color: white; padding: 10px; text-align: right; font-weight: bold;">Gap</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {table_rows_html}
                                    </tbody>
                                </table>
                            </div>
                            <div style="background-color: {footer_bg}; color: white; text-align: center;
                                        padding: 10px; border-radius: 0 0 10px 10px; margin: 15px -20px -20px -20px;
                                        font-weight: bold;">
                                {footer_text}
                            </div>
                        </div>
                        """
                        
                        # Hitung tinggi dinamis
                        row_height = 40
                        header_height = 40
                        padding_height = 40
                        footer_height = 40
                        dynamic_height = (len(df_gap) * row_height) + header_height + padding_height + footer_height
                        max_height = 380 # Batas tinggi maksimum

                        components.html(gap_analysis_html, height=min(dynamic_height, max_height))

        except Exception as e:
            st.error(f"Gagal membuat tabel Gap Analysis: {e}")
            st.error(traceback.format_exc())

        
            st.markdown(
                """
                <div class="dashboard-container card-kabkota">
                    <p class="card-title">Kab/Kota</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# --- FUNGSI UNTUK DASHBOARD UI/UX ---

def render_user_behavior_metrics():
    """Render user behavior metrics"""
    try:
        query = """
        SELECT
            date,
            total_sessions,
            total_clicks,
            bounce_rate,
            avg_session_duration_sec,
            avg_clicks_per_session
        FROM mart_user_behavior
        ORDER BY date DESC
        LIMIT 30
        """

        with sqlite3.connect(MART_DB_FILE) as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            st.markdown("""
            <div style="background-color: #044335; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: 'Poppins', sans-serif;">
                <h4>📊 Belum ada data user behavior</h4>
                <p>Silakan gunakan dashboard utama untuk mulai tracking aktivitas pengguna.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Display raw data for debugging
        st.write("### Debug: Raw Data from mart_user_behavior")
        st.dataframe(df)

        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Sessions", f"{df['total_sessions'].iloc[0]:,}")
        with col2:
            st.metric("Bounce Rate", f"{df['bounce_rate'].iloc[0]:.1f}%")
        with col3:
            st.metric("Avg Duration", f"{df['avg_session_duration_sec'].iloc[0]:.0f}s")
        with col4:
            st.metric("Avg Clicks", f"{df['avg_clicks_per_session'].iloc[0]:.1f}")

        # Trend charts
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['total_sessions'],
            name='Sessions',
            line=dict(color='#4dd0e1')
        ))
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['bounce_rate'],
            name='Bounce Rate (%)',
            line=dict(color='#ef4444'),
            yaxis='y2'
        ))

        fig.update_layout(
            title='User Behavior Trend (Last 30 Days)',
            yaxis=dict(title='Sessions'),
            yaxis2=dict(title='Bounce Rate (%)', overlaying='y', side='right'),
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="black"),
            legend=dict(bgcolor='rgba(255,255,255,0.8)')
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading user behavior metrics: {e}")
        st.warning("Pastikan tabel 'mart_user_behavior' ada di database dan berisi data.")
        import traceback
        st.code(traceback.format_exc())

def render_click_path_analysis():
    """Render Click Path Analysis dengan data dari mart_click_path"""
    try:
        # Query data click path
        query = """
        SELECT
            path_sequence,
            frequency,
            avg_completion_time_sec,
            success_rate
        FROM mart_click_path
        ORDER BY frequency DESC
        LIMIT 20
        """

        with sqlite3.connect(MART_DB_FILE) as conn:
            df_paths = pd.read_sql_query(query, conn)

        if df_paths.empty:
            st.markdown("""
            <div style="background-color: #044335; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: 'Poppins', sans-serif;">
                <h4>🔍 Belum ada data Click Path</h4>
                <p>Data akan muncul setelah pengguna berinteraksi dengan dashboard.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Header
        st.markdown("""
        <div style="background-color: #044335; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
            <h4 style="margin: 0;">🔍 Analisis Jalur Klik Pengguna</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Urutan klik yang paling sering dilakukan pengguna</p>
        </div>
        """, unsafe_allow_html=True)

        # Metrics cards
        col1, col2, col3 = st.columns(3)
        with col1:
            total_paths = len(df_paths)
            st.metric("Total Jalur Unik", f"{total_paths:,}")
        with col2:
            avg_freq = df_paths['frequency'].mean()
            st.metric("Rata-rata Frekuensi", f"{avg_freq:.1f}")
        with col3:
            max_freq = df_paths['frequency'].max()
            st.metric("Frekuensi Tertinggi", f"{max_freq:,}")

        # Bar chart untuk top paths
        fig = go.Figure()

        # Ambil top 10 untuk chart
        top_paths = df_paths.head(10).copy()
        top_paths['short_path'] = top_paths['path_sequence'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x)

        fig.add_trace(go.Bar(
            x=top_paths['frequency'],
            y=top_paths['short_path'],
            orientation='h',
            marker_color='#4dd0e1',
            hovertemplate='<b>%{y}</b><br>Frekuensi: %{x}<extra></extra>'
        ))

        fig.update_layout(
            title='Top 10 Jalur Klik Terpopuler',
            xaxis_title='Frekuensi',
            yaxis_title='Jalur Klik',
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="black", family='Poppins'),
            margin=dict(l=200, r=20, t=50, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Tabel detail
        st.markdown('<h5 style="color: #044335; font-family: Poppins;">Detail Jalur Klik</h5>', unsafe_allow_html=True)

        # Format data untuk tabel
        df_display = df_paths.copy()
        df_display['path_sequence'] = df_display['path_sequence'].apply(lambda x: x.replace(' → ', ' →<br>'))
        df_display['avg_completion_time_sec'] = df_display['avg_completion_time_sec'].round(1)
        df_display['success_rate'] = df_display['success_rate'].round(1)

        # Rename columns
        df_display.columns = ['Jalur Klik', 'Frekuensi', 'Waktu Selesai (detik)', 'Tingkat Keberhasilan (%)']

        # Display sebagai table dengan HTML
        table_html = f"""
        <div style="background-color: white; border-radius: 15px; padding: 20px; 
                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 10px;
                    font-family: 'Poppins', sans-serif; max-height: 400px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #044335; color: white;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Jalur Klik</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Frekuensi</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Waktu Selesai</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Keberhasilan</th>
                    </tr>
                </thead>
                <tbody>
        """

        for _, row in df_display.iterrows():
            table_html += f"""
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; text-align: left; font-size: 0.9em;">{row['Jalur Klik']}</td>
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: #044335;">{row['Frekuensi']:,}</td>
                        <td style="padding: 10px; text-align: center;">{row['Waktu Selesai (detik)']}s</td>
                        <td style="padding: 10px; text-align: center;">{row['Tingkat Keberhasilan (%)']}%</td>
                    </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        components.html(table_html, height=450, scrolling=True)

    except Exception as e:
        st.error(f"Error loading click path analysis: {e}")
        st.warning("Pastikan tabel 'mart_click_path' ada di database dan berisi data.")
        import traceback
        st.code(traceback.format_exc())

def render_error_analysis():
    """Render Error Analysis dengan data dari mart_element_performance"""
    try:
        # Query data error analysis
        query = """
        SELECT
            element_name,
            total_interactions,
            error_count,
            error_rate,
            avg_dwell_time_sec
        FROM mart_element_performance
        ORDER BY error_rate DESC, total_interactions DESC
        LIMIT 20
        """

        with sqlite3.connect(MART_DB_FILE) as conn:
            df_errors = pd.read_sql_query(query, conn)

        if df_errors.empty:
            st.markdown("""
            <div style="background-color: #044335; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: 'Poppins', sans-serif;">
                <h4>⚠️ Belum ada data Error Analysis</h4>
                <p>Data akan muncul setelah pengguna berinteraksi dengan dashboard.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Header
        st.markdown("""
        <div style="background-color: #044335; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
            <h4 style="margin: 0;">⚠️ Analisis Error & Performa Elemen</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Tingkat error dan performa setiap elemen UI</p>
        </div>
        """, unsafe_allow_html=True)

        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_elements = len(df_errors)
            st.metric("Total Elemen", f"{total_elements:,}")
        with col2:
            avg_error_rate = df_errors['error_rate'].mean()
            st.metric("Rata-rata Error", f"{avg_error_rate:.1f}%")
        with col3:
            max_error_rate = df_errors['error_rate'].max()
            st.metric("Error Tertinggi", f"{max_error_rate:.1f}%")
        with col4:
            avg_dwell = df_errors['avg_dwell_time_sec'].mean()
            st.metric("Rata-rata Dwell Time", f"{avg_dwell:.1f}s")

        # Bar chart untuk error rates
        fig = go.Figure()

        # Ambil top 10 error-prone elements
        top_errors = df_errors.head(10).copy()

        fig.add_trace(go.Bar(
            x=top_errors['error_rate'],
            y=top_errors['element_name'],
            orientation='h',
            marker_color='#ef4444',
            hovertemplate='<b>%{y}</b><br>Error Rate: %{x:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title='Top 10 Elemen dengan Error Tertinggi',
            xaxis_title='Error Rate (%)',
            yaxis_title='Elemen UI',
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="black", family='Poppins'),
            margin=dict(l=200, r=20, t=50, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Scatter plot: Error Rate vs Dwell Time
        fig_scatter = go.Figure()

        fig_scatter.add_trace(go.Scatter(
            x=df_errors['avg_dwell_time_sec'],
            y=df_errors['error_rate'],
            mode='markers+text',
            text=df_errors['element_name'],
            textposition="top center",
            marker=dict(
                size=df_errors['total_interactions']/df_errors['total_interactions'].max()*20 + 10,
                color='#4dd0e1',
                sizemode='diameter'
            ),
            hovertemplate='<b>%{text}</b><br>Dwell Time: %{x:.1f}s<br>Error Rate: %{y:.1f}%<extra></extra>'
        ))

        fig_scatter.update_layout(
            title='Korelasi Error Rate vs Dwell Time',
            xaxis_title='Average Dwell Time (seconds)',
            yaxis_title='Error Rate (%)',
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="black", family='Poppins'),
            showlegend=False
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        # Tabel detail
        st.markdown('<h5 style="color: #044335; font-family: Poppins;">Detail Performa Elemen</h5>', unsafe_allow_html=True)

        # Format data untuk tabel
        df_display = df_errors.copy()
        df_display['total_interactions'] = df_display['total_interactions'].apply(lambda x: f"{x:,}")
        df_display['error_count'] = df_display['error_count'].apply(lambda x: f"{x:,}")
        df_display['error_rate'] = df_display['error_rate'].apply(lambda x: f"{x:.1f}%")
        df_display['avg_dwell_time_sec'] = df_display['avg_dwell_time_sec'].apply(lambda x: f"{x:.1f}s")

        # Rename columns
        df_display.columns = ['Elemen UI', 'Total Interaksi', 'Jumlah Error', 'Tingkat Error', 'Rata-rata Dwell Time']

        # Display sebagai table dengan HTML
        table_html = f"""
        <div style="background-color: white; border-radius: 15px; padding: 20px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 10px;
                    font-family: 'Poppins', sans-serif; max-height: 400px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #044335; color: white;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Elemen UI</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Total Interaksi</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Jumlah Error</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Tingkat Error</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Dwell Time</th>
                    </tr>
                </thead>
                <tbody>
        """

        for _, row in df_display.iterrows():
            table_html += f"""
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; text-align: left; font-size: 0.9em;">{row['Elemen UI']}</td>
                        <td style="padding: 10px; text-align: center;">{row['Total Interaksi']}</td>
                        <td style="padding: 10px; text-align: center; color: #ef4444; font-weight: bold;">{row['Jumlah Error']}</td>
                        <td style="padding: 10px; text-align: center; color: #ef4444;">{row['Tingkat Error']}</td>
                        <td style="padding: 10px; text-align: center;">{row['Rata-rata Dwell Time']}</td>
                    </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        components.html(table_html, height=450, scrolling=True)

    except Exception as e:
        st.error(f"Error loading error analysis: {e}")
        st.warning("Pastikan tabel 'mart_element_performance' ada di database dan berisi data.")
        import traceback
        st.code(traceback.format_exc())

def render_funnel_analysis():
    """Render Funnel Analysis dengan data dari mart_funnel"""
    try:
        query = """
        SELECT step_name, step_order, user_count, dropout_rate
        FROM mart_funnel
        WHERE date = DATE('now')
        ORDER BY step_order
        """

        with sqlite3.connect(MART_DB_FILE) as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            st.markdown("""
            <div style="background-color: #044335; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: 'Poppins', sans-serif;">
                <h4>🎯 Belum ada data Funnel Analysis</h4>
                <p>Data akan muncul setelah pengguna berinteraksi dengan dashboard.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Header
        st.markdown("""
        <div style="background-color: #044335; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
            <h4 style="margin: 0;">🎯 Analisis Funnel Pengguna</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Alur langkah-langkah pengguna dalam dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        total_users = df['user_count'].max()
        completion_rate = (df['user_count'].iloc[-1] / df['user_count'].iloc[0] * 100) if df['user_count'].iloc[0] > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", f"{total_users:,}")
        with col2:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        with col3:
            avg_dropout = df['dropout_rate'].mean()
            st.metric("Avg Dropout Rate", f"{avg_dropout:.1f}%")

        # Funnel chart
        fig = go.Figure(go.Funnel(
            y = df['step_name'],
            x = df['user_count'],
            textinfo = "value+percent initial",
            marker = {"color": ["#4dd0e1", "#7e57c2", "#e57373", "#64b5f6", "#ffb74d"]}
        ))

        fig.update_layout(
            title='User Funnel',
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="black", family='Poppins')
        )

        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.markdown('<h5 style="color: #044335; font-family: Poppins;">Detail Funnel Steps</h5>', unsafe_allow_html=True)

        df_display = df.copy()
        df_display['user_count'] = df_display['user_count'].apply(lambda x: f"{x:,}")
        df_display['dropout_rate'] = df_display['dropout_rate'].apply(lambda x: f"{x:.1f}%")
        df_display.columns = ['Step Name', 'Order', 'User Count', 'Dropout Rate']

        table_html = f"""
        <div style="background-color: white; border-radius: 15px; padding: 20px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 10px;
                    font-family: 'Poppins', sans-serif; max-height: 300px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #044335; color: white;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Step</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Users</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Dropout Rate</th>
                    </tr>
                </thead>
                <tbody>
        """

        for _, row in df_display.iterrows():
            table_html += f"""
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; text-align: left;">{row['Step Name']}</td>
                        <td style="padding: 10px; text-align: center; font-weight: bold;">{row['User Count']}</td>
                        <td style="padding: 10px; text-align: center; color: #ef4444;">{row['Dropout Rate']}</td>
                    </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        components.html(table_html, height=350, scrolling=True)

    except Exception as e:
        st.error(f"Error loading funnel analysis: {e}")
        st.warning("Pastikan tabel 'mart_funnel' ada di database dan berisi data.")
        import traceback
        st.code(traceback.format_exc())

def render_usability_score():
    """Render Usability Score dengan data dari mart_usability_score"""
    try:
        # Query data usability score terbaru
        query = """
        SELECT
            date,
            task_completion_rate,
            avg_time_on_task_sec,
            error_rate,
            usability_score
        FROM mart_usability_score
        ORDER BY date DESC
        LIMIT 1
        """

        with sqlite3.connect(MART_DB_FILE) as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            st.markdown("""
            <div style="background-color: #044335; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: 'Poppins', sans-serif;">
                <h4>📊 Belum ada data Usability Score</h4>
                <p>Data akan muncul setelah pengguna berinteraksi dengan dashboard.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Ambil data terbaru
        latest = df.iloc[0]
        score = latest['usability_score']
        completion = latest['task_completion_rate']
        time_on_task = latest['avg_time_on_task_sec']
        error_rate = latest['error_rate']
        date = latest['date']

        # Header
        st.markdown("""
        <div style="background-color: #044335; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
            <h4 style="margin: 0;">⭐ Usability Score Dashboard</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Skor kegunaan sistem berdasarkan interaksi pengguna</p>
        </div>
        """, unsafe_allow_html=True)

        # Main Score Card
        score_color = "#4ade80" if score >= 80 else "#fbbf24" if score >= 60 else "#ef4444"
        score_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%);
                    border-radius: 15px; padding: 30px; margin-bottom: 20px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                    font-family: 'Poppins', sans-serif;">
            <div style="font-size: 4rem; margin-bottom: 10px;">{score_emoji}</div>
            <div style="color: #ffb74d; font-size: 3rem; font-weight: bold;">{score:.1f}</div>
            <div style="color: white; font-size: 1.2rem;">Usability Score</div>
            <div style="color: #ffb74d; font-size: 0.9rem; margin-top: 5px;">Data per {date}</div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics Cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="background-color: white; border-radius: 15px; padding: 20px;
                        box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                        font-family: 'Poppins', sans-serif;">
                <div style="color: #044335; font-size: 2rem; font-weight: bold;">{completion:.1f}%</div>
                <div style="color: #666; font-size: 0.9rem;">Task Completion Rate</div>
                <div style="color: #044335; font-size: 0.8rem; margin-top: 5px;">Tingkat penyelesaian tugas</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background-color: white; border-radius: 15px; padding: 20px;
                        box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                        font-family: 'Poppins', sans-serif;">
                <div style="color: #044335; font-size: 2rem; font-weight: bold;">{time_on_task:.1f}s</div>
                <div style="color: #666; font-size: 0.9rem;">Avg Time on Task</div>
                <div style="color: #044335; font-size: 0.8rem; margin-top: 5px;">Rata-rata waktu penyelesaian</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background-color: white; border-radius: 15px; padding: 20px;
                        box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                        font-family: 'Poppins', sans-serif;">
                <div style="color: #044335; font-size: 2rem; font-weight: bold;">{error_rate:.1f}%</div>
                <div style="color: #666; font-size: 0.9rem;">Error Rate</div>
                <div style="color: #044335; font-size: 0.8rem; margin-top: 5px;">Tingkat kesalahan pengguna</div>
            </div>
            """, unsafe_allow_html=True)

        # Formula Explanation
        st.markdown("""
        <div style="background-color: white; border-radius: 15px; padding: 20px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 20px;
                    font-family: 'Poppins', sans-serif;">
            <h5 style="color: #044335; margin-top: 0;">📐 Formula Perhitungan</h5>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 10px;">
                <div style="font-family: monospace; color: #044335; line-height: 1.6;">
                    Usability Score = (Completion Rate × 0.5) + (Time Efficiency × 0.3) + ((100 - Error Rate) × 0.2)<br><br>
                    <strong>Dimana:</strong><br>
                    • Completion Rate = Tingkat penyelesaian tugas (0-100%)<br>
                    • Time Efficiency = Efisiensi waktu (100% jika ≤30s, turun linear sampai 0% di 120s)<br>
                    • Error Rate = Tingkat kesalahan (0-100%)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading usability score: {e}")
        st.warning("Pastikan tabel 'mart_usability_score' ada di database dan berisi data.")
        import traceback
        st.code(traceback.format_exc())

def generate_dummy_data():
    """Generate dummy data for demonstration purposes (Laporan Bab 4)"""
    try:
        with sqlite3.connect(MART_DB_FILE) as conn:
            cursor = conn.cursor()
            
            # 1. User Behavior
            cursor.execute("DELETE FROM mart_user_behavior")
            dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(30)]
            for date in dates:
                sessions = random.randint(50, 200)
                cursor.execute("""
                    INSERT INTO mart_user_behavior (date, total_sessions, total_clicks, bounce_rate, avg_session_duration_sec, avg_clicks_per_session)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date, sessions, sessions * random.randint(3, 10), random.uniform(20, 60), random.uniform(60, 300), random.uniform(2, 8)))

            # 2. Click Path
            cursor.execute("DELETE FROM mart_click_path")
            paths = [
                ("dashboard_main → filter_year → chart_trend", 150),
                ("dashboard_main → map_click → detail_view", 120),
                ("dashboard_main → tab_uiux → filter_date", 80),
                ("dashboard_main → scatter_plot → hover_info", 60),
                ("dashboard_main → filter_region → map_zoom", 45)
            ]
            for path, freq in paths:
                cursor.execute("""
                    INSERT INTO mart_click_path (path_sequence, frequency, avg_completion_time_sec, success_rate)
                    VALUES (?, ?, ?, ?)
                """, (path, freq, random.uniform(5, 15), random.uniform(80, 100)))

            # 3. Element Performance
            cursor.execute("DELETE FROM mart_element_performance")
            elements = ["button_refresh", "dropdown_year", "map_marker", "tab_analytics", "chart_bar"]
            for el in elements:
                interactions = random.randint(100, 500)
                errors = int(interactions * random.uniform(0.01, 0.05))
                cursor.execute("""
                    INSERT INTO mart_element_performance (element_name, total_interactions, error_count, error_rate, avg_dwell_time_sec)
                    VALUES (?, ?, ?, ?, ?)
                """, (el, interactions, errors, (errors/interactions)*100, random.uniform(1, 5)))

            # 4. Funnel
            cursor.execute("DELETE FROM mart_funnel")
            steps = [("Visit Dashboard", 1), ("Interact with Filter", 2), ("View Details", 3), ("Complete Analysis", 4)]
            users = 1000
            for step, order in steps:
                cursor.execute("""
                    INSERT INTO mart_funnel (step_name, step_order, user_count, dropout_rate, date)
                    VALUES (?, ?, ?, ?, DATE('now'))
                """, (step, order, users, random.uniform(10, 30)))
                users = int(users * 0.7)

            # 5. Usability Score
            cursor.execute("DELETE FROM mart_usability_score")
            cursor.execute("""
                INSERT INTO mart_usability_score (date, task_completion_rate, avg_time_on_task_sec, error_rate, usability_score)
                VALUES (DATE('now'), ?, ?, ?, ?)
            """, (random.uniform(80, 95), random.uniform(30, 60), random.uniform(1, 5), random.uniform(70, 90)))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Gagal membuat data dummy: {e}")
        return False

def render_uiux_dashboard():
    """Render dashboard UI/UX metrics"""
    st.markdown('<h2 style="color: white;">📊 UI/UX Performance Dashboard</h2>', unsafe_allow_html=True)
    
    # Toggle Mode Demo untuk Laporan
    demo_mode = st.toggle("🔴 Mode Demonstrasi (Data Dummy untuk Laporan)", value=False)

    if demo_mode:
        st.warning("⚠️ Mode Demonstrasi Aktif: Tracking asli dinonaktifkan. Gunakan tombol di bawah untuk mengisi dashboard dengan data simulasi.")
        if st.button("🎲 Generate Data Simulasi (Isi Dashboard)"):
            with st.spinner("Sedang membuat data simulasi..."):
                if generate_dummy_data():
                    st.success("Data simulasi berhasil dibuat! Dashboard telah diperbarui.")
                    time.sleep(1)
                    st.rerun()
    else:
        # --- MODE DATA ASLI (REAL-TIME) ---
        if etl_uiux_metrics:
            # Jalankan ETL otomatis saat halaman dibuka untuk memproses data baru dari API
            with st.spinner("Mengupdate Data Mart dari Tracking Asli..."):
                try:
                    etl_uiux_metrics.main_etl_uiux()
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    st.toast(f"Data tracking asli diperbarui: {current_time}", icon="✅")
                except Exception as e:
                    st.error(f"Gagal update data: {e}")
        else:
            st.error("Modul ETL (etl_uiux_metrics) tidak ditemukan. Pastikan file etl_scripts ada.")
        
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            if st.button("🔄 Refresh Halaman"):
                st.cache_data.clear()
                st.rerun()
        with col_info:
            st.info("Mode Tracking Asli aktif. Pastikan **Server API (Port 5001)** sedang berjalan di terminal terpisah agar data interaksi terekam.")

    # Tombol untuk refresh manual, jika diperlukan.
    # Tab selector
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 User Behavior",
        "🔍 Click Path",
        "⚠️ Error Analysis",
        "🎯 Funnel",
        "⭐ Usability Score"
    ])

    with st.expander("🔧 Info Debugging Database (Cek Update Data)"):
        st.write(f"**Lokasi Database:** `{MART_DB_FILE}`")
        if MART_DB_FILE.exists():
            stat = MART_DB_FILE.stat()
            st.write(f"**Ukuran File:** {stat.st_size / 1024:.2f} KB")
            
            # PERBAIKAN: Ganti file modification time dengan timestamp data terbaru
            try:
                with sqlite3.connect(MART_DB_FILE) as conn:
                    cursor = conn.cursor()
                    
                    # Query timestamp terbaru dari data tracking
                    cursor.execute("SELECT MAX(timestamp) FROM fact_user_interaction")
                    latest_timestamp = cursor.fetchone()[0]
                    
                    if latest_timestamp:
                        st.write(f"**Terakhir Update (Data Terbaru):** {latest_timestamp}")
                    else:
                        st.write(f"**Terakhir Update (Data Terbaru):** Belum ada data tracking")
                    
                    # Cek jumlah data di tabel Fact (Data Mentah)``
                    count_interactions = cursor.execute("SELECT COUNT(*) FROM fact_user_interaction").fetchone()[0]
                    count_sessions = cursor.execute("SELECT COUNT(*) FROM fact_session").fetchone()[0]
                    st.write(f"**Total Interaksi (Fact):** {count_interactions:,} baris")
                    st.write(f"**Total Sesi (Fact):** {count_sessions:,} baris")
            except Exception as e:
                st.error(f"Gagal membaca database: {e}")
        else:
            st.error("⚠️ File database tidak ditemukan di path tersebut.")
            
    with tab1:
        render_user_behavior_metrics()
    with tab2:
        render_click_path_analysis()
    with tab3:
        render_error_analysis()
    with tab4:
        render_funnel_analysis()
    with tab5:
        render_usability_score()
# Inject tracking (taruh di akhir, setelah semua UI render)
components.html(inject_tracking_script(), height=0)
# --- JALANKAN APLIKASI ---
if __name__ == "__main__":
    # Cukup panggil fungsi main_app yang sekarang sudah mengontrol navigasi  
    
    main_app()