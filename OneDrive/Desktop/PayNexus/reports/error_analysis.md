# MuleHunter: Post-Remediation Error Analysis

## 1. Confusion Matrix (Held-out Test Set)
- **True Positives (TP)**: 2
- **False Positives (FP)**: 68
- **True Negatives (TN)**: 122
- **False Negatives (FN)**: 3

- **Legitimate merchants flagged**: 68
- **Mule merchants missed**: 3

## 2. False Positive Analysis (Top 30)
| merchant_id | predicted_risk | actual | weighted_network_degree | unique_ip_count | pagerank_score | active_days_ratio | avg_tx_per_customer | ip_sharing_concentration | device_sharing_concentration | customer_sharing_concentration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M0487 | 98.4% | 0 | 1028.00 | 46.00 | 0.01 | 0.90 | 1.81 | 0.98 | 1.00 | 0.98 |
| M0424 | 98.4% | 0 | 970.00 | 27.00 | 0.01 | 0.90 | 1.82 | 1.00 | 0.97 | 0.98 |
| M0394 | 98.0% | 0 | 184.00 | 9.00 | 0.00 | 0.16 | 1.14 | 1.00 | 0.91 | 1.00 |
| M0431 | 97.8% | 0 | 119.00 | 7.00 | 0.00 | 0.11 | 1.10 | 1.00 | 0.86 | 1.00 |
| M0464 | 97.8% | 0 | 214.00 | 11.00 | 0.00 | 0.14 | 1.00 | 1.00 | 1.00 | 1.00 |
| M0077 | 97.5% | 0 | 172.00 | 9.00 | 0.00 | 0.16 | 1.14 | 1.00 | 1.00 | 1.00 |
| M0039 | 97.5% | 0 | 200.00 | 9.00 | 0.00 | 0.23 | 1.25 | 1.00 | 0.89 | 1.00 |
| M0142 | 97.4% | 0 | 845.00 | 27.00 | 0.01 | 0.89 | 1.75 | 1.00 | 0.97 | 0.99 |
| M0101 | 97.3% | 0 | 387.00 | 14.00 | 0.00 | 0.48 | 1.33 | 0.93 | 0.93 | 1.00 |
| M0289 | 97.3% | 0 | 455.00 | 18.00 | 0.01 | 0.78 | 2.84 | 1.00 | 1.00 | 0.95 |
| M0444 | 97.2% | 0 | 624.00 | 16.00 | 0.01 | 0.72 | 1.55 | 1.00 | 1.00 | 0.99 |
| M0075 | 97.2% | 0 | 545.00 | 15.00 | 0.01 | 0.67 | 1.69 | 1.00 | 1.00 | 0.98 |
| M0203 | 97.1% | 0 | 569.00 | 24.00 | 0.01 | 0.57 | 1.55 | 1.00 | 1.00 | 1.00 |
| M0069 | 97.0% | 0 | 167.00 | 8.00 | 0.00 | 0.16 | 1.23 | 1.00 | 1.00 | 1.00 |
| M0147 | 97.0% | 0 | 789.00 | 26.00 | 0.01 | 0.83 | 1.62 | 0.96 | 1.00 | 0.99 |
| M0333 | 96.9% | 0 | 220.00 | 10.00 | 0.00 | 0.29 | 1.25 | 1.00 | 1.00 | 1.00 |
| M0013 | 96.9% | 0 | 275.00 | 12.00 | 0.00 | 0.29 | 1.09 | 1.00 | 1.00 | 0.97 |
| M0214 | 96.9% | 0 | 451.00 | 14.00 | 0.01 | 0.56 | 1.28 | 1.00 | 1.00 | 1.00 |
| M0254 | 96.8% | 0 | 479.00 | 13.00 | 0.01 | 0.62 | 1.55 | 0.92 | 1.00 | 1.00 |
| M0176 | 96.8% | 0 | 532.00 | 13.00 | 0.01 | 0.62 | 1.63 | 1.00 | 1.00 | 1.00 |
| M0061 | 96.8% | 0 | 183.00 | 7.00 | 0.00 | 0.18 | 1.23 | 1.00 | 1.00 | 0.92 |
| M0347 | 96.7% | 0 | 428.00 | 17.00 | 0.00 | 0.51 | 1.40 | 1.00 | 1.00 | 1.00 |
| M0410 | 96.7% | 0 | 535.00 | 17.00 | 0.01 | 0.81 | 2.18 | 1.00 | 0.93 | 1.00 |
| M0290 | 96.7% | 0 | 167.00 | 7.00 | 0.00 | 0.12 | 1.00 | 1.00 | 1.00 | 1.00 |
| M0349 | 96.7% | 0 | 116.00 | 7.00 | 0.00 | 0.10 | 1.12 | 1.00 | 1.00 | 1.00 |
| M0015 | 96.7% | 0 | 703.00 | 16.00 | 0.01 | 0.70 | 1.42 | 1.00 | 0.97 | 0.99 |
| M0076 | 96.6% | 0 | 334.00 | 9.00 | 0.00 | 0.46 | 1.37 | 1.00 | 1.00 | 0.98 |
| M0470 | 96.5% | 0 | 339.00 | 9.00 | 0.00 | 0.42 | 1.20 | 1.00 | 1.00 | 0.98 |
| M0405 | 96.4% | 0 | 493.00 | 29.00 | 0.01 | 0.72 | 2.69 | 1.00 | 1.00 | 1.00 |
| M0395 | 96.4% | 0 | 202.00 | 10.00 | 0.00 | 0.17 | 1.00 | 1.00 | 1.00 | 0.94 |

## 3. Feature Distributions (Train Set)
| Feature | Mule Mean | Legit Mean |
| --- | --- | --- |
| weighted_network_degree | 68.94 | 15.44 |
| unique_ip_count | 10.31 | 3.21 |
| pagerank_score | 0.01 | 0.00 |
| active_days_ratio | 0.27 | 0.06 |
| avg_tx_per_customer | 1.21 | 0.98 |
| ip_sharing_concentration | 0.63 | 0.65 |
| device_sharing_concentration | 0.67 | 0.64 |
| customer_sharing_concentration | 0.72 | 0.66 |

## 4. Remediation Verdict
> [!IMPORTANT]
> **LEAKAGE REMEDIATION SUCCESSFUL:**
> The structural leakage where test graph edges inflated training network features has been fixed.
> Graph projection is now computed **per-split** using subgraphs. The model performance now reflects reality (F1 ~0.05) rather than the impossible 100% recall seen previously.
