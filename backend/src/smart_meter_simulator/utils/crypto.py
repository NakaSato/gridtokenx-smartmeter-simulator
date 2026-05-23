import base64
import base58
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair() -> tuple[str, str]:
    """
    Generate a new Ed25519 keypair.
    Returns:
        tuple[str, str]: (private_key_b64, public_key_b64)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key to bytes then base64
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_b64 = base64.b64encode(private_bytes).decode("utf-8")

    # Serialize public key to bytes then base64
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    public_b64 = base64.b64encode(public_bytes).decode("utf-8")

    return private_b64, public_b64


def sign_message(private_key_b64: str, message: str) -> str:
    """
    Sign a message using an Ed25519 private key.

    Args:
        private_key_b64: Base64 encoded private key
        message: String message to sign

    Returns:
        str: Base58 encoded signature (aligned with Oracle Bridge)
    """
    return sign_bytes(private_key_b64, message.encode("utf-8"))


def sign_bytes(private_key_b64: str, data: bytes) -> str:
    """
    Sign raw bytes using an Ed25519 private key.

    Args:
        private_key_b64: Base64 encoded private key
        data: bytes payload to sign

    Returns:
        str: Base58 encoded signature
    """
    try:
        # Decode private key
        private_bytes = base64.b64decode(private_key_b64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)

        # Sign data
        signature = private_key.sign(data)

        # Return base58 encoded signature
        return base58.b58encode(signature).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to sign bytes: {e}")


def verify_signature(public_key_b64: str, message: str, signature_b58: str) -> bool:
    """
    Verify an Ed25519 signature.

    Args:
        public_key_b64: Base64 encoded public key
        message: Original message string
        signature_b58: Base58 encoded signature

    Returns:
        bool: True if valid, False otherwise
    """
    return verify_signature_bytes(
        public_key_b64, message.encode("utf-8"), signature_b58
    )


def verify_signature_bytes(
    public_key_b64: str, data: bytes, signature_b58: str
) -> bool:
    """
    Verify an Ed25519 signature against raw bytes.

    Args:
        public_key_b64: Base64 encoded public key
        data: Original bytes payload
        signature_b58: Base58 encoded signature

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Decode public key and signature
        public_bytes = base64.b64decode(public_key_b64)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        signature = base58.b58decode(signature_b58)

        # Verify
        public_key.verify(signature, data)
        return True
    except Exception:
        return False


class KeyManager:
    """
    Manages Ed25519 keys for a meter.
    """

    def __init__(self, private_key: Optional[str] = None):
        if private_key:
            # Reconstruct from provided private key
            self.private_key = private_key
            private_bytes = base64.b64decode(private_key)
            priv = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
            pub = priv.public_key()
            pub_bytes = pub.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            self.public_key = base64.b64encode(pub_bytes).decode("utf-8")
        else:
            self.private_key, self.public_key = generate_keypair()

    def sign_data(self, data: str) -> str:
        """Sign string data."""
        return sign_message(self.private_key, data)

    def sign_binary_data(self, data: bytes) -> str:
        """Sign raw binary bytes."""
        return sign_bytes(self.private_key, data)

    def get_public_key(self) -> str:
        """Get base64 public key."""
        return self.public_key

    def get_public_key_hex(self) -> str:
        """Get hex public key (for Redis registration)."""
        public_bytes = base64.b64decode(self.public_key)
        return public_bytes.hex()
