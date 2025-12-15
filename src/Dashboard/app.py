import streamlit as st
import pandas as pd
from pathlib import Path
import sqlite3
from dash import Dash, dcc, html, dash_table
import plotly.express as px
import traceback
import streamlit.components.v1 as components
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

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
        width: 71.5%;
        border-radius: 20px;
        margin-top: 20px;
        background-image: linear-gradient(to right, #00776b, #0B634F, #044335 60%); /* Hijau Gelap */
        display: flex;
        align-items: center;
        background-size: 400% 400%; /* Kunci animasi */
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
        font-size: 2.5rem !important; /* Memaksa Ukuran (32-40px) */
        font-weight: bold !important;
        color: white !important;      /* MEMAKSA WARNA PUTIH */
        margin: 0 !important;         /* Menghilangkan margin bawaan */
        padding: 0 !important;
        line-height: 1.0 !important;
    }

    h4.sub-title { 
        font-size: 1.25rem !important; /* Memaksa Ukuran (20px) */
        font-weight: 500 !important;
        color: #ffb74d !important;    /* MEMAKSA WARNA ORANYE */
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
        top: 150px; /* Jarak dari atas layar */
        width: 327px;    
        height: calc(100vh - 160px); /* Tinggi sidebar, sisakan ruang di bawah */    
        background-color: #044335;    
        border-radius: 0px 20px 20px 0px;    
        padding-top: 10px; /* Kurangi padding karena 'top' sudah diatur */    
    }
    
    
    .sidebar-title {
        color: white; 
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 1rem;
        font-weight: bold;
        font-family: 'Poppins', sans-serif;
    }

    /* Lebih spesifik untuk memastikan style tidak tertimpa oleh Streamlit */
    [data-testid="stSidebar"] .sidebar-title {
        color: #ffffff !important;
    }

    .sidebar-list {
        list-style: none; /* Hapus bullet point bawaan */
        padding: 0;      /* Hapus padding kiri bawaan UL */
        margin: 0;       /* Hapus margin bawaan UL */
        margin-bottom: 20px; /* Tambahkan jarak dari elemen di bawahnya */
        margin-left: 50px; /* Sesuaikan posisi daftar ke kiri */
        font-family: 'Poppins', sans-serif;
    }

    .sidebar-item {
        color: white; 
        margin-bottom: 10px; /* Jarak antar item daftar */
        display: flex; 
        align-items: center;
    }
    
    .item-text {
        color: white;
        font-size: 1rem;
        font-family: 'Poppins';
    }

    /* Styling untuk Ikon Kategori di dalam Li */
    .category-icon {
        font-size: 1.5rem; /* Ukuran ikon dan panah */
        margin-right: 10px;
        font-weight: bold;
    }
    
    /* Styling untuk radio button tahun di sidebar */
    div[role="radiogroup"] {
        padding-left: 35px !important; /* Align with categories */
    }

    /* Style each radio item's label */
    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
        margin-bottom: 10px !important; /* Space between items */
    }

    /* Style the radio input button itself */
    div[role="radiogroup"] input[type="radio"] {
        width: 20px !important;
        height: 20px !important;
        cursor: pointer !important;
        accent-color: #4dd0e1 !important; /* Apply user's desired color */
        margin-right: 15px !important; /* Space between button and text */
    }
    
    /* Buat Grafik tren */
    /* Container Grafik Tren */
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

# Sumber: Data Mart
MART_PATH = DATA_ROOT / "04_data_mart"
MART_DB_FILE = MART_PATH / "mart_health_summary.db"

# --- VERIFIKASI ---
# Cetak path yang dihasilkan untuk memastikan kebenaran sebelum digunakan
print(f"PROJECT_ROOT ditentukan sebagai: {PROJECT_ROOT.resolve()}")
print(f"Path Data Mart yang dihasilkan: {MART_DB_FILE.resolve()}")
 
# --- FUNGSI UTAMA DASHBOARD ---
def main_app():
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
                src="data:image/png;base64,
                alt="Dashboard Icon" 
                style="width: 120px; height: 120px; margin-left: 20px; object-fit: contain; margin-right: 20px;"
            >
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
        st.markdown(
            """
            <h4 class="sidebar-title">Kategori</h4>
            <ul class="sidebar-list">
                <li class="sidebar-item">
                    <span class="category-icon">&gt;</span>
                    <span class="category-icon">👤</span>
                    <span class="item-text">Tenaga Kesehatan</span>
                </li>
                <li class="sidebar-item">
                    <span class="category-icon">&gt;</span>
                    <span class="category-icon">📦</span>
                    <span class="item-text">Kasus Penyakit</span>
                </li>
            </ul>
            """, unsafe_allow_html=True
        )
        st.markdown('<h4 class="sidebar-title" style="padding-left:20px;">Tahun</h4>', unsafe_allow_html=True)
        selected_year = st.radio(
            "Pilih Tahun", 
            options=[2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017],
            index=0,
            key='selected_year',
            label_visibility='collapsed'
        )


    # === LAYOUT RESPONSIF DENGAN KOLOM STREAMLIT ===
    # Buat dua kolom utama, spacer tidak lagi diperlukan karena st.sidebar
    chart_col, right_col = st.columns([2.4, 1], gap="small")

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
                    <div style="background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; box-sizing: border-box; margin-top: 25px;" class="trend-chart-container">
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

        st.markdown('<h3 style="background-color: #DAA520; color: white; text-align: center; border-radius: 10px; padding: 10px; margin-top: 10px;">Analisis Berdasarkan Wilayah</h3>', unsafe_allow_html=True)

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
                                <div style="color: #ffb74d; font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', sans-serif;">
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
                                <div style="color: #ffb74d; font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', sans-serif;">
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
        
                            
    # === DIV 2: Kab/Kota (Warna #044335) ===
    with right_col:
        st.markdown('<div style="margin-top: 150px;"></div>', unsafe_allow_html=True)
        
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
            st.markdown(
                '<h3 style="color: white; font-family: Poppins; margin-bottom: 10px;">Kabupaten/Kota</h3>',
                unsafe_allow_html=True
            )
            
            selected_wilayah = st.selectbox(
                "Pilih Wilayah",
                options=list(koordinat_wilayah.keys()),
                index=2,  # Default Banjar
                key='selected_wilayah',
                label_visibility='collapsed'
            )
            
            # Ambil data untuk wilayah yang dipilih
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
            
            # Ambil koordinat wilayah yang dipilih
            coords = koordinat_wilayah[selected_wilayah]
            
            # Inisialisasi peta dengan zoom ke Kalimantan Selatan
            m = folium.Map(
                location=[coords['lat'], coords['lon']],
                zoom_start=coords['zoom'],
                tiles='OpenStreetMap',
                scrollWheelZoom=False,
                dragging=True
            )
            
            # Tambahkan marker untuk wilayah yang dipilih
            folium.Marker(
                location=[coords['lat'], coords['lon']],
                popup=f"<b>{selected_wilayah}</b><br>Kasus: {total_cases_wilayah:,}<br>Tenaga: {total_workforce_wilayah:,}",
                tooltip=selected_wilayah,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
            # Tampilkan peta dalam card putih
            st.markdown(
                """
                <div style="background-color: white; border-radius: 15px; padding: 15px; 
                            box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin-top: 15px;">
                """,
                unsafe_allow_html=True
            )
            
            # Render peta
            st_folium(m, width=None, height=300, returned_objects=[])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Card informasi statistik
            st.markdown(
                f"""
                <div style="background-color: #720709; border-radius: 15px; padding: 20px; 
                            margin-top: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.12);">
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="text-align: center;">
                            <div style="background-color: #4dd0e1; width: 60px; height: 60px; 
                                        border-radius: 50%; display: flex; align-items: center; 
                                        justify-content: center; margin: 0 auto 10px;">
                                <span style="font-size: 24px;">📊</span>
                            </div>
                            <div style="color: white; font-size: 1.8rem; font-weight: bold; 
                                        font-family: 'Poppins', sans-serif;">
                                {total_cases_wilayah:,}
                            </div>
                            <div style="color: #ffb74d; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
                                Kasus Penyakit
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <div style="background-color: #7e57c2; width: 60px; height: 60px; 
                                        border-radius: 50%; display: flex; align-items: center; 
                                        justify-content: center; margin: 0 auto 10px;">
                                <span style="font-size: 24px;">👨‍⚕️</span>
                            </div>
                            <div style="color: white; font-size: 1.8rem; font-weight: bold; 
                                        font-family: 'Poppins', sans-serif;">
                                {total_workforce_wilayah:,}
                            </div>
                            <div style="color: #ffb74d; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
                                Tenaga Kesehatan
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.error(f"Gagal membuat peta wilayah: {e}")
            import traceback
            st.error(traceback.format_exc())
        
        
            st.markdown(
                """
                <div class="dashboard-container card-kabkota">
                    <p class="card-title">Kab/Kota</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# --- JALANKAN APLIKASI ---
if __name__ == "__main__":
    main_app()