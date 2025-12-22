import sys
import os
from datetime import datetime
from pathlib import Path

# Tambahkan project root ke sys.path agar import absolut bekerja
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Impor Modul Utama (Asumsi skrip ETL Anda punya fungsi main yang bisa dipanggil)
# Catatan: Jika skrip Anda menggunakan 'if __name__ == "__main__":' untuk menjalankan,
# Anda harus mengubahnya menjadi fungsi bernama main() yang dipanggil di sini.
try:
    # Menggunakan import absolut karena script dijalankan langsung
    from src.etl_scripts import extract, transform, load as load_dw, create_mart
    from src.etl_scripts.callback_functions import log_status_callback, setup_log_table
except ImportError as e:
    print(f"❌ ERROR IMPORT: Pastikan semua file ETL (.py) ada di folder yang sama: {e}")
    sys.exit(1)


# --- KONFIGURASI GLOBAL ---
# Engine yang akan digunakan untuk koneksi log status
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"
CORE_DW_DB_FILE = DATA_ROOT / "07_Test" / "core_dw_test.db" # Path untuk test, menggunakan folder 07_Test
from sqlalchemy import create_engine
CORE_DW_ENGINE = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")


def run_etl_stage(stage_name, function_to_call):
    """Fungsi pembantu untuk menjalankan setiap tahap ETL dan menangkap status."""
    print(f"\n=======================")
    print(f"[STAGE] Memulai {stage_name}...")
    try:
        # Panggil fungsi main dari setiap skrip ETL
        result = function_to_call()
        print(f"[STAGE] ✅ {stage_name} berhasil diselesaikan.")
        return result
    except Exception as e:
        # Jika ada kegagalan di tahap ini, kita akan tangkap di main_etl_workflow
        print(f"[STAGE] ❌ {stage_name} GAGAL: {e}")
        raise # Meneruskan exception ke blok except utama

def main_etl_workflow():
    """
    Fungsi utama orkestrasi yang menjalankan proses ETL dari Extract hingga Mart,
    menggunakan DRP dan Callback Logging. (Versi Test Error: Simulasi Gagal Total)
    """
    process_name = "DAILY_ETL_WORKFLOW_TEST_ERROR"
    start_time = datetime.now()
    total_rows_processed = 0

    # Buat engine lokal untuk logging
    local_engine = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")

    # 1. Pastikan Tabel Log Dibuat di Awal
    setup_log_table(local_engine)
    local_engine.dispose()  # Tutup koneksi sebelum load stage

    try:
        # Simulasi kegagalan total ETL untuk test
        raise Exception("Simulated ETL Failure: Proses ETL gagal total untuk keperluan testing.")

        # --- TAHAP 1: EXTRACT ---
        # Asumsi: extract.py.main() mengembalikan status atau jumlah data
        run_etl_stage("1/4: Data Extraction", extract.main)

        # --- TAHAP 2: TRANSFORM ---
        run_etl_stage("2/4: Data Transformation", transform.main)

        # --- TAHAP 3: LOAD DW (Meliputi DRP Backup & Load Dimensi/Fact) ---
        # Asumsi: load_dw.main() mengembalikan jumlah baris yang berhasil dimuat
        rows_loaded = run_etl_stage("3/4: Load Data Warehouse", load_dw.main)
        total_rows_processed = rows_loaded if rows_loaded is not None else 0

        # --- TAHAP 4: CREATE MART ---
        run_etl_stage("4/4: Create Data Mart", create_mart.main_create_mart)

        # =================================================================
        # >>> SUCCESS CALLBACK <<<
        # =================================================================
        # Buat ulang engine untuk callback
        local_engine = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")
        log_status_callback(
            local_engine,
            process_name,
            "SUCCESS",
            "Workflow ETL harian berhasil diselesaikan secara keseluruhan.",
            start_time,
            total_rows_processed
        )
        local_engine.dispose()
        print(f"\n=======================================================")
        print("✅ Proses ETL Selesai Total. Status dicatat di Audit Log.")
        print(f"=======================================================")

    except Exception as e:
        # =================================================================
        # >>> ERROR CALLBACK <<<
        # =================================================================
        import traceback # <-- TAMBAHKAN INI

        # Tampilkan error lengkap ke console untuk debugging
        print("\n=== DEBUG: FULL TRACEBACK ===")
        traceback.print_exc()
        print("==============================")
            
        # Ambil nama fungsi yang gagal
        error_message = f"Proses ETL GAGAL Total. Lokasi Kegagalan: {e.__traceback__.tb_frame.f_code.co_name} (di salah satu stage), Error: {str(e)}"

        try:
            # Buat ulang engine untuk error callback
            local_engine = create_engine(f"sqlite:///{CORE_DW_DB_FILE}")
            log_status_callback(
                local_engine,
                process_name,
                "FAILED",
                error_message,
                start_time,
                total_rows_processed
            )
            local_engine.dispose()
        except Exception as log_error:
            print(f"⚠️ Gagal mencatat error ke log: {log_error}")

        print(f"\n=======================================================")
        print(f"❌ PROSES ETL GAGAL TOTAL. Detail dicatat di Audit Log di folder 07_Test.")
        print(f"=======================================================")
        sys.exit(1) # Keluar dengan status error

if __name__ == "__main__":
    main_etl_workflow()
