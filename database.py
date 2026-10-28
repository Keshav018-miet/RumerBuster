import sqlite3
import os
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

if os.environ.get('VERCEL'):
    DB_FILE = os.path.join('/tmp', 'rumorbuster.db')
else:
    DB_FILE = os.path.join(os.path.dirname(__file__), 'rumorbuster.db')
    old_db = os.path.join(os.path.dirname(__file__), 'truthscan.db')
    if os.path.exists(old_db) and not os.path.exists(DB_FILE):
        try:
            shutil.copy2(old_db, DB_FILE)
        except Exception:
            pass

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS forensic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE NOT NULL,
            analysis_type TEXT NOT NULL,
            input_name TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            sha256_hash TEXT,
            perceptual_hash TEXT,
            result TEXT,
            confidence REAL,
            metadata_json TEXT,
            fact_check_info TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS origin_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT UNIQUE NOT NULL,
            query_text TEXT NOT NULL,
            query_type TEXT NOT NULL,
            query_hash TEXT NOT NULL,
            earliest_date TEXT,
            ground_zero_source TEXT,
            ground_zero_url TEXT,
            domain_age_days INTEGER,
            submitter_ip TEXT,
            submitter_geo TEXT,
            summary_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Seed default admin user if not exists
    admin_user = c.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_user:
        hashed_pw = generate_password_hash('admin123')
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                  ('admin', 'admin@rumorbuster.local', hashed_pw))
        conn.commit()

    conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pw = generate_password_hash(password)
    try:
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                  (username.strip(), email.strip().lower(), hashed_pw))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.IntegrityError as e:
        conn.close()
        err_str = str(e).lower()
        if 'username' in err_str:
            return False, "Username already exists."
        elif 'email' in err_str:
            return False, "Email already registered."
        return False, "Registration failed due to a constraint conflict."

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username.strip(),)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),)).fetchone()
    conn.close()
    return dict(user) if user else None

def verify_user_password(username, password):
    user = get_user_by_username(username)
    if not user:
        return False, None
    if check_password_hash(user['password_hash'], password):
        return True, user
    return False, None

def save_record(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO forensic_records (
            record_id, analysis_type, input_name, file_type, file_size,
            sha256_hash, perceptual_hash, result, confidence, metadata_json, fact_check_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('record_id'), data.get('analysis_type'), data.get('input_name'),
        data.get('file_type'), data.get('file_size'), data.get('sha256_hash'),
        data.get('perceptual_hash'), data.get('result'), data.get('confidence'),
        data.get('metadata_json'), data.get('fact_check_info')
    ))
    conn.commit()
    conn.close()

def get_all_records():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM forensic_records ORDER BY timestamp DESC').fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_record_by_id(record_id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM forensic_records WHERE record_id = ?', (record_id,)).fetchone()
    conn.close()
    return dict(record) if record else None

def save_origin_trace(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO origin_traces (
            trace_id, query_text, query_type, query_hash, earliest_date,
            ground_zero_source, ground_zero_url, domain_age_days,
            submitter_ip, submitter_geo, summary_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('trace_id'), data.get('query_text'), data.get('query_type'),
        data.get('query_hash'), data.get('earliest_date'), data.get('ground_zero_source'),
        data.get('ground_zero_url'), data.get('domain_age_days'), data.get('submitter_ip'),
        data.get('submitter_geo'), data.get('summary_json')
    ))
    conn.commit()
    conn.close()

def get_origin_trace_recurrence(query_hash):
    """Checks if a claim/URL hash was previously analyzed, returns count and first timestamp."""
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT trace_id, submitter_geo, timestamp FROM origin_traces WHERE query_hash = ? ORDER BY timestamp ASC',
        (query_hash,)
    ).fetchall()
    conn.close()
    if not rows:
        return {"count": 0, "first_seen": None, "first_geo": None}
    return {
        "count": len(rows),
        "first_seen": rows[0]['timestamp'],
        "first_geo": rows[0]['submitter_geo']
    }

def get_all_origin_traces(limit=25):
    conn = get_db_connection()
    traces = conn.execute(
        'SELECT * FROM origin_traces ORDER BY timestamp DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(t) for t in traces]

