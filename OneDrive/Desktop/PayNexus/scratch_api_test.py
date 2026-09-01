import requests

for m_id in ["M00109", "M00150", "M00001"]:
    payload = {
        "merchant_id": m_id,
        "scoring_timestamp": "2024-03-31 00:00:00"
    }
    try:
        resp = requests.post("http://localhost:8000/v1/score/merchant", json=payload)
        data = resp.json()
        ev = data.get("evidence_features", {})
        temporal = {k: v for k, v in ev.items() if 'delta' in k or 'velocity' in k or 'churn' in k or 'growth' in k or 'change' in k}
        print(f"--- {m_id} ---")
        for k, v in temporal.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(e)
