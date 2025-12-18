import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

def create_user_logs_schema(conn):
    """
    Membuat struktur tabel untuk User Interaction Logs (UI/UX Tracking).
    Dipanggil setelah create_mart_db_schema().
    """
    cursor = conn.cursor()

    print("\n[DDL] Membuat Struktur Tabel User Logs untuk UI/UX Tracking...")

    # Drop existing tables jika ada
    tables_to_drop = [
        'fact_user_interaction',
        'fact_session',
        'dim_user',
        'dim_action',
        'dim_element',
        'mart_user_behavior',
        'mart_click_path',
        'mart_element_performance',
        'mart_usability_score',
        'mart_funnel'
    ]

    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
    conn.commit()

    # === DIMENSI TABLES ===

    # 1. Dimensi User
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_user (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            user_session_id TEXT UNIQUE NOT NULL,
            device_type TEXT,
            browser TEXT,
            screen_resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Dimensi Action Type
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_action (
            id_action INTEGER PRIMARY KEY AUTOINCREMENT,
            action_name TEXT UNIQUE NOT NULL,
            action_category TEXT
        );
    """)

    # 3. Dimensi Element
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_element (
            id_element INTEGER PRIMARY KEY AUTOINCREMENT,
            element_name TEXT UNIQUE NOT NULL,
            element_type TEXT,
            page_section TEXT
        );
    """)

    # === FACT TABLES ===

    # 4. Fact User Interaction
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_user_interaction (
            id_interaction INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            id_action INTEGER,
            id_element INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_ms INTEGER,
            is_success BOOLEAN DEFAULT 1,
            error_message TEXT,
            page_url TEXT,
            previous_element TEXT,
            FOREIGN KEY (id_user) REFERENCES dim_user(id_user),
            FOREIGN KEY (id_action) REFERENCES dim_action(id_action),
            FOREIGN KEY (id_element) REFERENCES dim_element(id_element)
        );
    """)

    # 5. Fact Session
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_session (
            id_session INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            session_start TIMESTAMP,
            session_end TIMESTAMP,
            total_duration_sec INTEGER,
            total_clicks INTEGER,
            total_errors INTEGER,
            is_bounce BOOLEAN,
            FOREIGN KEY (id_user) REFERENCES dim_user(id_user)
        );
    """)

    # === MART TABLES (Agregasi UI/UX) ===

    # 6. Mart User Behavior
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_user_behavior (
            date DATE,
            total_sessions INTEGER,
            total_clicks INTEGER,
            total_errors INTEGER,
            bounce_rate REAL,
            avg_session_duration_sec REAL,
            avg_clicks_per_session REAL
        );
    """)

    # 7. Mart Click Path
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_click_path (
            path_sequence TEXT,
            frequency INTEGER,
            avg_completion_time_sec REAL,
            success_rate REAL
        );
    """)

    # 8. Mart Element Performance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_element_performance (
            date DATE,
            element_name TEXT,
            total_interactions INTEGER,
            error_count INTEGER,
            error_rate REAL,
            avg_dwell_time_sec REAL
        );
    """)

    # 9. Mart Usability Score
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_usability_score (
            date DATE,
            task_completion_rate REAL,
            avg_time_on_task_sec REAL,
            error_rate REAL,
            usability_score REAL
        );
    """)

    # 10. Mart Funnel Analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mart_funnel (
            date DATE,
            step_name TEXT,
            step_order INTEGER,
            user_count INTEGER,
            dropout_rate REAL
        );
    """)

    conn.commit()

    # === INSERT SEED DATA ===

    print("[SEED] Mengisi data awal untuk dim_action dan dim_element...")

    # Insert data awal dim_action
    cursor.executemany("""
        INSERT OR IGNORE INTO dim_action (action_name, action_category) VALUES (?, ?)
    """, [
        ('click_button', 'click'),
        ('click_dropdown', 'click'),
        ('select_year', 'filter'),
        ('select_wilayah', 'filter'),
        ('select_kategori', 'filter'),
        ('view_chart', 'view'),
        ('scroll', 'scroll'),
        ('hover', 'hover'),
        ('page_load', 'navigation'),
        ('page_exit', 'navigation'),
        ('widget_change', 'interaction')
    ])

    # Insert data awal dim_element
    cursor.executemany("""
        INSERT OR IGNORE INTO dim_element (element_name, element_type, page_section) VALUES (?, ?, ?)
    """, [
        ('radio_year', 'radio_button', 'sidebar'),
        ('dropdown_wilayah', 'dropdown', 'right_panel'),
        ('dropdown_kategori', 'dropdown', 'right_panel'),
        ('chart_trend', 'chart', 'main_chart'),
        ('chart_donut', 'chart', 'main_chart'),
        ('chart_stacked_bar_cases', 'chart', 'main_chart'),
        ('chart_stacked_bar_workforce', 'chart', 'main_chart'),
        ('chart_scatter_correlation', 'chart', 'main_chart'),
        ('chart_pie_kategori', 'chart', 'right_panel'),
        ('map_wilayah', 'map', 'right_panel'),
        ('card_summary', 'card', 'main_chart'),
        ('card_workload', 'card', 'right_panel'),
        ('table_gap_analysis', 'table', 'right_panel'),
        ('dashboard_main', 'page', 'main')
    ])

    conn.commit()
    print("[DDL] Struktur tabel User Logs dan Mart UI/UX berhasil dibuat.")


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
            create_user_logs_schema(conn)  # TAMBAHKAN INI

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