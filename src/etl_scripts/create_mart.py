import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

# --- KONFIGURASI JALUR DATA DAN DB ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Sumber: Core Data Warehouse (Output dari load_dw.py)
CORE_DW_PATH = DATA_ROOT / "05_core_dw"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_mart.db"

# Tujuan: Data Mart (Folder dan File DB baru)
MART_PATH = DATA_ROOT / "04_data_mart"
MART_DB_FILE = MART_PATH / "mart_health_summary.db"
MART_PATH.mkdir(parents=True, exist_ok=True) # Pastikan folder 04_data_mart ada

# Backup Path
BACKUP_PATH = DATA_ROOT / "06_backup"
BACKUP_PATH.mkdir(parents=True, exist_ok=True) # Pastikan folder 06_backup ada

# Engine Koneksi
CORE_DW_ENGINE = create_engine(f'sqlite:///{CORE_DW_DB_FILE}')
#MART_ENGINE = create_engine(f'sqlite:///{MART_DB_FILE}')

# --- FUNGSI PEMBUATAN MART ---

def create_mart_db_schema(conn):
    """
    Membuat struktur tabel (DDL) untuk Data Mart.
    Data Mart hanya berisi tabel hasil agregasi (tanpa dimensi, karena dimensi sudah di Core DW).
    """
    cursor = conn.cursor()
    
    tables_to_drop = [
        'mart_annual_case_summary',
        'mart_annual_workforce_summary',
        'mart_workload_ratio'
    ]

    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
    conn.commit()
    
    print("\n[DDL] Membuat Struktur Tabel Data Mart...")

    # 1. Mart Annual Case Summary (Kasus Penyakit)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_annual_case_summary (
            tahun INTEGER,
            nama_wilayah TEXT,
            nama_penyakit TEXT,
            total_cases DECIMAL (15,2)
        );
    """)

    # 2. Mart Annual Workforce Summary (Tenaga Kesehatan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_annual_workforce_summary (
            id_summary INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tahun INTEGER NOT NULL,
            id_wilayah INTEGER NOT NULL,
            id_tenaga INTEGER NOT NULL,
            nama_tenaga_kerja TEXT,
            total_tenaga_kerja DECIMAL (15,2) NOT NULL
        );
    """)

    # 3. Mart Workload Ratio (Rasio Beban Kerja - Analisis Kebutuhan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_workload_ratio (
            tahun INTEGER,
            nama_wilayah TEXT,
            total_workforce INTEGER,
            total_cases INTEGER,
            workforce_ratio REAL
        );
    """)

    conn.commit()
    print("[DDL] Pembuatan struktur tabel Data Mart selesai.")


def load_mart_annual_case_summary(core_dw_engine, mart_engine):
    """
    Mengagregasi total kasus penyakit per tahun, per wilayah, per jenis penyakit.
    """
    print("\n--- 1. Memuat mart_annual_case_summary ---")

    sql_summary = """
    SELECT
        T.tahun,
        W.nama_wilayah,
        P.kasus_penyakit AS nama_penyakit,
        SUM(F.jumlah) AS total_cases
    FROM fact_kesehatan F
    JOIN dim_tahun T ON F.id_tahun = T.id_tahun
    JOIN dim_wilayah W ON F.id_wilayah = W.id_wilayah
    JOIN dim_penyakit P ON F.id_penyakit = P.id_penyakit
    -- Filter untuk hanya mengambil data Kasus Penyakit
    WHERE F.jenis_data = 'Kasus Penyakit'
    GROUP BY 1, 2, 3;
    """

    try:
        df_summary = pd.read_sql(sql_summary, core_dw_engine)
        df_summary.to_sql('mart_annual_case_summary', mart_engine, if_exists='replace', index=False)
        print(f"✅ mart_annual_case_summary dimuat: {len(df_summary)} baris.")
    except Exception as e:
        print(f"❌ ERROR saat memuat mart_annual_case_summary: {e}")


def load_mart_annual_workforce_summary(core_dw_engine, mart_engine):
    """
    Mengagregasi total tenaga kesehatan per tahun, per wilayah, per jenis tenaga.
    """
    print("\n--- 2. Memuat mart_annual_workforce_summary ---")
    
    sql_summary = """
    SELECT
        F.id_tahun,
        F.id_wilayah,
        F.id_tenaga,
        T.tenaga_kerja AS nama_tenaga_kerja,
        SUM(F.jumlah) AS total_tenaga_kerja
    FROM fact_kesehatan F
    JOIN dim_tenaga_kesehatan T ON F.id_tenaga = T.id_tenaga
    -- Filter untuk hanya mengambil data Tenaga Kerja
    WHERE F.jenis_data = 'Tenaga Kerja'
    GROUP BY 1, 2, 3, 4;
    """
    
    try:
        df_summary = pd.read_sql(sql_summary, core_dw_engine)
        df_summary.to_sql('mart_annual_workforce_summary', mart_engine, if_exists='replace', index=False)
        print(f"✅ mart_annual_workforce_summary dimuat: {len(df_summary)} baris.")
    except Exception as e:
        print(f"❌ ERROR saat memuat mart_annual_workforce_summary: {e}")


def load_mart_workload_ratio(core_dw_engine, mart_engine):
    """
    Membuat ringkasan Rasio Beban Kerja (menggunakan asumsi dari dim_indikator_asumsi).
    Ini adalah contoh perhitungan kompleks di level Mart.
    """
    print("\n--- 3. Memuat mart_workload_ratio ---")

    # SQL untuk menggabungkan fakta (jumlah tenaga) dengan dimensi asumsi (kapasitas ideal)
    sql_ratio = """
    SELECT
        T.tahun,
        W.nama_wilayah,
        SUM(F.jumlah) AS total_workforce,
        (SELECT SUM(F2.jumlah) FROM fact_kesehatan F2 WHERE F2.id_tahun = F.id_tahun AND F2.id_wilayah = F.id_wilayah AND F2.jenis_data = 'Kasus Penyakit') AS total_cases,
        CASE
            WHEN SUM(F.jumlah) > 0 THEN (SELECT SUM(F2.jumlah) FROM fact_kesehatan F2 WHERE F2.id_tahun = F.id_tahun AND F2.id_wilayah = F.id_wilayah AND F2.jenis_data = 'Kasus Penyakit') / SUM(F.jumlah)
            ELSE 0
        END AS workforce_ratio
    FROM fact_kesehatan F
    JOIN dim_tahun T ON F.id_tahun = T.id_tahun
    JOIN dim_wilayah W ON F.id_wilayah = W.id_wilayah
    JOIN dim_indikator_asumsi I ON F.id_indikator = I.id_indikator
    WHERE F.jenis_data = 'Tenaga Kerja' AND F.id_indikator != 0 -- Hanya tenaga kerja yang punya asumsi
    GROUP BY 1, 2;
    """

    try:
        df_ratio = pd.read_sql(sql_ratio, core_dw_engine)

        # Jika ada data, muat ke Mart
        if not df_ratio.empty:
            df_ratio.to_sql('mart_workload_ratio', mart_engine, if_exists='replace', index=False)
            print(f"✅ mart_workload_ratio dimuat: {len(df_ratio)} baris.")
        else:
            print("⚠️ Peringatan: Data untuk mart_workload_ratio kosong. Pastikan data asumsi dan fact table terisi.")

    except Exception as e:
        print(f"❌ ERROR saat memuat mart_workload_ratio: {e}")

# --- FUNGSI UTAMA ---

def main_create_mart():
    """
    Fungsi utama untuk menjalankan proses roll-up dari Core DW ke Data Mart.
    """
    print("Memulai Proses Pembuatan Data Mart (Roll-up)...")
    
    if not CORE_DW_DB_FILE.exists():
        print(f"❌ ERROR: Core Data Warehouse DB ({CORE_DW_DB_FILE.name}) tidak ditemukan. Harap jalankan load_dw.py terlebih dahulu.")
        return
    
    # Inisialisasi MART_ENGINE di luar try/except (agar bisa diakses di sub-fungsi)
    global MART_ENGINE # Gunakan global karena kita memodifikasi variabel di luar scope
    MART_ENGINE = None # Inisialisasi awal ke None

    try:
        # A. DRP: Backup dan Hapus File Lama
        if MART_DB_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"mart_health_summary_backup_{timestamp}.db"
            backup_file_path = BACKUP_PATH / backup_filename
            shutil.copy2(MART_DB_FILE, backup_file_path)
            print(f"✅ Backup file DB Mart lama dibuat: {backup_file_path}")
            
            # --- TITIK KRITIS PERBAIKAN ---
            # Tutup paksa semua koneksi SQLAlchemy yang mungkin tertinggal sebelum unlink.
            # Namun, karena kita menghapus MART_ENGINE dari atas, ini seharusnya tidak perlu.
            # TAMBAHKAN INI: Tutup Engine Mart yang mungkin aktif sebelum menghapus file
           
            if MART_ENGINE is not None: # TIDAK PERLU 'MART_ENGINE' in globals() lagi karena sudah global
                try:
                    MART_ENGINE.dispose() # Menutup semua koneksi yang dipegang oleh engine
                    # Tidak perlu set MART_ENGINE = None lagi setelah dispose di sini
                    print("✅ Koneksi MART_ENGINE lama berhasil ditutup/dilepas.")
                except Exception as dispose_e:
                    print(f"⚠️ Peringatan: Gagal dispose MART_ENGINE: {dispose_e}")

            # Lanjutkan penghapusan file
            try:
                # MART_DB_FILE.unlink() # <--- HAPUS BARIS INI KARENA ADA DUPLIKASI
                print(f"File DB Data Mart lama ({MART_DB_FILE.name}) dihapus.")
            except Exception as unlink_e:
                print(f"❌ ERROR KRITIS: Gagal menghapus file DB Mart! File mungkin terkunci. {unlink_e}")
                raise # Angkat error agar ditangkap oleh orkestrator
            
            # KODE DRP YANG BENAR:
            MART_DB_FILE.unlink() # Asumsi ini adalah baris UNLINK pertama yang dieksekusi
            print(f"File DB Data Mart lama ({MART_DB_FILE.name}) dihapus.")

        # B. RE-INISIALISASI ENGINE KONEKSI SETELAH FILE LAMA DIHAPUS
        MART_ENGINE = create_engine(f'sqlite:///{MART_DB_FILE}')

        # C. Buat Struktur Tabel (DDL) di Data Mart DB baru
        # Kita menggunakan sqlite3.connect untuk DDL karena lebih langsung
        with sqlite3.connect(MART_DB_FILE) as conn:
            create_mart_db_schema(conn)

        # D. Load Tabel-tabel Mart (Agregasi)
        load_mart_annual_case_summary(CORE_DW_ENGINE, MART_ENGINE)
        load_mart_annual_workforce_summary(CORE_DW_ENGINE, MART_ENGINE)
        load_mart_workload_ratio(CORE_DW_ENGINE, MART_ENGINE)
        
        print("\n✅ Proses Pembuatan Data Mart Selesai! Data Mart siap untuk BI.")

    except Exception as e:
        print(f"\n❌ ERROR selama proses pembuatan Mart: {e}")

# --- JALANKAN PROSES UTAMA ---
if __name__ == "__main__":
    main_create_mart() # Ganti main() dengan main_create_mart() agar tidak perlu fungsi main() wrapper