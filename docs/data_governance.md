Dokumen ini menguraikan prinsip-prinsip Tata Kelola Data (Data Governance) yang dianut oleh Data Warehouse Kesehatan.

1. Prinsip Kualitas Data
Tata Kelola Data dijamin melalui implementasi prinsip kualitas data pada tahap Transformasi.

Akurasi: Data, seperti jumlah kasus atau tenaga kesehatan, yang bernilai NULL, negatif, atau sangat tidak realistis diidentifikasi dan ditangani pada tahap Transformasi (transform.py).

Konsistensi: Unit pengukuran diseragamkan. Kolom kunci seperti Kode_Wilayah dan Tahun distandarisasi dan dikonversi ke tipe data yang konsisten di seluruh skema (misalnya VARCHAR untuk Kode Wilayah, INTEGER untuk Tahun).

Kelengkapan: Melibatkan mekanisme Extract untuk mengambil data dari semua tahun yang tersedia. Pada tahap Load, data yang tidak lengkap (Missing Keys) pada kolom dimensi dikelola, misalnya, diberi placeholder "Unknown" atau ID khusus.

Keterbaruan: Data Warehouse ini menggunakan pendekatan Full Load harian. Seluruh tabel Fakta dan Dimensi dimuat ulang dari Staging pada setiap run ETL, menjamin data adalah versi terbaru dari sumbernya.

2. Standar Arsitektur Data
2.1 Desain Skema
Data Warehouse ini menggunakan Desain Skema Bintang (Star Schema). Desain ini memisahkan data menjadi Tabel Fakta yang menampung metrik kuantitatif (misalnya, Jumlah_Clean) dan Tabel Dimensi yang menampung atribut deskriptif (misalnya, dim_wilayah, dim_tahun).

2.2 Standar Penamaan
Seluruh objek dalam Data Warehouse (DW) mengikuti standar penamaan yang konsisten untuk keterbacaan dan pemeliharaan: Tabel Dimensi menggunakan prefix dim_ (contoh: dim_wilayah). Tabel Fakta menggunakan prefix fact_ (contoh: fact_health_data). Tabel Mart menggunakan prefix mart_ (contoh: mart_annual_case_summary). Kunci Utama (Primary Key) menggunakan prefix id_ (contoh: id_wilayah).

3. Tata Kelola Operasional (Monitoring)
Tata kelola operasional dijamin melalui mekanisme monitoring aktif. Audit Trail diimplementasikan melalui tabel etl_audit_log yang mencatat riwayat setiap proses ETL, memungkinkan audit historis terhadap waktu run, durasi, dan status. Penanganan Kegagalan dijamin oleh DRP yang menggunakan backup sebelum load. Akses Data pengguna akhir (BI Tools) diarahkan ke Data Marts (mart_health_summary.db) yang merupakan subset data teragregasi. Ini mencegah akses langsung dan lock file pada Core DW (core_dw_mart.db) dan meningkatkan kinerja kueri pelaporan.