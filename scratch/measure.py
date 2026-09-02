import time
import requests

BASE_URL = "http://localhost:8000/v1"
MERCHANT = "M00109"

def measure():
    print("Measuring performance...")
    
    # Wait for API if not started
    try:
        requests.get("http://localhost:8000/health")
    except:
        print("API not running. Please start FastAPI on port 8000.")
        return

    # 1. Merchant Scoring Latency
    start = time.time()
    res = requests.post(f"{BASE_URL}/score/merchant", json={"merchant_id": MERCHANT, "scoring_timestamp": "2024-03-31 00:00:00"})
    m_score_time = (time.time() - start) * 1000
    
    # 2. Network Retrieval Latency
    start = time.time()
    res = requests.post(f"{BASE_URL}/score/network", json={"merchant_id": MERCHANT, "scoring_timestamp": "2024-03-31 00:00:00"})
    n_score_time = (time.time() - start) * 1000
    
    # 3. Timeline Request Latency
    start = time.time()
    ts = ["2024-01-31 00:00:00", "2024-02-15 00:00:00", "2024-02-28 00:00:00", "2024-03-15 00:00:00", "2024-03-31 00:00:00"]
    res = requests.post(f"{BASE_URL}/score/merchant/timeline", json={"merchant_id": MERCHANT, "scoring_timestamps": ts})
    t_score_time = (time.time() - start) * 1000
    
    print(f"Merchant Scoring: {m_score_time:.2f} ms")
    print(f"Network Retrieval: {n_score_time:.2f} ms")
    print(f"Timeline Request: {t_score_time:.2f} ms")

if __name__ == "__main__":
    measure()
