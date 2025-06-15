import sqlite3
import csv
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from base64 import urlsafe_b64encode
import os

# ----------------------------
# PASSWORD, SALT e ITERAÇÕES
# ----------------------------
PASSWORD = "eventflow2025"
SALT = b"eventflow_salt_2025"
ITERATIONS = 390000

# ----------------------------
# DERIVAR CHAVE SEGURA
# ----------------------------
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=SALT,
    iterations=ITERATIONS,
)
key = urlsafe_b64encode(kdf.derive(PASSWORD.encode()))
fernet = Fernet(key)

# ----------------------------
# EXPORTAR LOGS ENCRIPTADOS PARA logs_backups/
# ----------------------------
def export_logs_to_csv():
    conn = sqlite3.connect("app/eventflow_logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]
    conn.close()

    # Criar diretório logs_backups se não existir
    os.makedirs("logs_backups", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_name = f"admin_logs_{timestamp}.csv"
    enc_name = f"{csv_name}.enc"

    csv_path = os.path.join("logs_backups", csv_name)
    enc_path = os.path.join("logs_backups", enc_name)

    # Escrever CSV temporário
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)

    # Encriptar e guardar
    with open(csv_path, "rb") as f:
        encrypted_data = fernet.encrypt(f.read())
    with open(enc_path, "wb") as f:
        f.write(encrypted_data)

    os.remove(csv_path)  # Apagar CSV plano

    print(f"✅ Logs exportados e encriptados com sucesso para: {enc_path}")

if __name__ == "__main__":
    export_logs_to_csv()