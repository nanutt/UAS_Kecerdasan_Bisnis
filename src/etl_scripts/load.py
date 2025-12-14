import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, Float, text
import shutil
from datetime import datetime

# --- KONFIGURASI JALUR DATA DAN DB (DISESUAIKAN) ---

# Pathing Relatif
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Staging Sources (Asumsi Output Transformasi)
STAGING_PATH = DATA_ROOT / "02_staging"
PENYAKIT_DB_FILE = STAGING_PATH / "stg_kasus_penyakit.db"
TENAGA_DB_FILE = STAGING_PATH / "stg_tenaga_kesehatan.db"

# Reference Data Source
REFERENCE_DATA_PATH = DATA_ROOT / "03_ref_data"
MANUAL_ASSUMPTION_FILE = REFERENCE_DATA_PATH / "indikator_asumsi.xlsx"

# Target Database (Core DW/Mart)
CORE_DW_PATH = DATA_ROOT / "05_core_dw" # Menggunakan folder 05_core_dw untuk Star Schema
CORE_DW_DB_PATH = CORE_DW_PATH / "core_dw_mart.db" # Nama file database
CORE_DW_PATH.mkdir(parents=True, exist_ok=True) # Pastikan folder target ada

# Backup Path
BACKUP_PATH = DATA_ROOT / "06_backup"
BACKUP_PATH.mkdir(parents=True, exist_ok=True) # Pastikan folder backup ada

TAHUN_KERJA_MINGGU = 52 # Jumlah minggu dalam setahun

# Koneksi SQLAlchemy untuk Core DW/Mart
CORE_DW_ENGINE = create_engine(f"sqlite:///{CORE_DW_DB_PATH}")


# --- FUNGSI UTAMA ---

def load_data_from_staging():
    """Membaca data dari dua Staging DB yang terpisah dan menggabungkannya."""
    df_list = []
    
    # Fungsi pembantu untuk membaca DB
    def read_db(db_file, data_type):
        if db_file.exists():
            try:
                engine = create_engine(f'sqlite:///{db_file}')
                
                # MODIFIKASI: Nama tabel diambil dari stem file (misal: 'stg_kasus_penyakit')
                table_name = db_file.stem 
                
                print(f"Membaca data {data_type} dari DB: {db_file.name}, Tabel: {table_name}")
                df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
                
                # Kolom Jenis_Data harus ada untuk filtering di Dimensi
                df['Jenis_Data'] = data_type 
                return df
            except Exception as e:
                # Menambahkan nama tabel ke pesan error untuk debugging
                print(f"❌ ERROR: Gagal membaca {data_type} dari DB ({table_name}): {e}")
                return pd.DataFrame()
        else:
            print(f"⚠️ Peringatan: File DB {db_file.name} tidak ditemukan.")
            return pd.DataFrame()

    # 1. Load Kasus Penyakit
    df_penyakit = read_db(PENYAKIT_DB_FILE, 'Kasus Penyakit')
    if not df_penyakit.empty:
        df_list.append(df_penyakit)
            
    # 2. Load Tenaga Kesehatan
    df_tenaga = read_db(TENAGA_DB_FILE, 'Tenaga Kerja') # Nama 'Tenaga Kerja' sesuai filtering di kode Anda
    if not df_tenaga.empty:
        df_list.append(df_tenaga)

    if not df_list:
        print("❌ ERROR: Data staging kosong. Proses Load dibatalkan.")
        return pd.DataFrame()

    # Gabungkan (UNION)
    df_master = pd.concat(df_list, ignore_index=True)
    df_master = df_master.replace({np.nan: None}) # Ganti NaN dengan None untuk SQLite
    print(f"Data Master digabungkan: {len(df_master)} baris total.")
    return df_master


def create_mart_tables(conn):
    """ Membuat DDL (Data Definition Language) untuk Dimension dan Fact Tables.
    Menggunakan koneksi sqlite3 untuk eksekusi DDL murni."""
    # --- DDL SCRIPT (TETAP DARI KODE ANDA) ---
    tables_to_drop = [
        'dim_wilayah', 'dim_tahun', 'dim_penyakit', 'dim_tenaga_kesehatan', 
        'dim_indikator_asumsi', 'fact_kesehatan'
    ]

    cursor = conn.cursor()
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
        conn.commit()
    print("Membuat Dimension Tables...")
    
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
    
    # Dimension Table: dim_penyakit
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_penyakit (
            id_penyakit INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_data VARCHAR(50) NOT NULL,
            kasus_penyakit VARCHAR(255)         
        );
    """)

    # Dimension Table: dim_tenaga_kesehatan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_tenaga_kesehatan (
            id_tenaga INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_data VARCHAR(50) NOT NULL,
            tenaga_kerja VARCHAR(20) NOT NULL UNIQUE           
        );
    """)

    # Dimension Table: dim_indikator_asumsi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_indikator_asumsi (
            id_indikator INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_tenaga VARCHAR(100) NOT NULL,
            jam_bekerja_per_minggu INTEGER,
            hari_kerja_per_minggu INTEGER,
            jam_kerja_per_hari INTEGER,
            jam_kerja_per_tahun INTEGER,
            hari_kerja_per_tahun INTEGER,
            waktu_per_pasien_jam REAL,
            kapasitas_pasien_per_hari REAL,
            rasio_pasien_ideal_per_hari REAL,
            sumber_referensi VARCHAR(255)
        );
    """)
    
    # Fact Table: fact_kesehatan
    cursor.execute("""
        CREATE TABLE fact_kesehatan (
            id_fact INTEGER PRIMARY KEY,
            id_wilayah INTEGER,
            id_tahun INTEGER,
            id_penyakit INTEGER,
            id_tenaga INTEGER,
            id_indikator INTEGER,
            jenis_data VARCHAR(50) NOT NULL,
            jumlah DECIMAL (12,2) NOT NULL,
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (id_wilayah) REFERENCES dim_wilayah(id_wilayah),
            FOREIGN KEY (id_tahun) REFERENCES dim_tahun(id_tahun),
            FOREIGN KEY (id_penyakit) REFERENCES dim_penyakit(id_penyakit),
            FOREIGN KEY (id_tenaga) REFERENCES dim_tenaga_kesehatan(id_tenaga),
            FOREIGN KEY (id_indikator) REFERENCES dim_indikator_asumsi(id_indikator)
        );
    """)
    
    conn.commit()
    print("Pembuatan tabel selesai.")


def load_dimensions(engine, df_master):
    """
    Mengisi tabel dimensi dari data master.
    """
    print("\n--- Memuat Dimension Tables ---")
    
    # PASTIKAN FOLDER REFERENCE DATA ADA
    REFERENCE_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    # 1. dim_wilayah
    df_wilayah = df_master[['Kode_Wilayah', 'Nama_Wilayah']].drop_duplicates().dropna(subset=['Kode_Wilayah'])
    df_wilayah = df_wilayah.rename(columns={'Kode_Wilayah': 'kode_wilayah', 'Nama_Wilayah': 'nama_wilayah'})
    df_wilayah['kode_wilayah'] = df_wilayah['kode_wilayah'].astype(str)
    df_wilayah.to_sql('dim_wilayah', engine, if_exists='append', index=False)
    print(f"dim_wilayah dimuat: {len(df_wilayah)} baris.")

    # 2. dim_tahun
    df_tahun = df_master[['Tahun']].drop_duplicates().dropna()
    df_tahun = df_tahun.rename(columns={'Tahun': 'tahun'})
    df_tahun['tahun'] = df_tahun['tahun'].astype(int)
    df_tahun.to_sql('dim_tahun', engine, if_exists='append', index=False)
    print(f"dim_tahun dimuat: {len(df_tahun)} baris.")

    # 3. dim_penyakit
    # Filtering berdasarkan 'Kasus Penyakit'
    df_penyakit = df_master[df_master['Jenis_Data'] == 'Kasus Penyakit'][
        ['Nama Kasus Penyakit']
    ].drop_duplicates().dropna()
    df_penyakit = df_penyakit.rename(columns={'Nama Kasus Penyakit': 'kasus_penyakit'})
    df_penyakit['jenis_data'] = 'Kasus Penyakit'
    df_penyakit = df_penyakit[['jenis_data', 'kasus_penyakit']]
    df_penyakit.to_sql('dim_penyakit', engine, if_exists='append', index=False)
    print(f"dim_penyakit dimuat: {len(df_penyakit)} baris.")

    # 4. dim_tenaga_kesehatan
    # Filtering berdasarkan 'Tenaga Kerja' (Sesuai dengan filtering Anda di atas)
    df_tenaga = df_master[df_master['Jenis_Data'] == 'Tenaga Kerja'][
        ['Nama Tenaga Kesehatan']
    ].drop_duplicates().dropna()
    df_tenaga = df_tenaga.rename(columns={'Nama Tenaga Kesehatan': 'tenaga_kerja'})
    df_tenaga['jenis_data'] = 'Tenaga Kerja'
    df_tenaga = df_tenaga[['jenis_data', 'tenaga_kerja']]
    df_tenaga.to_sql('dim_tenaga_kesehatan', engine, if_exists='append', index=False)
    print(f"dim_tenaga_kesehatan dimuat: {len(df_tenaga)} baris.")

    # 5. dim_indikator_asumsi (Data dari file Excel manual)
    print("\n[INFO] Membaca file indikator_asumsi.xlsx...")
    
    if not MANUAL_ASSUMPTION_FILE.exists():
        print(f"❌ ERROR: File asumsi {MANUAL_ASSUMPTION_FILE.name} TIDAK ditemukan di {REFERENCE_DATA_PATH}. Melewati Dimensi ini.")
        return 
        
    df_asumsi = pd.read_excel(MANUAL_ASSUMPTION_FILE)
    df_asumsi = df_asumsi.drop_duplicates(subset=['jenis_tenaga'], keep='first')
    
    # Konversi dan perhitungan
    df_asumsi['hari_kerja_per_minggu'] = pd.to_numeric(df_asumsi['hari_kerja_per_minggu'], errors='coerce').fillna(5).astype(int)
    df_asumsi['jam_kerja_per_hari'] = pd.to_numeric(df_asumsi['jam_kerja_per_hari'], errors='coerce').fillna(8).astype(int)

    # Clean float value
    if df_asumsi['waktu_per_pasien_jam'].dtype == 'object':
        df_asumsi['waktu_per_pasien_jam'] = df_asumsi['waktu_per_pasien_jam'].astype(str).str.replace(',', '.')
    df_asumsi['waktu_per_pasien_jam'] = pd.to_numeric(df_asumsi['waktu_per_pasien_jam'], errors='coerce').fillna(0.25)
    
    # Hitung kolom turunan
    df_asumsi['jam_bekerja_per_minggu'] = (df_asumsi['hari_kerja_per_minggu'] * df_asumsi['jam_kerja_per_hari'])
    df_asumsi['jam_kerja_per_tahun'] = (df_asumsi['jam_bekerja_per_minggu'] * TAHUN_KERJA_MINGGU)
    df_asumsi['hari_kerja_per_tahun'] = (df_asumsi['hari_kerja_per_minggu'] * TAHUN_KERJA_MINGGU)
    df_asumsi['kapasitas_pasien_per_hari'] = (df_asumsi['jam_kerja_per_hari'] / df_asumsi['waktu_per_pasien_jam']).round(2)
    # Rasio Pasien Ideal: Asumsi Anda adalah rasio per hari. Menggunakan nilai tetap dari Anda.
    df_asumsi['rasio_pasien_ideal_per_hari'] = float(1000.0 / 365) # 2.74 Pasien per hari per 1000 penduduk

    # Rename columns to match table schema
    df_asumsi = df_asumsi.rename(columns={
        'jenis_tenaga': 'jenis_tenaga',
        # Kolom lainnya sudah sesuai atau dihitung ulang
    })

    # Load ke DB (Tidak perlu menambahkan id_indikator secara manual di Pandas, karena di SQLite sudah AUTOINCREMENT)
    # Hapus kolom id_indikator buatan Anda agar SQLite yang mengurus id_indikator
    # if 'id_indikator' in df_asumsi.columns:
    #    df_asumsi = df_asumsi.drop(columns=['id_indikator'])
    
    df_asumsi.to_sql('dim_indikator_asumsi', engine, if_exists='append', index=False)
    print(f"dim_indikator_asumsi dimuat: {len(df_asumsi)} baris.")

def load_fact_table(engine, df_master):
    """
    Mengisi fact_kesehatan dengan menghubungkan data master ke kunci dimensi.
    """
    print("\n--- Memuat Fact Table (fact_kesehatan) ---")
    
    # 1. Ambil Dimensi Keys dari DB yang sudah terisi
    with engine.connect() as conn:
        df_dim_wilayah = pd.read_sql("SELECT id_wilayah, kode_wilayah FROM dim_wilayah", conn)
        df_dim_tahun = pd.read_sql("SELECT id_tahun, tahun FROM dim_tahun", conn)
        df_dim_penyakit = pd.read_sql("SELECT id_penyakit, kasus_penyakit FROM dim_penyakit", conn)
        df_dim_tenaga = pd.read_sql("SELECT id_tenaga, tenaga_kerja FROM dim_tenaga_kesehatan", conn)
        df_dim_indikator = pd.read_sql("SELECT id_indikator, jenis_tenaga FROM dim_indikator_asumsi", conn)

    # Ensure data types match for merging
    df_dim_wilayah['kode_wilayah'] = df_dim_wilayah['kode_wilayah'].astype(str)
    df_dim_tahun['tahun'] = df_dim_tahun['tahun'].astype(int)
    df_dim_penyakit.rename(columns={'kasus_penyakit': 'kode_penyakit'}, inplace=True)
    df_dim_tenaga.rename(columns={'tenaga_kerja': 'kode_tenaga'}, inplace=True)
    df_dim_indikator.rename(columns={'jenis_tenaga': 'kode_indikator'}, inplace=True)
    
    # Ubah kolom kunci pada df_master agar sesuai dengan nama kolom dimensi
    df_master = df_master.rename(columns={
        'Kode_Wilayah': 'kode_wilayah',
        'Tahun': 'tahun',
        'Jumlah_Clean': 'jumlah',
        'Source_File': 'source_file' # Mengubah Source_File menjadi Source_File (tanpa spasi)
    })
    
    # 2. Persiapan Kunci Fact (CRITICAL STEP)
    df_master['kode_wilayah'] = df_master['kode_wilayah'].astype(str)
    df_master['tahun'] = df_master['tahun'].astype(int)

    # Membentuk kunci: hanya satu dari kolom ini yang akan terisi per baris
    df_master['kode_penyakit'] = df_master.apply(
        lambda row: row['Nama Kasus Penyakit'] if row['Jenis_Data'] == 'Kasus Penyakit' else None, axis=1)
    df_master['kode_tenaga'] = df_master.apply(
        lambda row: row['Nama Tenaga Kesehatan'] if row['Jenis_Data'] == 'Tenaga Kerja' else None, axis=1)
    # Indikator asumsi terhubung dengan tenaga kesehatan
    df_master['kode_indikator'] = df_master['kode_tenaga'].copy() 

    # Konversi ke string untuk merge
    df_master['kode_penyakit'] = df_master['kode_penyakit'].apply(lambda x: str(x) if pd.notna(x) else None)
    df_master['kode_tenaga'] = df_master['kode_tenaga'].apply(lambda x: str(x) if pd.notna(x) else None)
    df_master['kode_indikator'] = df_master['kode_indikator'].apply(lambda x: str(x) if pd.notna(x) else None)

    # 3. Melakukan proses Lookup/Merge untuk mendapatkan Foreign Keys (FK)
    df_fact = df_master.copy()

    # Merge Wilayah (Output: id_wilayah)
    df_fact = df_fact.merge(df_dim_wilayah, on='kode_wilayah', how='left').drop(columns=['kode_wilayah'])

    # Merge Tahun (Output: id_tahun)
    df_fact = df_fact.merge(df_dim_tahun, on='tahun', how='left').drop(columns=['tahun'])

    # Merge Penyakit (Output: id_penyakit)
    df_fact = df_fact.merge(df_dim_penyakit, on='kode_penyakit', how='left').drop(columns=['kode_penyakit'])

    # Merge Tenaga Kesehatan (Output: id_tenaga)
    df_fact = df_fact.merge(df_dim_tenaga, on='kode_tenaga', how='left').drop(columns=['kode_tenaga'])

    # Merge Indikator Asumsi (Output: id_indikator)
    df_fact = df_fact.merge(df_dim_indikator, on='kode_indikator', how='left').drop(columns=['kode_indikator'])
    
    # Fill NaN FKs dengan -1 atau 0 (sesuai praktik DW)
    # Catatan: id_penyakit akan null jika datanya adalah Tenaga Kerja, dan sebaliknya
    df_fact['id_penyakit'] = df_fact['id_penyakit'].fillna(0).astype(int)
    df_fact['id_tenaga'] = df_fact['id_tenaga'].fillna(0).astype(int)
    # id_indikator hanya relevan untuk Tenaga Kerja
    df_fact['id_indikator'] = df_fact['id_indikator'].fillna(0).astype(int)

    # 4. Finalisasi kolom fact table
    df_final_fact = df_fact[['id_wilayah', 'id_tahun', 'id_penyakit', 'id_tenaga', 'id_indikator', 'Jenis_Data', 'jumlah', 'source_file']]

    print(f"\n[DEBUG] Fact table siap dimuat: {len(df_final_fact)} baris.")
    
    # 5. Load ke fact_kesehatan
    df_final_fact.to_sql('fact_kesehatan', engine, if_exists='replace', index=False)
    print(f"fact_kesehatan dimuat: {len(df_final_fact)} baris berhasil.")
    

def main_load_process():
    """
    Fungsi utama untuk menjalankan proses ETL (Load) ke Data Warehouse.
    """
    
    # 1. EXTRACT: Load Data dari Staging DBs
    df_master = load_data_from_staging()
    if df_master.empty:
        return

    # 2. TRANSFORM & LOAD
    try:
        # Backup file DB lama jika ada sebelum dihapus
        if CORE_DW_DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"core_dw_mart_backup_{timestamp}.db"
            backup_file_path = BACKUP_PATH / backup_filename
            shutil.copy2(CORE_DW_DB_PATH, backup_file_path)
            print(f"✅ Backup file DB lama dibuat: {backup_file_path}")
            CORE_DW_DB_PATH.unlink()
            print(f"File DB lama ({CORE_DW_DB_PATH.name}) dihapus.")
            
        with sqlite3.connect(CORE_DW_DB_PATH) as conn:
            # A. Buat Struktur Tabel (DDL)
            create_mart_tables(conn)
        
        # B. Load Dimensi
        load_dimensions(CORE_DW_ENGINE, df_master)
        
        # C. Load Fact Table
        load_fact_table(CORE_DW_ENGINE, df_master)
        
        print(f"\n✅ Proses Load ke Data Warehouse ({CORE_DW_DB_PATH.name}) Selesai!")
        
    except Exception as e:
        print(f"\n❌ ERROR selama proses Load: {e}")
        

def main():
    main_load_process()

# --- JALANKAN PROSES UTAMA ---
if __name__ == "__main__":
    main()
