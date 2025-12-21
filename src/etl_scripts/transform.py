import pandas as pd
import json
import shutil
import datetime
from pathlib import Path
from sqlalchemy import create_engine

# --- KONFIGURASI JALUR DATA ---
# 1. PATHING RELATIF (Diperbaiki)
# Path(__file__).resolve().parent.parent.parent menunjuk ke D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent 
DATA_ROOT = PROJECT_ROOT / "Data" 

# 2. DEFINISI FOLDER (Sesuai Struktur DW Anda)
RAW_DATA_PATH = DATA_ROOT / "01_raw"          # Sumber: File JSON mentah
STAGING_PATH = DATA_ROOT / "02_staging"      # Tujuan: Staging Area (STG_DB/INT_DB)
CORE_DW_PATH = DATA_ROOT / "05_core_dw"      # Core DW Area
BACKUP_PATH = DATA_ROOT / "06_backup" / "backup_daily"        # Folder untuk backup

# 3. DATABASE FILES
CORE_DW_DB_FILE = CORE_DW_PATH / "core_dw_mart.db" # Database Core DW
MART_DB_FILE = DATA_ROOT / "04_data_mart" / "mart_health_summary.db" # Database Mart

BPS_VAR_MAPPING = {
    # Pemetaan variabel untuk kasus penyakit
    'fmumuesaff': 'Jumlah Kasus Penyakit - HIV/AIDS Kasus Baru',
    'bwkenrtsjt': 'Jumlah Kasus Penyakit - Malaria (Suspek)',
    'qdd1uktkny': 'Jumlah Kasus Penyakit - TB Paru',
    'fttzyjustj': 'Jumlah Kasus Penyakit - Pneumonia',
    'jmy11unqrx': 'Jumlah Kasus Penyakit - Kusta',
    'qtmcbxxvor': 'Jumlah Kasus Penyakit - Tetanus Neonatorum',
    'cjs4kxzrqw': 'Jumlah Kasus Penyakit - Campak',
    'frbktzdgwm': 'Jumlah Kasus Penyakit - Diare',
    '1saqzibyq1': 'Jumlah Kasus Penyakit - Demam Berdarah Dengue (DBD)',
    'r0inb73kfv': 'Jumlah Kasus Penyakit - HIV/AIDS Kasus Kumulatif',
    'h8ck3okhby': 'Jumlah Kasus Penyakit - Infeksi Menular Seksual (IMS)',
    
    # 2021 (tidak ada data)
    'uaikde6heaivlwdqabcf': 'Jumlah Kasus Penyakit - Angka Penemuan TBC',
    'xa3wrsnhbr4nmsqs4kri': 'Jumlah Kasus Penyakit - Angka Keberhasilan Pengobatan TBC',
    'czcjnafyzmbswvdud21x': 'Jumlah Kasus Penyakit - Penemuan Kasus Baru Kusta per 100.000 Penduduk',
    'tqqci2nnm0gpq2mzhyhc': 'Jumlah Kasus Penyakit - Angka Kesakitan Malaria per 1.000 Penduduk',
    '9n8me3mg1beg4pv1jckl': 'Jumlah Kasus Penyakit - Angka Kesakitan DBD per 100.000 Penduduk',
    
    # Paramater variabel untuk tenaga kerja kesehatan
    'cjkm56zyxh': 'Tenaga Kesehatan - Dokter',
    'trpp7jfxhj': 'Tenaga Kesehatan - Perawat',
    'wiexntuwb3': 'Tenaga Kesehatan - Bidan',
    '4ekzzjil5t': 'Tenaga Kesehatan - Tenaga Kefarmasian',
    'mcqvjutjsu': 'Tenaga Kesehatan - Tenaga Gizi',
    'rppxieukr9ffpscta1sf': 'Tenaga Kesehatan - Tenaga Kesehatan Masyarakat',
    '8quhgdykmvfsqh9f6efy': 'Tenaga Kesehatan - Tenaga Kesehatan Lingkungan',
    'rtxbxsujhyxaetyowrpd': 'Tenaga Kesehatan - Ahli Teknologi Laboratorium Medik',
    'qy5kkoasx5': 'Jumlah Tenaga Medis',
    'vju26nbmcl': 'Jumlah Tenaga Kesehatan Psikologi Klinis',
    'albep7ehtj': 'Jumlah Tenaga Keterapian Fisik',
    '2yrsnw7dsc': 'Jumlah Tenaga Keteknisan Medis',
    'dj4p8f6qnl': 'Jumlah Tenaga Teknik Biomedika',
    'wlezhymeqm': 'Jumlah Tenaga Kesehatan Tradisional',
    
}

# --- FUNGSI TRANSFORMATION ---

def transform_bps_data(filepath: Path, data_type: str) -> pd.DataFrame:
    """
    Memuat, meratakan (flattening), dan membersihkan data JSON BPS.
    """
    print(f" > Memproses {data_type.upper()} dari file: {filepath.name}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Periksa ketersediaan data (Data Governance Rule)
    if len(data['data']) < 2 or 'data' not in data['data'][1] or data['data'][1].get('condition') == 'ERROR':
        print(f"    [SKIP] Data tidak valid atau kosong di tahun {data['data'][1].get('tahun_data', '?')}.")
        return pd.DataFrame()

    # 1. Ekstrak Metadata (Tahun)
    tahun_data = data['data'][1]['tahun_data']

    # 2. Flattening Utama
    list_data = data['data'][1]['data']
    
    # Tentukan nama kolom berdasarkan jenis data
    if data_type == "kasus_penyakit":
        column_name = 'Nama Kasus Penyakit'
    elif data_type == "tenaga_kesehatan":
        column_name = 'Nama Tenaga Kesehatan'
    else:
        column_name = 'nama variabel'

    records = []
    for item in list_data:
        # Loop melalui setiap variabel (kasus penyakit/nakes) di setiap wilayah
        for var_id, var_content in item.get('variables', {}).items():
            # Mendapatkan nama yang dapat dibaca dari mapping
            nama_kolom = BPS_VAR_MAPPING.get(var_id, f'UNKNOWN_VAR_{var_id}')
            # Ambil nilai mentah (value_raw) atau nilai biasa (value)
            value = var_content.get('value_raw') if 'value_raw' in var_content and var_content.get('value_raw') is not None else var_content.get('value')
            records.append({
                'Tahun': tahun_data,
                'Kode_Wilayah': item['kode_wilayah'],
                'Nama_Wilayah': item['label'],
                'Jenis_Data': data_type.replace('_', ' ').title(),
                column_name: nama_kolom,
                'Jumlah_Raw': value,
                'Source_File': filepath.name
            })

    df_final = pd.DataFrame(records)
    # --- TRANSFORMATION & CLEANING (DATA GOVERNANCE) ---
    if df_final.empty:
        return df_final

    # 1. Cleaning & Standardisasi Angka
    df_final['Jumlah_Raw'] = df_final['Jumlah_Raw'].replace(['...', '–', '-'], pd.NA) 
    
    df_final['Jumlah_Clean'] = (df_final['Jumlah_Raw']
                                .astype(str)
                                .str.replace('.', '', regex=False) 
                                .str.replace(',', '.', regex=False)
                                )
    
    df_final['Jumlah_Clean'] = pd.to_numeric(df_final['Jumlah_Clean'], errors='coerce') 

    # 2. Penanganan Missing Values (Ganti NaN dengan 0 untuk Fakta)
    df_final['Jumlah_Clean'] = df_final['Jumlah_Clean'].fillna(0)
    
    # 3. Filtering (Hanya ambil data kabupaten/kota)
    df_final = df_final[df_final['Kode_Wilayah'] % 10000 != 0]

    return df_final

def process_and_save_data(data_type: str):
    """Mencari file, memproses, dan menyimpan hasil transformasi."""
    # Cari semua file JSON berdasarkan pola nama (misal: kasus_penyakit_*.json)
    file_pattern = f"{data_type}_*.json"
    all_files = list(RAW_DATA_PATH.glob(file_pattern))

    if not all_files:
        print(f"⚠️ Peringatan: Tidak ada file JSON '{data_type}' ditemukan di {RAW_DATA_PATH}.")
        return

    list_df = []
    for f in all_files:
        df_transformed = transform_bps_data(f, data_type)
        if not df_transformed.empty:
            list_df.append(df_transformed)

    if list_df:
        # Gabungkan semua data menjadi satu DataFrame besar
        df_integrated = pd.concat(list_df, ignore_index=True)

        # --- Simpan ke STAGING DATABASE (INT_DB Layer) ---
        print(f"\n[LOAD STAGING] Memuat {len(df_integrated)} baris data {data_type.upper()} ke SQLite...")

        try:
            # Tentukan file database berdasarkan data_type
            if data_type == "kasus_penyakit":
                db_file = STAGING_PATH / "stg_kasus_penyakit.db"
                table_name = 'stg_kasus_penyakit'
            elif data_type == "tenaga_kesehatan":
                db_file = STAGING_PATH / "stg_tenaga_kesehatan.db"
                table_name = 'stg_tenaga_kesehatan'
            else:
                raise ValueError(f"Unknown data_type: {data_type}")

            engine = create_engine(f'sqlite:///{db_file}')
            df_integrated.to_sql(table_name, engine, if_exists='replace', index=False)

            print(f"✅ Pemuatan ke STAGING DB berhasil: {data_type.upper()} dimuat ke tabel '{table_name}' di {db_file.name}.")

        except Exception as e:
            print(f"❌ ERROR: Gagal memuat data ke STAGING DB: {e}")

    else:
        print(f"\n❌ Transformasi {data_type.upper()} Gagal: Semua data kosong atau tidak valid.")

def create_timestamped_backup():
    """Membuat backup timestamped dari file database (DB) yang ada."""

    BACKUP_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Daftar semua file database yang perlu di-backup
    db_files = [
        STAGING_PATH / "stg_kasus_penyakit.db",
        STAGING_PATH / "stg_tenaga_kesehatan.db",
        STAGING_PATH / "staging_data.db",
        CORE_DW_DB_FILE,
        MART_DB_FILE
    ]

    print("\n--- Memulai Backup Database ---")

    for original_path in db_files:
        if original_path.exists():
            # Tentukan nama file backup
            backup_db_path = BACKUP_PATH / f"{original_path.name.replace('.db', '')}_{timestamp}.db"

            try:
                shutil.copy2(original_path, backup_db_path)
                print(f"[SUCCESS] Backup DB {original_path.name} berhasil disimpan.")
            except Exception as e:
                print(f"[WARNING] Gagal backup {original_path.name}: {e}")
        else:
            print(f"ℹ️ File {original_path.name} tidak ditemukan, melewati backup.")

    # Hapus staging_data.db setelah backup, karena sudah tidak diperlukan
    staging_data_path = STAGING_PATH / "staging_data.db"
    if staging_data_path.exists():
        staging_data_path.unlink()
        print(f"✅ Deleted old staging_data.db from {STAGING_PATH}.")


def main():
    # 1. Panggil fungsi backup (Data Recovery Plan)
    create_timestamped_backup()

    # 2. Proses Kasus Penyakit
    process_and_save_data("kasus_penyakit")

    # 3. Proses Tenaga Kesehatan
    process_and_save_data("tenaga_kesehatan")

    print("\n--- Transformasi Data BPS Selesai dan Dimuat ke Staging Database ---")

if __name__ == "__main__":
    main()
    