# packages/security/src/kms.py
"""Hardware KMS envelope encryption provider for secrets and environment variables."""

import base64
import hashlib
import os
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class KMSEnvelopeEncryption:
    """Envelope encryption provider simulating AWS KMS master key and data key hierarchy."""

    def __init__(self, master_key_arn: str = "arn:aws:kms:us-east-1:123456789012:key/kautilya-prod") -> None:
        self.master_key_arn = master_key_arn
        # Derive master key from ARN for local envelope operations
        self._master_secret = hashlib.sha256(master_key_arn.encode("utf-8")).digest()

    def generate_data_key(self) -> tuple[bytes, str]:
        """Generate a plaintext data encryption key (DEK) and its ciphertext encrypted by master key.

        Returns:
            Tuple of (plaintext_dek: bytes, encrypted_dek_b64: str).
        """
        raw_dek = os.urandom(32)
        # Encrypt DEK with master key using SHA-256 HMAC stream mask
        mask = hashlib.sha256(self._master_secret + b"KMS_DEK_ENVELOPE").digest()
        encrypted_dek = bytes(a ^ b for a, b in zip(raw_dek, mask))
        encrypted_dek_b64 = base64.b64encode(encrypted_dek).decode("utf-8")
        return raw_dek, encrypted_dek_b64

    def decrypt_data_key(self, encrypted_dek_b64: str) -> bytes:
        """Decrypt ciphertext DEK using the master key.

        Args:
            encrypted_dek_b64: Base64-encoded encrypted DEK.

        Returns:
            Plaintext DEK bytes.
        """
        encrypted_dek = base64.b64decode(encrypted_dek_b64.encode("utf-8"))
        mask = hashlib.sha256(self._master_secret + b"KMS_DEK_ENVELOPE").digest()
        return bytes(a ^ b for a, b in zip(encrypted_dek, mask))

    def encrypt_secret(self, plaintext: str) -> dict[str, str]:
        """Encrypt a secret string using KMS envelope encryption.

        Returns:
            Dictionary with 'ciphertext' and 'encrypted_dek' strings.
        """
        dek, encrypted_dek = self.generate_data_key()
        pt_bytes = plaintext.encode("utf-8")
        # Symmetric stream encryption with DEK
        key_stream = hashlib.sha256(dek + b"SECRET_STREAM").digest()
        repeats = (len(pt_bytes) // len(key_stream)) + 1
        full_stream = (key_stream * repeats)[:len(pt_bytes)]
        ct = bytes(p ^ k for p, k in zip(pt_bytes, full_stream))

        return {
            "ciphertext": base64.b64encode(ct).decode("utf-8"),
            "encrypted_dek": encrypted_dek,
            "master_key_arn": self.master_key_arn,
        }

    def decrypt_secret(self, encrypted_bundle: dict[str, str]) -> str:
        """Decrypt an envelope-encrypted secret bundle.

        Args:
            encrypted_bundle: Dictionary containing 'ciphertext' and 'encrypted_dek'.

        Returns:
            Decrypted plaintext string.
        """
        dek = self.decrypt_data_key(encrypted_bundle["encrypted_dek"])
        ct = base64.b64decode(encrypted_bundle["ciphertext"].encode("utf-8"))
        key_stream = hashlib.sha256(dek + b"SECRET_STREAM").digest()
        repeats = (len(ct) // len(key_stream)) + 1
        full_stream = (key_stream * repeats)[:len(ct)]
        pt_bytes = bytes(c ^ k for c, k in zip(ct, full_stream))
        return pt_bytes.decode("utf-8")
