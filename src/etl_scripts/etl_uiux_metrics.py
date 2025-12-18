import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MART_DB_FILE = PROJECT_ROOT / "Data" / "04_data_mart" / "mart_health_summary.db"

def create_mart_uiux_tables():
    """Buat tabel mart untuk metrik UI/UX (sudah dibuat di create_mart.py, ini backup)"""
    with sqlite3.connect(MART_DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Cek apakah tabel sudah ada
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mart_user_behavior'")
        if cursor.fetchone():
            print("✅ Tabel mart UI/UX sudah ada.")
            return
        
        print("⚠️ Tabel mart UI/UX belum ada. Silakan jalankan create_mart.py dulu.")


def calculate_daily_user_behavior():
    """Hitung metrik user behavior harian"""
    print("\n--- 1. Menghitung User Behavior Metrics ---")

    with sqlite3.connect(MART_DB_FILE) as conn:
        cursor = conn.cursor()

        # Hapus data hari ini dulu (jika sudah ada)
        cursor.execute("DELETE FROM mart_user_behavior WHERE date = DATE('now')")

        # Cek apakah ada data di fact_session
        cursor.execute("SELECT COUNT(*) FROM fact_session")
        session_count = cursor.fetchone()[0]

        if session_count == 0:
            # Jika tidak ada data session, buat data dummy untuk testing
            print("⚠️ Tidak ada data session, membuat data dummy untuk testing...")
            cursor.execute("""
                INSERT INTO mart_user_behavior (date, total_sessions, total_clicks, total_errors,
                                                bounce_rate, avg_session_duration_sec, avg_clicks_per_session)
                VALUES (DATE('now'), 5, 25, 2, 20.0, 180.5, 5.0)
            """)
            rows = 1
        else:
            # Agregasi data session hari ini
            cursor.execute("""
                INSERT INTO mart_user_behavior (date, total_sessions, total_clicks, total_errors,
                                                bounce_rate, avg_session_duration_sec, avg_clicks_per_session)
                SELECT
                    DATE(session_start) as date,
                    COUNT(DISTINCT id_session) as total_sessions,
                    SUM(total_clicks) as total_clicks,
                    SUM(total_errors) as total_errors,
                    ROUND(AVG(CASE WHEN is_bounce = 1 THEN 100.0 ELSE 0.0 END), 2) as bounce_rate,
                    ROUND(AVG(total_duration_sec), 2) as avg_session_duration_sec,
                    ROUND(AVG(CAST(total_clicks AS REAL)), 2) as avg_clicks_per_session
                FROM fact_session
                WHERE DATE(session_start) = DATE('now')
                GROUP BY DATE(session_start)
            """)

            rows = cursor.rowcount

            # Jika tidak ada data untuk hari ini, ambil data terakhir
            if rows == 0:
                cursor.execute("""
                    INSERT INTO mart_user_behavior (date, total_sessions, total_clicks, total_errors,
                                                    bounce_rate, avg_session_duration_sec, avg_clicks_per_session)
                    SELECT
                        DATE('now') as date,
                        COUNT(DISTINCT id_session) as total_sessions,
                        SUM(total_clicks) as total_clicks,
                        SUM(total_errors) as total_errors,
                        ROUND(AVG(CASE WHEN is_bounce = 1 THEN 100.0 ELSE 0.0 END), 2) as bounce_rate,
                        ROUND(AVG(total_duration_sec), 2) as avg_session_duration_sec,
                        ROUND(AVG(CAST(total_clicks AS REAL)), 2) as avg_clicks_per_session
                    FROM fact_session
                    GROUP BY DATE(session_start)
                    ORDER BY DATE(session_start) DESC
                    LIMIT 1
                """)
                rows = cursor.rowcount

        conn.commit()
        print(f"✅ User Behavior: {rows} baris diupdate untuk hari ini.")


def calculate_element_performance():
    """Hitung performa setiap elemen UI"""
    print("\n--- 2. Menghitung Element Performance ---")
    
    with sqlite3.connect(MART_DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Hapus data hari ini
        cursor.execute("DELETE FROM mart_element_performance WHERE date = DATE('now')")
        
        # Agregasi interaksi per elemen
        cursor.execute("""
            INSERT INTO mart_element_performance (date, element_name, total_interactions, 
                                                  error_count, error_rate, avg_dwell_time_sec)
            SELECT 
                DATE(fi.timestamp) as date,
                de.element_name,
                COUNT(*) as total_interactions,
                SUM(CASE WHEN fi.is_success = 0 THEN 1 ELSE 0 END) as error_count,
                ROUND(AVG(CASE WHEN fi.is_success = 0 THEN 100.0 ELSE 0.0 END), 2) as error_rate,
                ROUND(AVG(COALESCE(fi.duration_ms, 0)) / 1000.0, 2) as avg_dwell_time_sec
            FROM fact_user_interaction fi
            JOIN dim_element de ON fi.id_element = de.id_element
            WHERE DATE(fi.timestamp) = DATE('now')
            GROUP BY DATE(fi.timestamp), de.element_name
        """)
        
        rows = cursor.rowcount
        conn.commit()
        print(f"✅ Element Performance: {rows} elemen dianalisis.")


def calculate_usability_score():
    """Hitung Usability Score berdasarkan formula"""
    print("\n--- 3. Menghitung Usability Score ---")
    
    with sqlite3.connect(MART_DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Hapus data hari ini
        cursor.execute("DELETE FROM mart_usability_score WHERE date = DATE('now')")
        
        # Hitung metrik dasar
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN is_success = 1 THEN 100.0 ELSE 0.0 END) as task_completion_rate,
                AVG(COALESCE(duration_ms, 0)) / 1000.0 as avg_time_sec,
                AVG(CASE WHEN is_success = 0 THEN 100.0 ELSE 0.0 END) as error_rate
            FROM fact_user_interaction
            WHERE DATE(timestamp) = DATE('now')
        """)
        
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            completion_rate = result[0]
            avg_time = result[1]
            error_rate = result[2]
            
            # Formula Usability Score:
            # (Completion × 0.5) + (Time Efficiency × 0.3) + ((100 - Error) × 0.2)
            # Time Efficiency: 100 jika ≤ 30s, turun linear sampai 0 di 120s
            time_efficiency = max(0, min(100, 100 - ((avg_time - 30) / 90 * 100))) if avg_time > 30 else 100
            
            usability_score = (completion_rate * 0.5) + (time_efficiency * 0.3) + ((100 - error_rate) * 0.2)
            
            cursor.execute("""
                INSERT INTO mart_usability_score (date, task_completion_rate, avg_time_on_task_sec, 
                                                  error_rate, usability_score)
                VALUES (DATE('now'), ?, ?, ?, ?)
            """, (round(completion_rate, 2), round(avg_time, 2), round(error_rate, 2), round(usability_score, 2)))
            
            conn.commit()
            print(f"✅ Usability Score: {usability_score:.2f}/100")
        else:
            print("⚠️ Tidak ada data interaksi untuk hari ini.")


def calculate_click_path():
    """Analisis click path (urutan klik yang sering terjadi)"""
    print("\n--- 4. Menghitung Click Path Analysis ---")
    
    with sqlite3.connect(MART_DB_FILE) as conn:
        # Ambil data interaksi dengan urutan waktu
        df = pd.read_sql("""
            SELECT 
                du.user_session_id,
                de.element_name,
                fi.timestamp
            FROM fact_user_interaction fi
            JOIN dim_user du ON fi.id_user = du.id_user
            JOIN dim_element de ON fi.id_element = de.id_element
            WHERE DATE(fi.timestamp) = DATE('now')
            ORDER BY du.user_session_id, fi.timestamp
        """, conn)
        
        if df.empty:
            print("⚠️ Tidak ada data untuk click path.")
            return
        
        # Group by session dan buat path sequence
        paths = df.groupby('user_session_id')['element_name'].apply(lambda x: ' → '.join(x)).value_counts()
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mart_click_path")
        
        # Insert top 20 path
        for path, freq in paths.head(20).items():
            cursor.execute("""
                INSERT INTO mart_click_path (path_sequence, frequency, avg_completion_time_sec, success_rate)
                VALUES (?, ?, 0, 100)
            """, (path, int(freq)))
        
        conn.commit()
        print(f"✅ Click Path: {len(paths)} unique paths, top 20 disimpan.")


def calculate_funnel_analysis():
    """Analisis funnel (alur user dari step ke step)"""
    print("\n--- 5. Menghitung Funnel Analysis ---")
    
    # Definisi funnel steps
    funnel_steps = [
        ('page_load', 1),
        ('radio_year', 2),
        ('dropdown_wilayah', 3),
        ('chart_trend', 4),
        ('chart_stacked_bar_cases', 5)
    ]
    
    with sqlite3.connect(MART_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mart_funnel WHERE date = DATE('now')")
        
        total_users = cursor.execute("""
            SELECT COUNT(DISTINCT id_user) 
            FROM fact_user_interaction 
            WHERE DATE(timestamp) = DATE('now')
        """).fetchone()[0]
        
        if total_users == 0:
            print("⚠️ Tidak ada user hari ini.")
            return
        
        prev_count = total_users
        
        for element_name, step_order in funnel_steps:
            # Hitung user yang sampai ke step ini
            user_count = cursor.execute("""
                SELECT COUNT(DISTINCT fi.id_user)
                FROM fact_user_interaction fi
                JOIN dim_element de ON fi.id_element = de.id_element
                WHERE DATE(fi.timestamp) = DATE('now')
                AND de.element_name = ?
            """, (element_name,)).fetchone()[0]
            
            dropout_rate = round((1 - user_count / prev_count) * 100, 2) if prev_count > 0 else 0
            
            cursor.execute("""
                INSERT INTO mart_funnel (date, step_name, step_order, user_count, dropout_rate)
                VALUES (DATE('now'), ?, ?, ?, ?)
            """, (element_name, step_order, user_count, dropout_rate))
            
            prev_count = user_count
        
        conn.commit()
        print(f"✅ Funnel Analysis: {len(funnel_steps)} steps dianalisis.")


def main_etl_uiux():
    """Fungsi utama untuk menjalankan semua ETL UI/UX"""
    print("=" * 60)
    print("🚀 Memulai ETL UI/UX Metrics")
    print("=" * 60)
    
    if not MART_DB_FILE.exists():
        print(f"❌ Database tidak ditemukan: {MART_DB_FILE}")
        return
    
    try:
        create_mart_uiux_tables()
        calculate_daily_user_behavior()
        calculate_element_performance()
        calculate_usability_score()
        calculate_click_path()
        calculate_funnel_analysis()
        
        print("\n" + "=" * 60)
        print("✅ ETL UI/UX Metrics Selesai!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR selama ETL: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main_etl_uiux()