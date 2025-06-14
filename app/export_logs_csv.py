import sqlite3
import csv
import os

def export_logs_to_csv():
    db_path = "app/eventflow_logs.db"
    csv_path = "admin_logs.csv"

    if not os.path.exists(db_path):
        print(f"[ERRO] Base de dados '{db_path}' não encontrada.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp, user_email, method, path, status_code, message FROM logs")
    rows = cursor.fetchall()

    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "user_email", "method", "path", "status_code", "message"])
        writer.writerows(rows)

    conn.close()
    print(f"[OK] Logs exportados para {csv_path}")

if __name__ == "__main__":
    export_logs_to_csv()