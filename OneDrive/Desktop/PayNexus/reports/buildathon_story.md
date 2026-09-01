# The MuleHunter Story

## 1. What is the problem?

Financial criminals use networks of seemingly legitimate merchant accounts — called **mule merchants** — to launder money through payment platforms. Each individual mule merchant may process normal-looking transactions, maintain valid KYC documentation, and generate ordinary refund rates. The fraud is invisible at the individual merchant level because the criminal strategy is inherently *collective*: it depends on coordination between multiple accounts sharing infrastructure, customers, and behavioral patterns.

## 2. Why are individual merchant fraud scores insufficient?

Traditional merchant risk scoring examines each merchant in isolation: transaction velocity, chargeback rate, ticket size, refund ratio. A mule merchant is specifically designed to pass these checks. The merchant's individual behavior is engineered to be unremarkable. The signal is not *what* the merchant does — it is *who it connects to* and *how those connections form over time*.

## 3. What is a mule network?

A mule network is a coordinated cluster of merchant accounts that share infrastructure (devices, IP addresses, settlement accounts) in patterns that differ from legitimate business ecosystems. The network exists to distribute illicit funds across multiple apparently independent accounts, reducing the per-merchant risk signal below detection thresholds.

## 4. Why does network structure matter?

Legitimate merchants share infrastructure for benign reasons: common payment gateways, platform aggregators, and co-working spaces. What distinguishes a mule network is not the *existence* of shared infrastructure but the *pattern* of sharing. Mule networks exhibit abnormally dense, synchronized infrastructure convergence among merchants that have no legitimate business reason to share those specific devices or IPs.

However, static network topology alone is insufficient. Our experiments proved that static graph features (PageRank, degree centrality, clustering coefficient) produce a **23.6% false positive rate** on our synthetic dataset because they penalize all dense ecosystems equally — including perfectly legitimate aggregator platforms.

## 5. Why does temporal evolution matter?

Mule networks do not appear fully formed. They *build* over time. A ring of five merchants simultaneously adopting the same three IP addresses over a 14-day period is structurally different from five merchants that have organically shared the same platform IP for 18 months.

MuleHunter's core insight — validated by experiment — is that **the trajectory of network formation** is a stronger signal than the network's static state. Specifically:

- **Synchronized entity churn**: Multiple merchants simultaneously dropping old devices and acquiring the same new ones.
- **Correlated behavioral shifts**: Connected merchants spiking in volume or refunds at the same time.
- **Abnormal network growth velocity**: The speed at which a cluster of merchants converges onto shared infrastructure.

## 6. What does MuleHunter uniquely detect?

MuleHunter is positioned as **merchant mule-network intelligence**. It does not attempt to be a general fraud detector, a transaction-level anomaly system, or a chargeback predictor.

It specifically answers the question: *"Is this group of merchants forming a coordinated network that resembles known mule-ring formation patterns?"*

## 7. How does the system work?

1. **Point-in-time data access**: All scoring occurs at a specific timestamp. The system mathematically guarantees that no future data influences a historical score.
2. **Temporal windowing**: For any scoring timestamp T, the system extracts three 30-day snapshots (T−90 to T−60, T−60 to T−30, T−30 to T) and computes delta features between them.
3. **Evolution features**: 10 features capture the trajectory of each merchant's behavior and network structure: volume deltas, refund deltas, network growth velocity, device churn rate, and IP churn rate across consecutive windows.
4. **Frozen model inference**: A LightGBM classifier, trained on network-isolated held-out splits to prevent structural leakage, scores each merchant.
5. **Investigator dashboard**: A Next.js frontend allows analysts to search merchants, view risk scores, inspect evidence features, explore risk timelines, and navigate the 1-hop network graph.

## 8. What evidence supports the approach?

All findings are from **synthetic-data experiments**. They do not represent production performance on real payment data.

| Metric | Behavioral Baseline | MuleHunter (Behavior + Network Evolution) |
| :--- | :--- | :--- |
| Precision | 0.097 | **0.781** |
| Recall | 0.403 | **0.865** |
| F1 Score | 0.156 | **0.820** |
| ROC-AUC | 0.612 | **0.973** |
| False Positive Rate | 23.6% | **1.5%** |

- **Network-isolated evaluation**: Train/test splits are by network, not by merchant. No test-network merchants appear in training graphs.
- **Leakage remediation**: An initial version with structural leakage (inflated to 100% recall) was identified, documented, and fully remediated.
- **Blind-spot analysis**: Type-D behavioral-transition mules achieve only 65.6% recall, a known and documented limitation.

## 9. What are the known limitations?

- **Synthetic data only**: All experiments use programmatically generated data. Real-world performance is unproven.
- **Type-D blind spot**: Merchants that maintain stable infrastructure but only shift their transaction behavior are harder to detect (65.6% recall vs. 97.4% for gradual-expansion mules).
- **60-day minimum detection window**: The current temporal architecture requires at least two 30-day windows of observation before a meaningful trajectory signal emerges. Faster detection with compressed windows is theoretically possible but unvalidated.
- **False positive residual**: Even at 1.5% FPR on synthetic data, scaling to millions of real merchants would produce substantial false positives requiring human triage.
- **No production validation**: The system has not been tested against real Razorpay merchant data, real mule networks, or real attack patterns.

## 10. Why is this relevant to Razorpay?

Razorpay onboards and serves millions of merchants. As a payment aggregator, Razorpay's merchant ecosystem naturally creates dense infrastructure-sharing patterns (shared payment gateways, common API endpoints, platform-level device fingerprints). This density is exactly the environment where mule networks can hide — and where traditional per-merchant scoring is most likely to miss coordinated fraud.

MuleHunter proposes a potential complementary intelligence layer: instead of replacing existing transaction-level risk systems, it could sit alongside them to answer the specific question of whether a group of merchants is behaving like a coordinated mule ring, using the temporal trajectory of their network formation as the primary signal.
