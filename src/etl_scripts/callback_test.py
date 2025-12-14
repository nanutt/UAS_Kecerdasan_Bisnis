import pandas as pd
import sqlite3
import numpy as np
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
import shutil
from datetime import datetime

# --- IMPORT FUNGSI CALLBACK DARI MODUL LAIN ---
# Import log_status_callback untuk mencatat hasil
from callback_functions import log_status_callback, setup_log_table

# --- KONFIGURASI JALUR DATA DAN DB ---

# Pathing Relatif (Asumsi script berada di src/etl_scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Staging Sources (Asumsi Output Transformasi)
STAGING_PATH = DATA_ROOT / "02_staging"
PENYAKIT_DB_FILE = STAGING_PATH / "stg_kasus_penyakit.db"
TENAGA_DB_FILE = STAGING_PATH / "stg_tenaga_kesehatan.db"

# Target Database (Core DW/Mart) - Menggunakan 07_Test
CORE_DW_PATH = DATA_ROOT / "07_Test"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_test.db"
CORE_DW_PATH.mkdir(parents=True, exist_ok=True)

# Backup Path
BACKUP_PATH = DATA_ROOT / "06_backup"
BACKUP_PATH.mkdir(parents=True, exist_ok=True)

# Koneksi SQLAlchemy untuk Core DW/Mart
CORE_DW_ENGINE = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")


# --- FUNGSI CORE ETL (Sama seperti drp_test.py) ---

def load_data_from_staging():
    """Membaca data dari dua Staging DB yang terpisah dan menggabungkannya (dengan dummy data jika tidak ada)."""
    df_list = []

    def read_db(db_file, data_type):
        if db_file.exists():
            try:
                engine = create_engine(f'sqlite:///{db_file}')
                table_name = db_file.stem
                print(f"Membaca data {data_type} dari DB: {db_file.name}, Tabel: {table_name}")
                df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
                df['Jenis_Data'] = data_type
                return df
            except Exception as e:
                print(f"❌ ERROR: Gagal membaca {data_type} dari DB ({db_file.name}): {e}")
                return pd.DataFrame()
        else:
            # Menggunakan dummy data jika file staging tidak ditemukan
            print(f"⚠️ Peringatan: File DB {db_file.name} tidak ditemukan. Menggunakan dummy data.")
            if data_type == 'Kasus Penyakit':
                return pd.DataFrame({
                    'Kode_Wilayah': ['63.03.01', '63.03.02'], 
                    'Nama_Wilayah': ['Banjar', 'Martapura'], 
                    'Tahun': [2023, 2024], 
                    'Jumlah_Clean': [100.0, 150.0],
                    'Nama Kasus Penyakit': ['DBD', 'TBC'],
                    'Jenis_Data': ['Kasus Penyakit', 'Kasus Penyakit']
                })
            else:
                 return pd.DataFrame({
                    'Kode_Wilayah': ['63.03.01'], 
                    'Nama_Wilayah': ['Banjar'], 
                    'Tahun': [2024], 
                    'Jumlah_Clean': [50.0],
                    'Nama Tenaga Kesehatan': ['Dokter Umum'],
                    'Jenis_Data': ['Tenaga Kerja']
                })

    df_penyakit = read_db(PENYAKIT_DB_FILE, 'Kasus Penyakit')
    df_tenaga = read_db(TENAGA_DB_FILE, 'Tenaga Kerja')
    
    df_list = []
    if not df_penyakit.empty: df_list.append(df_penyakit)
    if not df_tenaga.empty: df_list.append(df_tenaga)

    if not df_list:
        print("❌ ERROR: Data staging kosong. Proses Load dibatalkan.")
        return pd.DataFrame()

    df_master = pd.concat(df_list, ignore_index=True)
    df_master = df_master.replace({np.nan: None})
    print(f"Data Master digabungkan: {len(df_master)} baris total.")
    return df_master

def create_mart_tables(conn):
    """ Membuat DDL untuk dim_wilayah dan dim_tahun."""
    tables_to_drop = [
        'dim_wilayah', 'dim_tahun'
    ]

    cursor = conn.cursor()
    print("Membuat DDL untuk dim_wilayah dan dim_tahun...")
    
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
    conn.commit()

    # Dimension Table: dim_wilayah
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_wilayah (
            id_wilayah INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_wilayah VARCHAR(20) NOT NULL UNIQUE,
            nama_wilayah TEXT
        );
    """)

    # Dimension Table: dim_tahun
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_tahun (
            id_tahun INTEGER PRIMARY KEY AUTOINCREMENT,
            tahun INTEGER
        );
    """)
    conn.commit()


def load_dimensions(engine, df_master):
    """ Mengisi tabel dimensi yang dipilih: dim_wilayah dan dim_tahun."""
    print("\n--- Memuat Dimension Tables ---")

    # 1. dim_wilayah
    df_wilayah = df_master[['Kode_Wilayah', 'Nama_Wilayah']].drop_duplicates().dropna(subset=['Kode_Wilayah'])
    df_wilayah = df_wilayah.rename(columns={'Kode_Wilayah': 'kode_wilayah', 'Nama_Wilayah': 'nama_wilayah'})
    df_wilayah['kode_wilayah'] = df_wilayah['kode_wilayah'].astype(str)
    df_wilayah.to_sql('dim_wilayah', engine, if_exists='replace', index=False)
    print(f"dim_wilayah dimuat: {len(df_wilayah)} baris.")

    # 2. dim_tahun
    df_tahun = df_master[['Tahun']].drop_duplicates().dropna()
    df_tahun = df_tahun.rename(columns={'Tahun': 'tahun'})
    df_tahun['tahun'] = df_tahun['tahun'].astype(int)
    df_tahun.to_sql('dim_tahun', engine, if_exists='replace', index=False)
    print(f"dim_tahun dimuat: {len(df_tahun)} baris.")


# --- FUNGSI UTAMA DENGAN DRP DAN CALLBACK ---

def main_load_process():
    """
    Fungsi utama yang mencakup DRP Backup dan Explicit Success/Error Callback.
    """
    
    # --- START TIMER ---
    start_time = datetime.now()
    # --- START TIMER ---

    print("\n=======================================================")
    print("      🛠️ MEMULAI CALLBACK TEST LOAD PROCESS             ")
    print("=======================================================")

    # 1. EXTRACT: Load Data dari Staging DBs
    df_master = load_data_from_staging()
    rows_loaded = len(df_master)
    
    if df_master.empty:
        # PANGGIL ERROR CALLBACK jika data kosong
        log_status_callback(CORE_DW_ENGINE, 
                            "CALLBACK_TEST_LOAD", 
                            "FAILED", 
                            "Data staging kosong. Load dibatalkan.", 
                            start_time)
        return

    # 2. TRANSFORM & LOAD
    try:
        # 2.1. DRP BACKUP
        if CORE_DW_DB_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"{CORE_DW_DB_FILE.stem}_{timestamp}_backup.db"
            backup_target = BACKUP_PATH / backup_file_name
            
            print(f"\n[DRP] Melakukan Backup DB Lama ke {BACKUP_PATH.name}...")
            try:
                shutil.copy2(CORE_DW_DB_FILE, backup_target)
                print(f"   ✅ Backup berhasil: {backup_file_name}")
                CORE_DW_DB_FILE.unlink()
                print(f"   ✅ File DB lama ({CORE_DW_DB_FILE.name}) dihapus.")
            except Exception as e:
                print(f"   ❌ ERROR DRP: Gagal membuat backup/menghapus. Melanjutkan Load. {e}")

        # 2.2. LOAD DDL & DML
        with sqlite3.connect(CORE_DW_DB_FILE) as conn:
            # Pastikan tabel log dibuat (penting untuk callback)
            setup_log_table(CORE_DW_ENGINE) 
            
            # Buat Struktur Tabel Dimensi
            create_mart_tables(conn)

        # Load Dimensi yang dipilih
        load_dimensions(CORE_DW_ENGINE, df_master)

        print(f"\n✅ Callback Test Load ke Data Warehouse ({CORE_DW_DB_FILE.name}) Selesai!")
        
        # --- SUCCESS CALLBACK ---
        log_status_callback(CORE_DW_ENGINE, 
                            "CALLBACK_TEST_LOAD", 
                            "SUCCESS", 
                            "Load Dimensi, DRP Test, dan Callback berhasil diimplementasikan.", 
                            start_time, 
                            rows_loaded)

    except Exception as e:
        error_msg = f"Fatal Error selama proses ETL: {str(e)}"
        print(f"\n❌ ERROR selama proses Load Callback Test: {error_msg}")
        
        # --- ERROR CALLBACK ---
        log_status_callback(CORE_DW_ENGINE, 
                            "CALLBACK_TEST_LOAD", 
                            "FAILED", 
                            error_msg, 
                            start_time)


# --- JALANKAN PROSES UTAMA ---
if __name__ == "__main__":
    main_load_process()