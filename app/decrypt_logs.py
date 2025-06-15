import os
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# -------------------------------
# Definições seguras (consistentes com o exportador)
# -------------------------------
SALT = b"eventflow_salt_2025"
ITERATIONS = 390_000

def decrypt_file(file_path, password):
    # Derivar chave a partir da password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=ITERATIONS,
    )
    key = urlsafe_b64encode(kdf.derive(password.encode()))
    fernet = Fernet(key)

    # Ler dados encriptados
    with open(file_path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception:
        raise ValueError("❌ Password incorreta ou ficheiro inválido.")

    # Criar diretório logs_backups se não existir
    os.makedirs("logs_backups", exist_ok=True)

    # Gerar caminho de output
    filename = os.path.basename(file_path).replace(".enc", "_decrypted.csv")
    output_path = os.path.join("logs_backups", filename)

    # Guardar CSV desencriptado
    with open(output_path, "wb") as f:
        f.write(decrypted_data)

    print(f"✅ Ficheiro desencriptado com sucesso: {output_path}")

# -------------------------------
# Execução direta
# -------------------------------
if __name__ == "__main__":
    enc_file = input("📄 Nome do ficheiro .enc (ex: logs_backups/admin_logs_2025-06-15_18-30-00.csv.enc): ").strip()
    password = input("🔐 Password de desencriptação: ").strip()

    if not os.path.isfile(enc_file):
        print("❌ Ficheiro não encontrado.")
    else:
        try:
            decrypt_file(enc_file, password)
        except Exception as e:
            print(str(e))