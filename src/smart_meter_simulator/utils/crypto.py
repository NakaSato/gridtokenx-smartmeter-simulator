import base64
import base58
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

    # Generate wallet address (base58 encoded public key)
    wallet_address = base58.b58encode(public_bytes).decode("utf-8")

    return private_b64, public_b64, wallet_address


def sign_message(private_key_b64: str, message: str) -> str:
    """
    Sign a message using an Ed25519 private key.

    Args:
        private_key_b64: Base64 encoded private key
        message: String message to sign

    Returns:
        str: Base64 encoded signature
    """
    try:
        # Decode private key
        private_bytes = base64.b64decode(private_key_b64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)

        # Sign message (convert to bytes first)
        signature = private_key.sign(message.encode("utf-8"))

        # Return base64 encoded signature
        return base64.b64encode(signature).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to sign message: {e}")


def verify_signature(public_key_b64: str, message: str, signature_b64: str) -> bool:
    """
    Verify an Ed25519 signature.

    Args:
        public_key_b64: Base64 encoded public key
        message: Original message string
        signature_b64: Base64 encoded signature

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Decode public key and signature
        public_bytes = base64.b64decode(public_key_b64)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        signature = base64.b64decode(signature_b64)

        # Verify
        public_key.verify(signature, message.encode("utf-8"))
        return True
    except Exception:
        return False


class KeyManager:
    """
    Manages Ed25519 keys for a meter.
    """

    def __init__(self):
        self.private_key, self.public_key, self.wallet_address = generate_keypair()

    def sign_data(self, data: str) -> str:
        """Sign string data."""
        return sign_message(self.private_key, data)

    def get_public_key(self) -> str:
        """Get base64 public key."""
        return self.public_key

    def get_wallet_address(self) -> str:
        """Get base58 wallet address."""
        return self.wallet_address
