import sqlite3
from datetime import datetime
import threading
import re
import logging
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "eventflow_logs.db")

class SQLiteLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                    cls._instance.cursor = cls._instance.conn.cursor()
                    cls._instance._create_table()
                    cls._instance._alter_table()
                    cls._instance._create_alerts_table()
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
                message TEXT,
                ip TEXT,
                user_agent TEXT
            )
        ''')
        self.conn.commit()
    def _create_alerts_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_email TEXT,
                ip TEXT,
                pattern TEXT,
                path TEXT
            )
        ''')
        self.conn.commit()
    def _alter_table(self):
        try:
            self.cursor.execute('''
                ALTER TABLE logs
                ADD COLUMN ip TEXT;
            ''')
            self.cursor.execute('''
                ALTER TABLE logs
                ADD COLUMN user_agent TEXT;
            ''')
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                raise

    def save_log(self, user_email, method, path, status_code, message="", ip=None, user_agent=""):
        timestamp = datetime.utcnow().isoformat()
        self.cursor.execute('''
            INSERT INTO logs (timestamp, user_email, method, path, status_code, message, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_email, method, path, status_code, message, ip, user_agent))
        print("✅ INSERT INTO logs executado")
        combined_text = f"{path} {message}"
        suspicious = detect_suspicious_pattern(combined_text)
        if suspicious:
            logging.warning(f"⚠️ Suspicious activity detected [{suspicious}] from IP: {ip} ({user_email})")
            self.cursor.execute('''
                INSERT INTO alerts (timestamp, user_email, ip, pattern, path)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, user_email, ip, suspicious, path))
        self.conn.commit()

def save_log(user_email, method, path, status_code, message="", ip=None, user_agent = ""):
    print(f"🪵 [LOGGING] Saving log: {method} {path} ({status_code})")
    logger = SQLiteLogger()
    logger.save_log(user_email, method, path, status_code, message, ip, user_agent)

def detect_suspicious_pattern(text: str) -> str | None:
    patterns = {
        "SQL Injection": [r"(?i)(union\s+select)", r"(?i)(or\s+1=1)", r"(?i)(drop\s+table)", r"(?i)--"],
        "XSS Attack": [r"(?i)<script>", r"(?i)javascript:", r"(?i)onerror\s*="],
        "Path Traversal": [r"\.\./", r"%2e%2e/"],
        "Generic Injection": [r"(?i)(\{\{|\}\})", r"(?i)\$ne", r"\$where"]
    }

    for label, regex_list in patterns.items():
        for regex in regex_list:
            if re.search(regex, text):
                return label
    return None
