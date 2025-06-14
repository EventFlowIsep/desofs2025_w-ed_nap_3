import sqlite3
import csv
from datetime import datetime

def export_logs_to_csv():
    db_path = "app/eventflow_logs.db"
    csv_path = f"admin_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, user_email, method, path, status_code, ip, user_agent, message FROM logs")

        rows = cursor.fetchall()

        headers = ["timestamp", "user_email", "method", "path", "status_code", "ip", "user_agent", "message"]

        with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"[✅ CSV exportado com sucesso] -> {csv_path}")

    except Exception as e:
        print(f"[❌ Erro ao exportar logs para CSV]: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    export_logs_to_csv()