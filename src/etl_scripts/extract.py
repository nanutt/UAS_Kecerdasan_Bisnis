import requests
import json
import os
from pathlib import Path

# --- KONFIGURASI API DAN JALUR DATA (Diubah untuk Environment Variable) ---

# 1. API_KEY diambil dari Environment Variable BPS_API_KEY
# Nama variabel lingkungan ini harus sama dengan yang Anda setel di PowerShell.
API_KEY = os.getenv("BPS_API_KEY") 

BASE_URL = "https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/simdasi/id/25/"
WILAYAH = "6300000" # Kalimantan Selatan

# ID Tabel dari query Anda:
CONFIG_TABLES = {
    "kasus_penyakit": "a05CZmFhT0JWY0lBd2g0cW80S0xiZz09",
    "tenaga_kesehatan": "aWpHRGF4UVBjZTVEODBHMTV4R0xUUT09" # Asumsi Anda menggunakan 'tenaga_kesehatan'
}

START_YEAR = 2017
END_YEAR = 2024

# Path navigasi ke D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis\Data\01_raw
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent 
DATA_ROOT = PROJECT_ROOT / "Data" 
RAW_DATA_PATH = DATA_ROOT / "01_raw" 

# --- FUNGSI EKSTRAKSI ---

def ensure_directory_exists(path):
    """Memastikan folder data (raw data) ada."""
    path.mkdir(parents=True, exist_ok=True)

def extract_bps_data():
    """Melakukan ekstraksi data dari BPS WebAPI untuk semua tahun dan tabel."""
    
    # 1. Cek Ketersediaan API Key (Wajib!)
    if not API_KEY:
        print("\nFATAL ERROR: BPS_API_KEY TIDAK DITEMUKAN!")
        print("Anda HARUS menjalankan perintah ini di PowerShell SEBELUM menjalankan skrip:")
        print('$env:BPS_API_KEY="0219815268b89ba81521d219d0a98771"')
        return # Hentikan eksekusi jika key tidak ada
        
    # 2. Lanjutkan proses jika API Key ditemukan
    ensure_directory_exists(RAW_DATA_PATH)
    print(f"Memulai ekstraksi data BPS dari {START_YEAR} hingga {END_YEAR}...")

    # Iterasi berdasarkan jenis data
    for data_type, id_tabel in CONFIG_TABLES.items():
        print(f"\n--- Mengambil data: {data_type.upper()} ---")
        
        # Iterasi berdasarkan tahun
        for tahun in range(START_YEAR, END_YEAR + 1):
            url = f"{BASE_URL}tahun/{tahun}/id_tabel/{id_tabel}/wilayah/{WILAYAH}/key/{API_KEY}"
            
            try:
                print(f"  > Mengambil data {tahun}...")
                response = requests.get(url)
                response.raise_for_status() 
                data = response.json()
                
                # Simpan ke Data Lake Layer (Data/01_raw)
                filename = RAW_DATA_PATH / f"{data_type}_{tahun}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
                print(f"    Berhasil. Disimpan di: {filename.relative_to(PROJECT_ROOT)}")
                
            except requests.exceptions.RequestException as e:
                print(f"    [ERROR] Gagal mengambil data BPS tahun {tahun} ({data_type}): {e}")
                continue

def main():
    extract_bps_data()

if __name__ == "__main__":
    main()
