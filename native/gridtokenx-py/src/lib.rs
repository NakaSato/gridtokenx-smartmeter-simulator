use pyo3::prelude::*;
use solana_zk_token_sdk::{
    encryption::{
        elgamal::{ElGamalKeypair, ElGamalCiphertext},
        pedersen::{PedersenOpening, PedersenCommitment},
    },
    instruction::range_proof::RangeProofU64Data,
    zk_token_elgamal::pod,
};
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use bytemuck::bytes_of;

#[pyclass]
struct ZkProver {
    // We don't need persistent state for now, just static methods effectively
}

#[pymethods]
impl ZkProver {
    #[new]
    fn new() -> Self {
        ZkProver {}
    }

    /// Generate a 64-byte ElGamal ciphertext for a given amount
    /// Returns: base64 encoded string of the ciphertext (64 bytes)
    #[staticmethod]
    fn encrypt_amount(amount: u64) -> PyResult<String> {
        let keypair = ElGamalKeypair::new_rand();
        let pubkey = keypair.pubkey();
        
        // Encrypt logic using SDK
        // We use a simplified encryption just for the ciphertext part (commitment + handle)
        // But the API expects just 64 bytes... wait.
        // ElGamal Ciphertext is 64 bytes (Commitment(32) + Handle(32))
        
        let ciphertext = pubkey.encrypt(amount);
        let bytes = ciphertext.to_bytes(); // 64 bytes
        
        Ok(BASE64.encode(bytes))
    }

    /// Generate an ElGamal ciphertext with a deterministic "mock" seed (demonstration only)
    /// Real ZK should be random, but for testing we might want stability? No, let's use random.
    
    /// Generate a confidential bid payload (encrypted price and amount) with Range Proof for amount
    /// Returns: (encrypted_amount, encrypted_price, amount_range_proof)
    #[staticmethod]
    fn generate_bid_data(amount: u64, price: u64) -> PyResult<(String, String, String)> {
        // Ephemeral keys for encryption
        let keypair = ElGamalKeypair::new_rand();
        let pubkey = keypair.pubkey();

        // 1. Setup for Amount with explicit opening for Range Proof
        let amount_opening = PedersenOpening::new_rand();
        let amount_cipher = pubkey.encrypt_with(amount, &amount_opening);
        
        // Extract commitment from ciphertext for the proof
        // ElGamalCiphertext = (PedersenCommitment, DecryptHandle)
        let amount_commitment = amount_cipher.commitment;

        // Generate Range Proof for Amount
        let amount_proof_data = RangeProofU64Data::new(&amount_commitment, amount, &amount_opening)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Proof generation failed: {:?}", e)))?;
        
        let amount_proof_bytes = bytes_of(&amount_proof_data.proof);

        // 2. Encrypt Price (simple encryption, no proof needed yet)
        let price_cipher = pubkey.encrypt(price);

        Ok((
            BASE64.encode(amount_cipher.to_bytes()),
            BASE64.encode(price_cipher.to_bytes()),
            BASE64.encode(amount_proof_bytes)
        ))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn gridtokenx_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ZkProver>()?;
    Ok(())
}
