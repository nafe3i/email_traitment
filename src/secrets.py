"""
secrets.py — Encryption & Secrets Management via Fernet.
Toutes les cles viennent du .env — zero hardcoding.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class SecretsManager:

    def __init__(self, master_key: str):
        try:
            key = master_key.encode() if isinstance(master_key, str) else master_key
            self.cipher = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid Fernet key: {e}")

    @classmethod
    def from_env(cls) -> "SecretsManager":
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError(
                "SECRET_KEY environment variable not found. "
                "Generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        return cls(secret_key)

    def encrypt_token(self, token: str) -> str:
        if not isinstance(token, str) or not token:
            raise ValueError("Token must be a non-empty string")
        try:
            return self.cipher.encrypt(token.encode()).decode()
        except Exception:
            logger.error("Encryption failed")
            raise

    def decrypt_token(self, encrypted_token: str) -> str:
        if not isinstance(encrypted_token, str) or not encrypted_token:
            raise ValueError("Encrypted token must be a non-empty string")
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            logger.error("Token decryption failed: invalid token")
            raise ValueError("Invalid or corrupted token")
        except Exception:
            logger.error("Decryption failed")
            raise

    def encrypt_dict(self, data: dict) -> dict:
        return {
            k: self.encrypt_token(v) if isinstance(v, str) else v
            for k, v in data.items()
        }

    def decrypt_dict(self, data: dict) -> dict:
        result = {}
        for k, v in data.items():
            if isinstance(v, str) and len(v) > 50:
                try:
                    result[k] = self.decrypt_token(v)
                except ValueError:
                    result[k] = v
            else:
                result[k] = v
        return result


def migrate_plaintext_credentials(
    plaintext_file: str,
    output_file: str,
    manager: SecretsManager,
    base_dir: Optional[str] = None,
) -> int:
    """Migre des credentials en clair vers chiffre avec protection path traversal."""
    base     = Path(base_dir).resolve() if base_dir else Path(".").resolve()
    in_path  = (base / plaintext_file).resolve()
    out_path = (base / output_file).resolve()

    if not str(in_path).startswith(str(base)):
        raise ValueError("Path traversal detected for input file")
    if not str(out_path).startswith(str(base)):
        raise ValueError("Path traversal detected for output file")

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    encrypted_data = {}
    count = 0
    for key, value in data.items():
        if isinstance(value, str):
            encrypted_data[key] = manager.encrypt_token(value)
            count += 1
        else:
            encrypted_data[key] = value

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(encrypted_data, f, indent=2)

    logger.info("Credentials migrated successfully")
    return count


def generate_fernet_key() -> str:
    return Fernet.generate_key().decode()


def validate_fernet_key(key: str) -> bool:
    try:
        Fernet(key.encode() if isinstance(key, str) else key)
        return True
    except Exception:
        return False
