from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS untuk terima request dari Streamlit

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MART_DB_FILE = PROJECT_ROOT / "Data" / "04_data_mart" / "mart_health_summary.db"

@app.route('/')
def index():
    """Root endpoint untuk memberikan pesan selamat datang dan status."""
    return jsonify({
        'status': 'running',
        'message': 'Welcome to the User Tracking API. Please use the designated endpoints.',
        'endpoints': ['/api/track', '/api/session', '/api/health'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/track', methods=['GET','POST'])
def track_event():
    """Endpoint untuk tracking user interaction"""
    if request.method == 'GET':
        return jsonify({'status': 'ready', 'message': 'Use POST to send tracking data'}), 200

    try:
        data = request.json
        # Validasi input dasar
        required_keys = ['session_id', 'action_name', 'element_name', 'element_type', 'timestamp', 'is_success', 'page_url']
        if not all(key in data for key in required_keys):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        with sqlite3.connect(MART_DB_FILE) as conn:
            # Aktifkan mode WAL untuk konkurensi yang lebih baik
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # Mulai transaksi secara eksplisit
            cursor.execute("BEGIN")

            # --- Operasi dalam satu transaksi ---
            # 1. Insert/Get User
            # 2. Get/Insert Action
            # 3. Get/Insert Element
            # 4. Insert Interaction

            # 1. Insert/Get User
            cursor.execute("""
                INSERT OR IGNORE INTO dim_user (user_session_id, device_type, browser, screen_resolution)
                VALUES (?, ?, ?, ?)
            """, (data['session_id'], data['device_type'], data['browser'], data['screen_resolution']))
            
            cursor.execute("SELECT id_user FROM dim_user WHERE user_session_id = ?", (data['session_id'],))
            id_user = cursor.fetchone()[0]
            
            # 2. Get/Insert Action ID
            cursor.execute("INSERT OR IGNORE INTO dim_action (action_name, action_category) VALUES (?, 'unknown')", 
                           (data['action_name'],))
            cursor.execute("SELECT id_action FROM dim_action WHERE action_name = ?", (data['action_name'],))
            id_action = cursor.fetchone()[0]
            
            # 3. Get/Insert Element ID
            cursor.execute("""
                INSERT OR IGNORE INTO dim_element (element_name, element_type, page_section) 
                VALUES (?, ?, 'unknown')
            """, (data['element_name'], data['element_type']))
            cursor.execute("SELECT id_element FROM dim_element WHERE element_name = ?", (data['element_name'],))
            id_element = cursor.fetchone()[0]
            
            # 4. Insert Interaction
            cursor.execute("""
                INSERT INTO fact_user_interaction 
                (id_user, id_action, id_element, timestamp, is_success, error_message, page_url, previous_element)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_user, id_action, id_element, data['timestamp'], 
                  data['is_success'], data.get('error_message'), data['page_url'], data.get('previous_element')))
            
            cursor.execute("COMMIT")
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        print(f"❌ Error tracking: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/session', methods=['POST'])
def save_session():
    """Endpoint untuk save session data"""
    try:
        data = request.json
        # Validasi input dasar
        required_keys = ['session_id', 'session_start', 'session_end', 'total_duration_sec', 'total_clicks', 'total_errors', 'is_bounce']
        if not all(key in data for key in required_keys):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        with sqlite3.connect(MART_DB_FILE) as conn:
            # Aktifkan mode WAL untuk konkurensi yang lebih baik
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute("SELECT id_user FROM dim_user WHERE user_session_id = ?", (data['session_id'],))
            result = cursor.fetchone()
            
            if result:
                id_user = result[0]
                
                # Insert session
                cursor.execute("""
                    INSERT INTO fact_session 
                    (id_user, session_start, session_end, total_duration_sec, total_clicks, total_errors, is_bounce)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (id_user, data['session_start'], data['session_end'], 
                      data['total_duration_sec'], data['total_clicks'], 
                      data['total_errors'], data['is_bounce']))
                
                return jsonify({'status': 'success'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    except Exception as e:
        print(f"❌ Error saving session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    print("🚀 Starting Flask API for User Tracking...")
    print(f"📁 Database: {MART_DB_FILE}")
    app.run(host='0.0.0.0', port=5000, debug=False)