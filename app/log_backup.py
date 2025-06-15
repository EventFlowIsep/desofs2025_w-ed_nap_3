import os
import shutil
from datetime import datetime

def backup_logs():
    origem = "app/eventflow_logs.db"
    backup_dir = "log_backups"
    os.makedirs(backup_dir, exist_ok=True)  # Garante que a pasta existe

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = os.path.join(backup_dir, f"eventflow_logs_backup_{timestamp}.db")

    shutil.copy(origem, destino)
    print(f"[OK] Backup criado: {destino}")

if __name__ == "__main__":
    backup_logs()