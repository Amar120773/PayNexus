# MuleHunter: Novelty Statement

## What MuleHunter Is

MuleHunter is a **merchant mule-network intelligence** system. It detects coordinated merchant mule rings by analyzing the *temporal trajectory* of network formation rather than the static state of individual merchants or their graph topology.

## What MuleHunter Is NOT

- It is **not** a general-purpose fraud detection system.
- It is **not** a transaction-level anomaly detector.
- It is **not** a chargeback predictor.
- It is **not** a KYC verification tool.
- It does **not** claim to replace existing merchant risk scoring.

---

## Differentiating from Existing Approaches

### vs. Merchant-Level Fraud Scoring
Traditional merchant risk models score each merchant independently using features like transaction velocity, average ticket size, chargeback ratio, and refund rate. These features are calculated per-merchant without reference to other merchants. MuleHunter's contribution is the observation — validated in our synthetic experiments — that mule merchants are *designed* to pass individual-level checks. The fraud signal lives in the *relationships between merchants*, not in any single merchant's behavior. Our baseline experiment confirmed this: a behavior-only model achieved F1 = 0.156 with a 23.6% false positive rate.

### vs. Generic Anomaly Detection
Unsupervised anomaly detection (isolation forests, autoencoders) flags merchants whose feature distributions deviate from the population. This fails for mule detection because each individual mule merchant's features may be well within normal bounds. MuleHunter does not perform unsupervised anomaly detection. It uses a supervised classifier trained on labeled temporal trajectory features extracted from the bipartite merchant-entity graph.

### vs. Generic Graph Fraud Detection
Standard graph-based fraud detection uses static topological features: PageRank, betweenness centrality, community detection, and graph neural networks over a single snapshot of the entity graph. Our experiments proved that static graph features alone produce an **8.7% false positive rate** (Model C in our ablation), because legitimate merchant ecosystems (aggregator platforms, co-working spaces) are also densely connected. The precision was only 0.347. MuleHunter's evolution features raised precision to 0.781 by distinguishing *how* connections form, not merely *that* they exist.

### vs. Generic Transaction Fraud Detection
Transaction-level fraud systems (e.g., real-time authorization scoring) evaluate individual payment events for characteristics like velocity, geolocation mismatch, or card-testing patterns. MuleHunter operates at a fundamentally different granularity: it scores *merchants* over *multi-week windows* based on *inter-merchant coordination patterns*. It does not examine individual transaction payloads.

### vs. Static Merchant Risk Scoring
Static merchant risk scores are computed once (or infrequently) based on a merchant's cumulative profile: time since onboarding, total volume, category risk, and historical incident count. These scores do not capture the *dynamic formation* of mule rings. MuleHunter's point-in-time temporal approach means the same merchant can have a different risk score at different timestamps, reflecting the evolving state of their network connections.

---

## The Specific Combination

MuleHunter's approach is a specific combination of five elements. No single element is novel in isolation; the contribution is their integration into a single investigation workflow:

### 1. Merchant-to-Entity Bipartite Relationships
We model merchants and shared entities (devices, IPs) as a bipartite graph. Merchants that share the same device or IP are connected through the entity node. This is a standard graph modeling technique.

### 2. Temporal Network Evolution
Instead of computing graph features on a single snapshot, we extract features at three consecutive 30-day windows (T1, T2, T3) and compute **deltas** between them. This captures the *speed and direction* of network formation. Our experiments demonstrated that this single change — from static to temporal — improved precision from 0.347 to 0.710 (Model C → Model D).

### 3. Synchronized Entity Churn
We specifically measure the rate at which merchants simultaneously shed old infrastructure and acquire new shared infrastructure (device churn rate, IP churn rate between windows). This is a targeted feature inspired by the observation that mule rings must rapidly converge their operational infrastructure during the coordination phase.

### 4. Point-in-Time Investigation
Every inference request specifies an explicit `scoring_timestamp`. The system guarantees — and adversarial tests verify — that no data from after that timestamp influences the score. This enables investigators to "rewind" and understand when a network first became suspicious.

### 5. Network-Isolated Evaluation
Our train/test split isolates entire mule networks, not individual merchants. This prevents the common graph-ML mistake of leaking test-network structure into training-time graph features. We documented and remediated an initial instance of exactly this leakage.

---

## Honest Boundaries

**What we have demonstrated (on synthetic data):**
- Temporal evolution features produce dramatically better precision and recall than static alternatives.
- The approach achieves 86.5% recall at 1.5% FPR on our synthetic dataset.
- Point-in-time scoring is temporally safe (adversarially verified).

**What we have NOT demonstrated:**
- Performance on real payment data.
- Robustness to real-world data drift, API latency, or adversarial evasion.
- Superiority over production-grade systems currently deployed at Razorpay or peer companies.
- Detection speed faster than the 60-day minimum observation window.
