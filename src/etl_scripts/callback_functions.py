from sqlalchemy import create_engine, text
from datetime import datetime
from pathlib import Path
import os
import sys

# --- KONFIGURASI DB ---
# Pathing Relatif (Asumsi script ini berada di src/etl_scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"
CORE_DW_PATH = DATA_ROOT / "07_Test"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_test.db"

# Engine yang spesifik untuk modul ini (digunakan jika dipanggil dari luar)
# Tetapi kita akan mengandalkan engine yang dipass dari callback_test.py
# CORE_DW_ENGINE_LOCAL = create_engine(f"sqlite:///{CORE_DW_DB_FILE}") 


def setup_log_table(engine):
    """Membuat tabel audit log (etl_audit_log) jika belum ada di database."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS etl_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        process_name TEXT NOT NULL,
        status TEXT NOT NULL, -- SUCCESS atau FAILED
        message TEXT,
        duration_sec REAL,
        data_rows_loaded INTEGER
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
    except Exception as e:
        # Menampilkan error, tetapi tidak menghentikan proses utama
        print(f"[CALLBACK_FUNC] ❌ ERROR: Gagal membuat tabel etl_audit_log: {e}")


def log_status_callback(engine, process_name, status, message, start_time, rows_loaded=0):
    """
    Fungsi Callback yang menulis hasil eksekusi ke etl_audit_log.
    Dipanggil setelah proses utama berhasil (SUCCESS) atau gagal (FAILED).
    """
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Memastikan tabel log tersedia
    setup_log_table(engine)
    
    insert_sql = text("""
        INSERT INTO etl_audit_log (timestamp, process_name, status, message, duration_sec, data_rows_loaded)
        VALUES (:timestamp, :process_name, :status, :message, :duration, :rows_loaded)
    """)
    
    try:
        with engine.connect() as conn:
            conn.execute(insert_sql, {
                'timestamp': end_time.strftime("%Y-%m-%d %H:%M:%S"),
                'process_name': process_name,
                'status': status,
                'message': message,
                'duration': duration,
                'rows_loaded': rows_loaded
            })
            conn.commit()
            print(f"[CALLBACK_FUNC] ✅ LOGGING BERHASIL: Status {status} dicatat di etl_audit_log.")
    except Exception as e:
        print(f"[CALLBACK_FUNC] ❌ ERROR LOGGING: Gagal menulis ke DB: {e}")