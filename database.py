import sqlite3, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / 'data' / 'predictions.db'

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))

def init_db():
    with _connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT,
                temperature     REAL,
                humidity        REAL,
                windspeed       REAL,
                irradiance      REAL,
                actual_kw       REAL,
                savings_monthly REAL,
                co2_reduction   REAL,
                home_type       TEXT DEFAULT "2bhk"
            )
        ''')
        # Add home_type column if upgrading from old DB
        try:
            conn.execute('ALTER TABLE predictions ADD COLUMN home_type TEXT DEFAULT "2bhk"')
        except:
            pass
        conn.commit()
    print(f"Database ready: {DB_PATH}")

def clear_history():
    """Delete all prediction records and reset the auto-increment counter."""
    with _connect() as conn:
        conn.execute('DELETE FROM predictions')
        conn.execute('DELETE FROM sqlite_sequence WHERE name="predictions"')
        conn.commit()

def save_prediction(temperature, humidity, windspeed, irradiance,
                    actual_kw, savings_monthly, co2_reduction, home_type='2bhk'):
    ts = datetime.datetime.now().isoformat(timespec='seconds')
    with _connect() as conn:
        conn.execute('''
            INSERT INTO predictions
              (timestamp,temperature,humidity,windspeed,irradiance,
               actual_kw,savings_monthly,co2_reduction,home_type)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (ts, temperature, humidity, windspeed, irradiance,
              actual_kw, savings_monthly, co2_reduction, home_type))
        conn.commit()

def get_history(limit=20):
    with _connect() as conn:
        cur = conn.execute(
            'SELECT * FROM predictions ORDER BY id DESC LIMIT ?', (limit,))
        return cur.fetchall()