# MuleHunter Phase 2: Post-Experiment Diagnosis

## Summary of Findings

Based on the evidence gathered throughout Phase 1 (Data Generation, Leakage Remediation, Peer Context Hypothesis, and Network Evolution Hypothesis), we have reached definitive conclusions about what makes a merchant mule network detectable.

### 1. What signals actually distinguish mule networks?
**[PROVEN BY EXPERIMENT]**
Mule networks are distinguished by the **synchronization of their temporal trajectories**. Specifically:
- **Synchronized Entity Churn:** Multiple merchants simultaneously adopting the same new IP or dropping old devices.
- **Correlated Behavioral Shifts:** Connected merchants simultaneously spiking in volume or refunds while altering their infrastructure.
- **Abnormal Network Growth Velocity:** The speed at which a new cluster forms, relative to its initial size.

### 2. Which signals are false positives?
**[PROVEN BY EXPERIMENT]**
- **Static Network Density:** High PageRank, clustering coefficients, and merchant degree are all highly prevalent in benign platforms (e.g., aggregators), leading to a massive FPR (up to 58% when used indiscriminately).
- **Absolute Behavior Spikes:** Fast volume growth or high refunds alone trigger false positives for legitimate seasonal or failing businesses.

### 3. Which mule lifecycle is easiest to detect?
**[PROVEN BY EXPERIMENT]**
- **Type B (Gradual Expansion)** is the easiest to detect (Recall: 97.4%). The sustained, linear addition of merchants to a shared infrastructure pool over multiple time windows creates a highly recognizable structural trajectory.
- **Type C (Infrastructure Convergence)** is also highly detectable (Recall: 91.8%) due to the massive, simultaneous IP/Device churn across previously unconnected entities.

### 4. Which lifecycle is hardest?
**[PROVEN BY EXPERIMENT]**
- **Type D (Behavioral Transition)** is the hardest (Recall: 65.6%). Because these mules maintain a completely stable, legitimate-looking structural network, the model cannot rely on structural $\Delta$ features. It must rely solely on behavioral $\Delta$s, which frequently overlap with legitimate business struggles.

### 5. Does evolution improve over static behavior?
**[PROVEN BY EXPERIMENT]**
Yes. Relying on static behavior yields an F1 score of 0.156. Introducing temporal behavior and structural evolution pushes the F1 score to 0.820.

### 6. Does evolution improve over static network topology?
**[PROVEN BY EXPERIMENT]**
Yes. Static network features suffer from terrible precision (0.347) because they penalize all dense ecosystems. Evolving network features double the precision to 0.781 by distinguishing between naturally formed dense ecosystems and artificially coordinated dense ecosystems.

### 7. How much does FPR change?
**[PROVEN BY EXPERIMENT]**
The False Positive Rate drops from **23.6%** (Static Behavior) and **8.7%** (Static Network) down to an extremely viable **1.5%** (Behavior + Network Evolution).

### 8. How much network recall changes?
**[PROVEN BY EXPERIMENT]**
Recall improves dramatically from **40.3%** (Behavioral Baseline) to **86.5%** (Combined Evolution).

### 9. How early can detection occur?
**[SUPPORTED BUT UNCERTAIN]**
The current experiment proves detection is highly effective when comparing 30-day disjoint snapshots (requiring 60 days of data). It remains uncertain whether this accuracy holds if the temporal window is compressed to rolling 7-day or 14-day snapshots to catch mules faster.

### 10. Which features should survive into the final product?
**[PROVEN BY EXPERIMENT]**
- Structural Trajectory: `network_growth_velocity`, `ip_churn_rate`, `device_churn_rate`
- Behavioral Trajectory: `volume_delta`, `refund_delta`

**[NOT SUPPORTED]**
- Raw network degree, raw PageRank, betweenness centrality, and simple unsupervised Z-scores.

---

## Recommended Technical Architecture for MVP

Given these findings, the MuleHunter MVP for the Razorpay Buildathon should NOT be a simple tabular classifier on a static merchant database. It must be a **Temporal Graph Analytics Platform**.

**Architecture Blueprint:**
1. **Data Ingestion (Event Ledger):** Treat raw data not as a static table, but as an append-only event stream (transactions, logins).
2. **Dynamic Graph Construction:** Use a graph database/library (like NetworkX or Neo4j) to project the Bipartite Merchant-Entity graph dynamically for requested rolling time windows (e.g. `t`, `t - 14d`, `t - 28d`).
3. **Trajectory Feature Store:** A pipeline that continuously computes the $\Delta$ between these rolling windows for each merchant's local neighborhood.
4. **XGBoost Inference:** The model scores merchants based on these trajectory deltas rather than their absolute state.
5. **Streamlit UI (Network Evolution Dashboard):** 
   - Instead of just showing a static network diagram, the UI MUST feature a **Time Slider**. 
   - Analysts need to see the network animate and visually observe the infrastructure convergence or rapid expansion to understand *why* the model flagged the cluster.
