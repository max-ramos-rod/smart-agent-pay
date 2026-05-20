import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    # Deriva uma chave Fernet de 32 bytes a partir do SECRET_KEY da aplicação
    raw = settings.SECRET_KEY.encode()[:32].ljust(32, b"0")
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def encrypt_key(private_key_b64: str) -> str:
    """Recebe a ephemeral private key em base64 e retorna criptografada."""
    return _get_fernet().encrypt(private_key_b64.encode()).decode()


def decrypt_key(encrypted: str) -> bytes:
    """Retorna os bytes da ephemeral private key descriptografada."""
    decrypted_b64 = _get_fernet().decrypt(encrypted.encode()).decode()
    return base64.b64decode(decrypted_b64)
