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
        st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True) # Spacer
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
                src="data:image/png;base64,
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
                    margin=dict(l=60, r=40, t=80, b=60),
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
                <div style="background-color: black; padding: 10px; border-radius: 8px; 
                            box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: -10px;
                            font-family: 'Poppins', sans-serif; font-size: 0.8rem;">
                    <h5 style="margin: 0 0 5px 0; color: #044335; text-align: center;">Legenda Beban Kerja</h5>
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
                <div style="background-color: white; padding: 15px; margin-top: -10px; 
                            box-shadow: 0 8px 20px rgba(0,0,0,0.12); ">
                """,
                unsafe_allow_html=True
            )
                        
            # Card informasi statistik
            st.markdown(
                f"""
                <div style="background-color: #044335; border-radius: 0px 0px 15px 15px; padding: 20px; margin-top: -2px; margin-bottom: 15px;
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
                components.html(workload_card_html, height=180)
            else:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #00776b 0%, #044335 100%); 
                                border-radius: 15px; padding: 25px; margin-top: 20px;
                                box-shadow: 0 8px 20px rgba(0,0,0,0.12); text-align: center;
                                color: white; font-family: 'Poppins', sans-serif; height: 180px; display: flex;
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

def render_uiux_dashboard():
    """Render dashboard UI/UX metrics"""
    st.markdown('<h2 style="color: white;">📊 UI/UX Performance Dashboard</h2>', unsafe_allow_html=True)
    
    # Tab selector
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 User Behavior", 
        "🔍 Click Path", 
        "⚠️ Error Analysis", 
        "🎯 Funnel", 
        "⭐ Usability Score"
    ])
    
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

# --- JALANKAN APLIKASI ---
if __name__ == "__main__":
    # Cukup panggil fungsi main_app yang sekarang sudah mengontrol navigasi  
    
    main_app()