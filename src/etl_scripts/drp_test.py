import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine
import shutil # Diperlukan untuk DRP (copy)
from datetime import datetime # Diperlukan untuk DRP (timestamp)
import sys # Diperlukan untuk exit jika gagal load data staging

# --- KONFIGURASI JALUR DATA DAN DB ---

# Pathing Relatif
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Staging Sources (Asumsi Output Transformasi)
STAGING_PATH = DATA_ROOT / "02_staging"
PENYAKIT_DB_FILE = STAGING_PATH / "stg_kasus_penyakit.db"
TENAGA_DB_FILE = STAGING_PATH / "stg_tenaga_kesehatan.db"

# Target Database (Core DW/Mart) - Menggunakan 07_Test untuk testing DRP
CORE_DW_PATH = DATA_ROOT / "07_Test"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_test.db" # Menggunakan CORE_DW_DB_FILE sebagai Path object
CORE_DW_PATH.mkdir(parents=True, exist_ok=True)

# Backup Path
BACKUP_PATH = DATA_ROOT / "06_backup"
BACKUP_PATH.mkdir(parents=True, exist_ok=True)

# Koneksi SQLAlchemy untuk Core DW/Mart
CORE_DW_ENGINE = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")


# --- FUNGSI LOAD DATA STAGING ---

def load_data_from_staging():
    """Membaca data dari dua Staging DB yang terpisah dan menggabungkannya."""
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
            print(f"⚠️ Peringatan: File DB {db_file.name} tidak ditemukan.")
            return pd.DataFrame()

    df_penyakit = read_db(PENYAKIT_DB_FILE, 'Kasus Penyakit')
    if not df_penyakit.empty:
        df_list.append(df_penyakit)

    df_tenaga = read_db(TENAGA_DB_FILE, 'Tenaga Kerja')
    if not df_tenaga.empty:
        df_list.append(df_tenaga)

    if not df_list:
        print("❌ ERROR: Data staging kosong. Proses Load dibatalkan.")
        # Menghentikan script jika data staging kosong
        sys.exit(1) 

    df_master = pd.concat(df_list, ignore_index=True)
    df_master = df_master.replace({np.nan: None})
    print(f"Data Master digabungkan: {len(df_master)} baris total.")
    return df_master


# --- FUNGSI DDL (Hanya dim_tahun dan dim_wilayah) ---

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
    print("Pembuatan DDL tabel terpilih selesai.")


# --- FUNGSI LOAD DIMENSION (Hanya dim_tahun dan dim_wilayah) ---

def load_dimensions(engine, df_master):
    """
    Mengisi tabel dimensi yang dipilih: dim_wilayah dan dim_tahun.
    Menggunakan if_exists='replace' karena tabel sudah di-DROP di DDL.
    """
    print("\n--- Memuat Dimension Tables ---")

    # 1. dim_wilayah
    df_wilayah = df_master[['Kode_Wilayah', 'Nama_Wilayah']].drop_duplicates().dropna(subset=['Kode_Wilayah'])
    df_wilayah = df_wilayah.rename(columns={'Kode_Wilayah': 'kode_wilayah', 'Nama_Wilayah': 'nama_wilayah'})
    df_wilayah['kode_wilayah'] = df_wilayah['kode_wilayah'].astype(str)
    df_wilayah.to_sql('dim_wilayah', engine, if_exists='replace', index=False) # Menggunakan 'replace'
    print(f"dim_wilayah dimuat: {len(df_wilayah)} baris.")

    # 2. dim_tahun
    df_tahun = df_master[['Tahun']].drop_duplicates().dropna()
    df_tahun = df_tahun.rename(columns={'Tahun': 'tahun'})
    df_tahun['tahun'] = df_tahun['tahun'].astype(int)
    df_tahun.to_sql('dim_tahun', engine, if_exists='replace', index=False) # Menggunakan 'replace'
    print(f"dim_tahun dimuat: {len(df_tahun)} baris.")


# --- FUNGSI UTAMA (Dengan Logika DRP) ---

def main_load_process():
    """
    Fungsi utama untuk menjalankan proses ETL dengan pengujian DRP Backup.
    """
    print("\n=======================================================")
    print("         🛠️ MEMULAI DRP TEST LOAD PROCESS             ")
    print("   Target DB: 07_Test/core_dw_test.db                ")
    print("=======================================================")

    # 1. EXTRACT: Load Data dari Staging DBs
    df_master = load_data_from_staging()
    if df_master.empty:
        # Jika df_master kosong, script sudah dihentikan di load_data_from_staging
        return

    # 2. TRANSFORM & LOAD
    try:
        # 2.1. DRP BACKUP (Mekanisme Pemulihan)
        if CORE_DW_DB_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"{CORE_DW_DB_FILE.stem}_{timestamp}_backup.db"
            backup_target = BACKUP_PATH / backup_file_name
            
            print(f"\n[DRP] Melakukan Backup DB Lama ke {BACKUP_PATH.name}...")
            try:
                # Membuat salinan file database
                shutil.copy2(CORE_DW_DB_FILE, backup_target)
                print(f"   ✅ Backup berhasil: {backup_file_name}")
                
                # Hapus file DB lama sebelum di-load ulang (Full Load Strategy)
                CORE_DW_DB_FILE.unlink()
                print(f"   ✅ File DB lama ({CORE_DW_DB_FILE.name}) dihapus.")
            except Exception as e:
                print(f"   ❌ ERROR DRP: Gagal membuat backup/menghapus. Melanjutkan Load. {e}")
                # Logika DRP menyatakan kita harus berusaha melanjutkan jika backup gagal,
                # tapi ini berisiko kehilangan data lama.

        # 2.2. LOAD DDL & DML
        with sqlite3.connect(CORE_DW_DB_FILE) as conn:
            # A. Buat Struktur Tabel (DDL)
            create_mart_tables(conn)

        # B. Load Dimensi yang dipilih
        load_dimensions(CORE_DW_ENGINE, df_master)

        print(f"\n✅ DRP Test Load ke Data Warehouse ({CORE_DW_DB_FILE.name}) Selesai!")

    except Exception as e:
        print(f"\n❌ ERROR selama proses Load DRP Test: {e}")


# --- JALANKAN PROSES UTAMA ---
if __name__ == "__main__":
    main_load_process()