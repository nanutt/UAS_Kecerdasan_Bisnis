import shutil
from pathlib import Path
import os
import sys

# --- KONFIGURASI JALUR DATA DAN DB ---
# Asumsi script berada di src/etl_scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "Data"

# Target Database yang akan dipulihkan (DB yang rusak)
CORE_DW_PATH = DATA_ROOT / "07_Test"
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_test.db"

# Sumber Backup
BACKUP_PATH = DATA_ROOT / "06_backup"

# --- FUNGSI UTILITY ---

def find_latest_backup(backup_folder: Path, db_name: str) -> Path | None:
    """Mencari file backup terbaru (berdasarkan waktu modifikasi/pembuatan) untuk database yang diberikan."""
    
    # Mencari semua file backup yang cocok dengan pola nama
    # Contoh pola: core_dw_test_20251212_121500_backup.db
    backup_files = sorted([
        f for f in backup_folder.glob(f'{db_name.split(".")[0]}_*_backup.db')
    ], key=os.path.getmtime, reverse=True) # Urutkan berdasarkan waktu (terbaru di depan)

    if backup_files:
        return backup_files[0]
    else:
        return None

def recover_core_dw():
    """Menjalankan proses pemulihan otomatis untuk core_dw_test.db."""
    
    print("\n=======================================================")
    print("         🛠️ MEMULAI PROSEDUR PEMULIHAN TEST DW        ")
    print("=======================================================")
    
    # 1. Identifikasi Backup Terbaru
    print(f"1. Mencari file backup terbaru di {BACKUP_PATH.name}...")
    latest_backup = find_latest_backup(BACKUP_PATH, CORE_DW_DB_FILE.name)

    if not latest_backup:
        print("❌ GAGAL: Tidak ada file backup core_dw_test.db yang ditemukan. Pemulihan tidak dapat dilakukan.")
        print("   Pastikan drp_test.py sudah dijalankan minimal 2 kali sehingga backup tercipta.")
        sys.exit(1)

    print(f"   ✅ Ditemukan file backup: {latest_backup.name}")
    
    # 2. Hapus DB Korup (jika ada)
    if CORE_DW_DB_FILE.exists():
        print(f"2. Menghapus atau memindahkan DB korup ({CORE_DW_DB_FILE.name})...")
        try:
            CORE_DW_DB_FILE.unlink() # Hapus file
            print("   ✅ File DB korup berhasil dihapus.")
        except Exception as e:
            print(f"   ❌ ERROR: Gagal menghapus DB korup. Pastikan tidak sedang digunakan. {e}")
            sys.exit(1)
    else:
        print("2. DB Target (core_dw_test.db) tidak ditemukan. Melanjutkan pemulihan...")

    # 3. & 4. Salin dan Ganti Nama File Backup
    try:
        # Target path sama dengan nama file DB asli (core_dw_test.db)
        target_path = CORE_DW_DB_FILE 
        
        print(f"3. Menyalin {latest_backup.name} ke {CORE_DW_PATH.name}...")
        
        # Salin file, shutil.copy2 mempertahankan metadata file
        shutil.copy2(latest_backup, target_path)
        
        print(f"   ✅ Pemulihan data berhasil! File disalin dan diubah namanya menjadi:")
        print(f"      -> {CORE_DW_DB_FILE.name}")
        
    except Exception as e:
        print(f"❌ ERROR FATAL: Gagal menyalin atau mengganti nama file. {e}")
        sys.exit(1)
        
    print("=======================================================")
    print("✅ PEMULIHAN CORE DW TEST SELESAI. DB siap digunakan kembali.")
    print("=======================================================")

if __name__ == "__main__":
    recover_core_dw()