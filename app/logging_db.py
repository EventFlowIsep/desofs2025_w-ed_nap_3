import sqlite3
from datetime import datetime
import threading

class SQLiteLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.conn = sqlite3.connect("eventflow_logs.db", check_same_thread=False)
                    cls._instance.cursor = cls._instance.conn.cursor()
                    cls._instance._create_table()
        return cls._instance

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_email TEXT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                message TEXT
            )
        ''')
        self.conn.commit()

    def save_log(self, user_email, method, path, status_code, message=""):
        timestamp = datetime.utcnow().isoformat()
        self.cursor.execute('''
            INSERT INTO logs (timestamp, user_email, method, path, status_code, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_email, method, path, status_code, message))
        self.conn.commit()

def save_log(user_email, method, path, status_code, message=""):
    logger = SQLiteLogger()
    logger.save_log(user_email, method, path, status_code, message)
