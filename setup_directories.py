# setup_directories.py
from pathlib import Path
import os

# Define base path
BASE_PATH = Path("D:/Kuliah/Semester 7/BI/UAS_Kecerdasan_Bisnis/Data")

# Define all required directories
DIRECTORIES = {
    'raw': BASE_PATH / "01_raw",
    'processed': BASE_PATH / "02_staging",
    'reference': BASE_PATH / "03_ref_data",
    'data_mart': BASE_PATH / "04_data_mart ",
    'core_dw': BASE_PATH / "05_core_dw",
    'backup': BASE_PATH / "06_backup"
}

def create_directory_structure():
    """
    Membuat seluruh struktur direktori yang diperlukan untuk data warehouse.
    Menggunakan mkdir dengan parents=True untuk membuat parent directories
    dan exist_ok=True untuk menghindari error jika directory sudah ada.
    """
    print("Creating directory structure...")
    
    for name, path in DIRECTORIES.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/Verified: {path}")
    
    print("\n✅ Directory structure successfully created!")
    print("\nDirectory Summary:")
    print(f"  - Data Lake (Raw):    {DIRECTORIES['raw']}")
    print(f"  - Staging (Processed): {DIRECTORIES['processed']}")
    print(f"  - Reference Data:     {DIRECTORIES['reference']}")
    print(f"  - Data Mart:          {DIRECTORIES['data_mart']}")
    print(f"  - Core Data Warehouse:{DIRECTORIES['core_dw']}")
    print(f"  - Backup Zone:        {DIRECTORIES['backup']}")

if __name__ == "__main__":
    create_directory_structure()
