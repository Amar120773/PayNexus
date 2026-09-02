import pandas as pd

def find_merchants():
    labels = pd.read_csv("data/synthetic_v2/merchant_labels.csv")
    tx = pd.read_csv("data/synthetic_v2/transactions.csv")
    rels = pd.read_csv("data/synthetic_v2/relationships.csv")
    
    mules = labels[labels["is_mule"] == 1]
    legit = labels[labels["is_mule"] == 0]
            
    print("\nLegit Candidates:")
    for m in legit.head(100)["merchant_id"]:
        m_tx = len(tx[tx["merchant_id"] == m])
        m_rels = len(rels[rels["merchant_id"] == m])
        if m_tx > 200 and m_rels > 4:
            print(f"{m} - tx: {m_tx}, rels: {m_rels}")
            break
            
    if "mule_type" in labels.columns:
        type_d = labels[labels["mule_type"] == "D"]
        if not type_d.empty:
            print("\nType D Candidates:")
            for m in type_d.head(5)["merchant_id"]:
                print(f"{m} - tx: {len(tx[tx['merchant_id'] == m])}")

if __name__ == "__main__":
    find_merchants()
