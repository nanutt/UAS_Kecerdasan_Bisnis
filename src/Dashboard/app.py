import streamlit as st
import pandas as pd
from pathlib import Path
import sqlite3
from dash import Dash, dcc, html, dash_table
import plotly.express as px
import traceback
import streamlit.components.v1 as components

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
    body, .stApp, .card-dashboard, .card-sidebar, .trend-chart-container, .trend-chart-title, .sidebar-title, .item-text {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Buat Sidebar */
    .card-sidebar {
        background-color: #044335; /* Hijau Gelap */
        border-radius: 0px 20px 20px 0px;
        position: fixed;
        width: 17.5%;
        top: 150px;
        left: 0;
        height: calc(100vh - 125px - 5px);
        z-index: 900;
    }
    
    .sidebar-content-wrapper {
        padding: 20px;
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
    .card-sidebar .sidebar-title {
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

    .year-radio-item {
        /* Mirip dengan sidebar-item */
        color: white; 
        margin-bottom: 5px; 
        padding-left: 0; 
    }

    .year-radio-item label {
        display: flex;
        align-items: center;
        cursor: pointer; /* Menunjukkan bahwa seluruh baris dapat diklik */
    }

    .year-radio-item input[type="radio"] {
        /* Mengatur margin dan ukuran radio button */
        margin-right: 15px; 
        width: 1.2rem;
        height: 1.2rem;
        /* Kita bisa menambahkan styling kustom di sini untuk membuatnya terlihat seperti checkbox,
        tetapi untuk saat ini, kita biarkan style default radio button agar fungsinya terlihat jelas. */
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
    .trend-chart-title {
        color: #044335;
        font-size: 1.5rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        margin: 0 0 15px 0;
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
        .trend-chart-title { font-size: 1.2rem; }
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

    # --- Sidebar (separate) ---
    st.markdown(
        """
        <div class="card-sidebar">
            <div class="sidebar-content-wrapper">
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
                <h4 class="sidebar-title">Tahun</h4>
                <ul class="sidebar-list">
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2024"><span class="item-text">2024</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2023"><span class="item-text">2023</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2022"><span class="item-text">2022</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2021"><span class="item-text">2021</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2020"><span class="item-text">2020</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2019"><span class="item-text">2019</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2018"><span class="item-text">2018</span></label></li>
                    <li class="sidebar-item year-radio-item"><label><input type="radio" name="selected_year" value="2017"><span class="item-text">2017</span></label></li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # === LAYOUT RESPONSIF DENGAN KOLOM STREAMLIT ===
    # Buat tiga kolom: spacer (untuk sidebar), kolom grafik (50%), dan kolom kanan untuk Kab/Kota
    left_spacer, chart_col, right_col = st.columns([0.59, 2.4, 1], gap="small")

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
                    # Pastikan kolom numerik
                    df_trend['total_workforce'] = pd.to_numeric(df_trend['total_workforce'], errors='coerce').fillna(0)
                    df_trend['total_cases'] = pd.to_numeric(df_trend['total_cases'], errors='coerce').fillna(0)

                    # Figure: gunakan transformasi pada sumbu Y agar jarak visual antar tick
                    # lebih merata meskipun nilai numerik sangat berbeda (0,100,500,10k,...)
                    custom_ticks = [0, 100, 500, 10000, 15000, 50000, 100000]

                    def transform_value(v, ticks):
                        # Pemetaan piecewise linear ke posisi tertransformasi 0..n-1
                        if v <= ticks[0]:
                            return 0.0
                        for i in range(len(ticks) - 1):
                            t0, t1 = ticks[i], ticks[i+1]
                            if t0 <= v <= t1:
                                return i + (v - t0) / (t1 - t0)
                        # Jika melebihi ticks terakhir, kembalikan posisi terakhir
                        return float(len(ticks) - 1)

                    # Terapkan transformasi pada data
                    df_trend['workforce_trans'] = df_trend['total_workforce'].apply(lambda x: transform_value(x, custom_ticks))
                    df_trend['cases_trans'] = df_trend['total_cases'].apply(lambda x: transform_value(x, custom_ticks))

                    fig = px.line(df_trend, x='tahun', y=['workforce_trans', 'cases_trans'], markers=True)

                    # Styling tiap trace (warna/isi)
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
                    chart_height = num_intervals * px_per_interval + 140
                    fig.update_layout(height=chart_height)

                    min_year = int(df_trend['tahun'].min())
                    max_year = int(df_trend['tahun'].max())
                    x_pad = 0.2  # padding dalam satuan tahun
                    
                    fig.update_xaxes(tickmode='linear', tick0=min_year, dtick=1, range=[min_year - x_pad, max_year + x_pad], title_text='Tahun', title_standoff=10, showgrid=False, zeroline=False)
                    fig.update_yaxes(range=[0, tick_positions[-1]], tickmode='array', tickvals=tick_positions, ticktext=tick_labels, title_text='Jumlah', title_standoff=30)
                    fig.update_layout(margin=dict(l=78, r=20, t=20, b=70))
                    fig.data[0].customdata = df_trend['total_workforce']
                    fig.data[1].customdata = df_trend['total_cases']
                    fig.data[0].hovertemplate = 'Tahun: %{x}<br>Total Tenaga: %{customdata:,}<extra></extra>'
                    fig.data[1].hovertemplate = 'Tahun: %{x}<br>Total Kasus: %{customdata:,}<extra></extra>'                   
                    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')                    
                    card_html = f"""
                    <div style="background-color: #ffffff; border-radius: 8px; padding: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.12); width:100%; box-sizing: border-box;">
                        <h3 style="color:#044335; font-size:1.25rem; margin-left: 20px; font-family: 'Poppins' !important; ">Grafik Tren</h3>
                        <style>
                            /* Pastikan elemen Plotly transparan supaya wrapper putih terlihat */
                            .plotly-graph-div, .js-plotly-plot {{ font-family: 'Poppins'!important; background-color: transparent !important; width:100% !important; height:auto !important; margin:0; }}
                            body {{ background-color: transparent !important; margin:0; padding:0; }}
                        </style>
                        {fig_html}
                    </div>
                    """
                    components.html(card_html, height=chart_height + 80, scrolling=False)
        except Exception as e:
            st.error(f"Gagal membuat grafik tren: {e}")

        # Tutup container HTML
        st.markdown("""
            </div>
            """,
            unsafe_allow_html=True
        )

    # === DIV 2: Kab/Kota (Warna #044335) ===
    with right_col:
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