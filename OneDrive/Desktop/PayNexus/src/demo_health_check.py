import sys
import requests
import time
from pathlib import Path

def print_status(check, passed, details=""):
    status = "PASS" if passed else "FAIL"
    color = "\033[92m" if passed else "\033[91m"
    end = "\033[0m"
    print(f"[{color}{status}{end}] {check}")
    if not passed and details:
        print(f"       -> {details}")

def main():
    print("="*50)
    print("MuleHunter Demo Health Check")
    print("="*50)
    
    passed_all = True
    
    # 1. Artifacts
    print("\nChecking Artifacts...")
    model_exists = Path("artifacts/model.pkl").exists()
    print_status("Model artifact exists", model_exists)
    if not model_exists: passed_all = False
    
    meta_exists = Path("artifacts/model_metadata.json").exists()
    print_status("Threshold artifact exists", meta_exists)
    if not meta_exists: passed_all = False
    
    # 2. Datasets
    print("\nChecking Dataset...")
    data_dir = Path("data/synthetic_v2")
    m_exists = (data_dir / "merchant_labels.csv").exists()
    t_exists = (data_dir / "transactions.csv").exists()
    r_exists = (data_dir / "relationships.csv").exists()
    dataset_exists = m_exists and t_exists and r_exists
    print_status("Frozen synthetic dataset exists", dataset_exists)
    if not dataset_exists: passed_all = False
    
    # 3. API Health
    print("\nChecking API...")
    api_running = False
    try:
        res = requests.get("http://localhost:8000/health", timeout=2)
        if res.status_code == 200:
            api_running = True
    except:
        pass
    
    print_status("API is running on port 8000", api_running, "Start with: uvicorn src.api.app:app")
    if not api_running: passed_all = False
    
    # 4. API Endpoints
    if api_running:
        try:
            m_res = requests.post("http://localhost:8000/v1/score/merchant", json={"merchant_id": "M00109", "scoring_timestamp": "2024-03-31"})
            print_status("Merchant scoring endpoint", m_res.status_code == 200)
            if m_res.status_code != 200: passed_all = False
            
            n_res = requests.post("http://localhost:8000/v1/score/network", json={"merchant_id": "M00109", "scoring_timestamp": "2024-03-31"})
            print_status("Network scoring endpoint", n_res.status_code == 200)
            if n_res.status_code != 200: passed_all = False
            
            t_res = requests.post("http://localhost:8000/v1/score/merchant/timeline", json={"merchant_id": "M00109", "scoring_timestamps": ["2024-03-31"]})
            print_status("Timeline scoring endpoint", t_res.status_code == 200)
            if t_res.status_code != 200: passed_all = False
            
            # Ground Truth Check
            if m_res.status_code == 200:
                data = m_res.json()
                no_leakage = "is_mule" not in data and "mule_type" not in data
                print_status("Ground-truth safely isolated", no_leakage, "Labels leaked in API!")
                if not no_leakage: passed_all = False
                
        except Exception as e:
            print_status("API Endpoint tests", False, str(e))
            passed_all = False
    
    print("\n" + "="*50)
    if passed_all:
        print("\033[92mALL SYSTEMS GO. DEMO IS READY.\033[0m")
        sys.exit(0)
    else:
        print("\033[91mHEALTH CHECK FAILED. FIX ISSUES BEFORE DEMO.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
