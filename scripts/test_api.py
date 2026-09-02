import requests
import time
import sys

base_url = 'http://localhost:8000/v1'
merchants = ['M00109', 'M00115', 'M00002']
ts = '2026-03-31 00:00:00'

print('--- API VERIFICATION ---')
for m in merchants:
    start = time.time()
    try:
        res_score = requests.post(f'{base_url}/score/merchant', json={'merchant_id': m, 'scoring_timestamp': ts})
        score_latency = time.time() - start
        
        start = time.time()
        res_explain = requests.post(f'{base_url}/explain/merchant', json={'merchant_id': m, 'scoring_timestamp': ts})
        explain_latency = time.time() - start
        
        print(f'\nMerchant: {m}')
        print(f'Score Status: {res_score.status_code}, Latency: {score_latency*1000:.1f}ms')
        if res_score.status_code == 200:
            data = res_score.json()
            print(f'  Probability: {data["probability"]:.4f}')
            print(f'  Risk Band: {data["risk_band"]}')
            
        print(f'Explain Status: {res_explain.status_code}, Latency: {explain_latency*1000:.1f}ms')
    except Exception as e:
        print(f"Error testing {m}: {e}")
