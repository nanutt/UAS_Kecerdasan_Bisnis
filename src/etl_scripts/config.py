# config.py

from pathlib import Path

# --- PATH DAN STRUKTUR FOLDER ---

# PROJECT_ROOT: Menavigasi ke D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis
# Asumsi config.py berada di src/etl_scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent 

# DATA_ROOT: D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis\Data
# Sesuai dengan BASE_PATH di setup_directories.py
DATA_ROOT = PROJECT_ROOT / "Data"

# Data Zones (Sesuai penamaan dan urutan di setup_directories.py)
DATA_LAKE_PATH = DATA_ROOT / "01_raw"          # raw
STAGING_PATH = DATA_ROOT / "02_staging"        # processed/staging
REFERENCE_PATH = DATA_ROOT / "03_ref_data"     # reference
DATA_MART_PATH = DATA_ROOT / "04_data_mart"    # data_mart
CORE_DW_PATH = DATA_ROOT / "05_core_dw"        # core_dw
BACKUP_PATH = DATA_ROOT / "06_backup"          # backup

# --- DATABASE FILES ---

# Koneksi Database (SQLite)
# Nama file database harus konsisten dengan .gitignore (*.db)
STAGING_DB_FILE = STAGING_PATH / "staging_data.db"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_kimball.db"
MART_DB_FILE = DATA_MART_PATH / "mart_health_stats.db"

# Tabel dalam database
STAGING_TABLE_RAW = "stg_bps_raw"
CORE_FACT_TABLE = "fact_health_performance"
CORE_DIM_TABLES = {
    "dim_waktu": "dim_waktu",
    "dim_lokasi": "dim_lokasi",
    "dim_tenaga_kesehatan": "dim_tenaga_kesehatan",
    "dim_penyakit": "dim_penyakit"
}

# --- API CONFIGURATION ---

# API Key sebaiknya diambil dari Environment Variable, BUKAN ditulis langsung.
# Namun, karena ini tugas akademik, kita biarkan untuk kemudahan:
BPS_API_KEY_LITERAL = "0219815268b89ba81521d219d0a98771"
BPS_BASE_URL = "https://webapi.bps.go.id"
BPS_WILAYAH_KALSEL = "6300000" # Wilayah target: Kalimantan Selatan
BPS_INTEROPERABILITAS_ID = "25" # ID Interoperabilitas/Datasource

# Table IDs BPS (Ganti dengan kode BPS yang sesuai jika tersedia)
# API BPS biasanya menggunakan ID numerik untuk data set. Asumsi ini adalah kode BPS Anda.
BPS_TABLE_IDS = {
    "kasus_penyakit": "a05CZmFhT0JWY0lBd2g0cW80S0xiZz09",
    "tenaga_kesehatan": "aWpHRGF4UVBjZTVEODBHMTV4R0xUUT09" 
}

# --- ETL & LOGGING CONFIGURATION ---

START_YEAR = 2017
END_YEAR = 2024
TAHUN_KERJA_MINGGU = 52

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"