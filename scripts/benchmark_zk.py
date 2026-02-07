import time
import asyncio
from gridtokenx_py import ZkProver

def benchmark_zk_proofs(n=100):
    print(f"Benchmarking ZK Proof Generation for {n} proofs...")
    
    start_time = time.time()
    for i in range(n):
        # Scale: amount in Wh (int), price in cents (int)
        amount = 5000 + i
        price = 25
        
        # This is the CPU intensive part
        ZkProver.generate_bid_data(amount, price)
        
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / n
    
    print(f"Total time for {n} proofs: {total_time:.4f}s")
    print(f"Average time per proof: {avg_time:.4f}s")
    print(f"Projected time for 100 meters: {avg_time * 100:.4f}s")

if __name__ == "__main__":
    benchmark_zk_proofs(100)
