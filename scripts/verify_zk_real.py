import logging
import base64
import sys
import os

# Add src to path to simulate app environment if needed (though extension is installed in site-packages)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_zk_real")

def run_verification():
    logger.info("Starting Real ZK Proof Verification...")
    
    try:
        import gridtokenx_py
        from gridtokenx_py import ZkProver
        logger.info(f"Successfully imported gridtokenx_py module: {gridtokenx_py}")
    except ImportError as e:
        logger.error(f"Failed to import gridtokenx_py: {e}")
        return

    # Test encrypt_amount
    amount = 500
    try:
        logger.info(f"Encrypting amount: {amount}")
        ciphertext_b64 = ZkProver.encrypt_amount(amount)
        logger.info(f"Ciphertext (Base64): {ciphertext_b64}")
        
        ciphertext_bytes = base64.b64decode(ciphertext_b64)
        logger.info(f"Ciphertext length (bytes): {len(ciphertext_bytes)}")
        
        if len(ciphertext_bytes) == 64:
            logger.info("SUCCESS: Ciphertext length is correct (64 bytes).")
        else:
            logger.warning(f"Ciphertext length is {len(ciphertext_bytes)}, expected 64.")
            
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return

    # Test generate_bid_data
    price = 100
    try:
        logger.info(f"Generating bid data for Amount={amount}, Price={price}")
        bid_data = ZkProver.generate_bid_data(amount, price)
        logger.info(f"Bid Data: (Encrypted Amount, Encrypted Price, Range Proof)")
        
        encrypted_amount, encrypted_price, range_proof = bid_data
        
        if len(base64.b64decode(encrypted_amount)) == 64 and len(base64.b64decode(encrypted_price)) == 64:
             logger.info("SUCCESS: Bid data contains valid ciphertexts.")
             proof_bytes = base64.b64decode(range_proof)
             logger.info(f"Range Proof Present: {len(proof_bytes)} bytes")
        else:
             logger.warning("Bid data ciphertexts have incorrect length.")

    except Exception as e:
        logger.error(f"Bid generation failed: {e}")

if __name__ == "__main__":
    run_verification()
