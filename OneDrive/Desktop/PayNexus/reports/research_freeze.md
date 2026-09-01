# MuleHunter Research Freeze Document

**IMPORTANT DISCLAIMER:**
All findings, metrics, and conclusions documented below are derived exclusively from **synthetic-data experiments** specifically engineered for the Razorpay Buildathon. These results **DO NOT** represent real Razorpay production performance or real-world incidence rates. 

## 1. Supported Findings
- **Evolution beats Static Topology:** Analyzing how merchant relationships form over time is vastly superior to analyzing static network snapshots, as the latter overwhelmingly penalizes legitimate dense ecosystems (like aggregators).
- **Synchronized Entity Churn is a Primary Indicator:** Mule networks can be effectively distinguished by their coordinated shedding and acquiring of shared infrastructure (IPs and devices).
- **Legitimate Ecosystems Can Be Differentiated:** While legitimate platforms can grow as rapidly as mule rings, they rarely exhibit the highly synchronized, rapid convergence of multiple merchants onto the exact same isolated IP/Device pairs seen in injected mules.

## 2. Partially Supported Findings
- **Detection Lead Time:** Detection relies on temporal deltas (e.g., T1 $\rightarrow$ T2). The current experiment proves it works on disjoint 30-day windows (requiring 60 days of data). It is theoretically supported—but unproven—whether the window can be compressed to 7 or 14 rolling days to detect mules faster.

## 3. Known Limitations
- The model still struggles with merchants who maintain perfectly legitimate structural connections and only exhibit behavioral anomalies (Type D mules).
- Z-score based peer context (tested in Phase 1) is fragile on extremely small peer groups (e.g., 2 merchants sharing an IP).
- All experiments were run on a synthetic, probabilistically generated dataset; real-world data drift and API noise are not modeled.

## 4. Best-Performing Feature Families
- **Temporal Network Deltas:** `network_growth`, `ip_churn`, `device_churn`.
- **Temporal Behavioral Deltas:** `volume_delta`, `refund_delta`.

## 5. Worst-Performing Feature Families
- **Static Topological Metrics:** PageRank, betweenness centrality, global merchant degree, and clustering coefficients computed across the entire graph. (Resulted in >58% FPR).
- **Unnormalized Behavioral Metrics:** Absolute transaction volumes and absolute ticket sizes.

## 6. Best Mule Lifecycle
- **Gradual Expansion (Type B):** Achieved the highest recall (97.4%). The sustained, linear addition of merchants to a shared infrastructure pool over multiple time windows creates a highly recognizable structural trajectory.
- **Infrastructure Convergence (Type C):** Achieved 91.8% recall due to massive, simultaneous IP/Device churn.

## 7. Worst Mule Lifecycle
- **Behavioral Transition (Type D):** Achieved the lowest recall (65.6%). These merchants maintain a completely stable, legitimate-looking structural network, forcing the model to rely solely on behavioral $\Delta$s, which frequently overlap with struggling legitimate merchants.

## 8. Current FPR
- **1.5%** (For the combined structural + behavioral evolution model).

## 9. Current Network Recall
- **86.5%** (For the combined structural + behavioral evolution model).

## 10. Current Detection Lead Time
- Minimum **60 Days** (based on the T1 $\rightarrow$ T2 snapshot comparison).

## 11. Features Approved for MVP
- `network_growth_t1_t2`
- `network_growth_t2_t3`
- `ip_churn_t1_t2`
- `ip_churn_t2_t3`
- `device_churn_t1_t2`
- `device_churn_t2_t3`
- `volume_delta_t1_t2`
- `volume_delta_t2_t3`
- `refund_delta_t1_t2`
- `refund_delta_t2_t3`

## 12. Features Rejected from MVP
- `pagerank_score`
- `betweenness_centrality`
- `merchant_degree`
- `clustering_coefficient`
- Peer-relative unsupervised Z-scores (due to small-group fragility and signal overshadowing).

---
RESEARCH FROZEN.
