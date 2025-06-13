import sqlite3
import time
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

DB_PATH = "eventflow_logs.db"
ERROR_THRESHOLD = 5  # erros por intervalo
CHECK_INTERVAL = 60  # segundos
ALERT_EMAIL = "teuemail@exemplo.com"

def send_email_alert(error_count, recent_errors):
    msg = EmailMessage()
    msg['Subject'] = f'[ALERTA] {error_count} erros detectados em EventFlow'
    msg['From'] = ALERT_EMAIL
    msg['To'] = ALERT_EMAIL
    body = "Foram detectados os seguintes erros recentes:\n\n"
    for e in recent_errors:
        body += f"[{e[0]}] {e[2]} {e[3]} - {e[5]}\n"
    msg.set_content(body)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(ALERT_EMAIL, 'TUA_SENHA_AQUI')
        smtp.send_message(msg)

def check_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    while True:
        now = datetime.utcnow()
        since = now - timedelta(seconds=CHECK_INTERVAL)
        cursor.execute('''
            SELECT timestamp, user_email, method, path, status_code, message
            FROM logs
            WHERE status_code >= 400 AND timestamp >= ?
        ''', (since.isoformat(),))
        errors = cursor.fetchall()

        if len(errors) >= ERROR_THRESHOLD:
            send_email_alert(len(errors), errors)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    check_logs()
