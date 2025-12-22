@echo off

REM --- Konfigurasi Environment dan Log ---
set BPS_API_KEY=0219815268b89ba81521d219d0a98771
set LOG_FILE="D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis\etl_log_%DATE:/=-%.txt"

REM Pindah ke direktori proyek (Wajib)
cd /d "D:\Kuliah\Semester 7\BI\UAS_Kecerdasan_Bisnis"

REM Aktifkan Virtual Environment
call venv_DW\Scripts\activate.bat

echo [%DATE% %TIME%] ========================================================================= >> %LOG_FILE%
echo [%DATE% %TIME%] Memulai Proses ETL Harian Pukul 06:00 >> %LOG_FILE%
echo [%DATE% %TIME%] ========================================================================= >> %LOG_FILE%

REM --- TAHAP 1: EKSTRAKSI (E) ---
echo [%DATE% %TIME%] [STAGE 1/3] Memulai Ekstraksi Data BPS... >> %LOG_FILE%
python src\etl_scripts\extract.py >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
    echo [%DATE% %TIME%] [ERROR] Ekstraksi GAGAL. Menghentikan proses. >> %LOG_FILE%
    goto :FAIL
)

REM --- TAHAP 2: TRANSFORMASI (T) ---
echo [%DATE% %TIME%] [STAGE 2/3] Memulai Transformasi dan Pembersihan... >> %LOG_FILE%
python src\etl_scripts\transform.py >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
    echo [%DATE% %TIME%] [ERROR] Transformasi GAGAL. Menghentikan proses. >> %LOG_FILE%
    goto :FAIL
)

REM --- TAHAP 3: LOAD & DATA MART (L) ---
echo [%DATE% %TIME%] [STAGE 3/3] Memuat ke Core DW dan Data Mart... >> %LOG_FILE%
python src\etl_scripts\load_dw.py >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
    echo [%DATE% %TIME%] [ERROR] Pemuatan GAGAL. Menghentikan proses. >> %LOG_FILE%
    goto :FAIL
)

goto :SUCCESS

:FAIL
echo [%DATE% %TIME%] [STATUS] Proses ETL GAGAL Total. >> %LOG_FILE%
goto :END

:SUCCESS
echo [%DATE% %TIME%] [STATUS] Proses ETL Selesai dan SUKSES. >> %LOG_FILE%

:END
call deactivate
echo [%DATE% %TIME%] Deaktivasi VENV. >> %LOG_FILE%
