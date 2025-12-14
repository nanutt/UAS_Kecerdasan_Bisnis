Dokumen ini menjelaskan strategi Pencegahan Kegagalan (DRP) dan Mekanisme Pelaporan (Callback/Logging) yang diimplementasikan pada alur kerja ETL Data Warehouse (DW) Kesehatan.

1. Strategi Disaster Recovery Plan (DRP)
DRP bertujuan untuk mengamankan data DW (core_dw_mart.db) sebelum setiap proses full load untuk memungkinkan pemulihan ke kondisi terakhir yang valid.

1.1 Mekanisme Pencegahan (Backup Otomatis)
Mekanisme pencegahan utama adalah backup otomatis file database. Proses ini dipicu oleh skrip load_dw.py (yang dijalankan oleh orchestrator) tepat sebelum ia memulai load data dari Staging ke Core DW. Skrip akan memeriksa keberadaan file DB target. Jika file ditemukan, skrip akan menyalin (shutil.copy2) core_dw_mart.db yang lama ke folder Data/06_backup/. Penamaan file menggunakan timestamp (contoh: core_dw_mart_backup_YYYYMMDD_HHMMSS.db) untuk memastikan keunikan dan urutan waktu. Tujuan dari tindakan ini adalah untuk memastikan bahwa jika proses load data baru gagal dan merusak file DB, backup dari run sebelumnya (keadaan valid terakhir) tersedia untuk pemulihan.

1.2 Prosedur Pemulihan (Recovery)
Pemulihan dilakukan menggunakan skrip utilitas recover_test.py secara manual. Proses ini tidak dijalankan setiap hari, melainkan hanya saat terjadi bencana atau kegagalan kritis. Langkah pertama adalah mengidentifikasi kerusakan, biasanya dikonfirmasi melalui etl_audit_log bahwa proses load berakhir dengan status FAILED, atau DB tidak dapat diakses. Administrator kemudian menjalankan skrip: python src/etl_scripts/recover_test.py. Skrip ini akan mencari file backup terbaru (berdasarkan timestamp) di Data/06_backup/. Kemudian, skrip menghapus DB yang rusak (core_dw_mart.db) dan menyalin file backup terbaru ke lokasi produksi Data/05_core_dw/. Setelah pemulihan, Core DW kembali ke kondisi data valid terakhir sebelum kegagalan.

2. Explicit Error/Success Callback (Monitoring)
Mekanisme callback menyediakan Audit Trail yang otomatis dan eksplisit untuk setiap run ETL.

2.1 Mekanisme Logging
Mekanisme logging diatur dalam modul callback_functions.py. Modul ini menyediakan fungsi log_status_callback yang menulis status ke tabel etl_audit_log yang berada di dalam core_dw_mart.db. Fungsi ini dipicu oleh main_orchestrator.py di akhir proses. Jika proses berhasil (di dalam blok try), status yang dicatat adalah SUCCESS, beserta durasi total dan jumlah baris data yang dimuat. Jika terjadi kegagalan (di dalam blok except), status yang dicatat adalah FAILED, beserta lokasi kegagalan dan pesan error secara rinci.

2.2 Manfaat etl_audit_log
Tabel log mencatat data krusial untuk operasional, meliputi: timestamp (kapan proses selesai/gagal), process_name (nama proses yang dijalankan), status (status akhir: SUCCESS atau FAILED), duration_sec (waktu eksekusi total), dan message (detail error atau konfirmasi sukses).
