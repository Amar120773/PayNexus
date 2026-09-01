# Experimental Design: The Coordination Hypothesis

## 1. The Hypothesis
**"Raw connectivity is not sufficient to identify merchant mule networks. Coordinated behavior across relationships is the stronger signal."**

Currently, MuleHunter relies on graph topology (e.g., PageRank, network degree) which merely captures the *size* and *density* of shared infrastructure. Because legitimate merchants frequently share infrastructure (payment gateways, SaaS platforms, regional IPs), they form dense, benign clusters that the model falsely flags as mules. 

The hypothesis asserts that malicious mule networks can be distinguished from benign clusters not by *if* they share entities, but by *how* they behave across those shared entities (Relationship Rarity and Behavioral Coordination).

## 2. Proposed Features

### A. Relationship Rarity Features
Benign sharing typically involves highly connected "hub" entities (e.g., a popular Shopify IP used by 1,000 merchants). Malicious sharing involves rare, dedicated entities (e.g., an IP used by exactly 4 merchants).
- **`rare_ip_sharing_score`**: For every shared IP, sum `1 / log(total_merchants_using_ip)`. High scores indicate sharing of obscure, dedicated IPs.
- **`rare_device_sharing_score`**: Similar IDF-style scoring for devices.
- *Why it indicates coordination:* Mules use dedicated shadow infra. Legitimate merchants use public/hub infra.
- *Leakage Risk:* High. The `total_merchants_using_entity` must be computed **strictly on the training split** to prevent test-set structural leakage.

### B. Behavioral Coordination Features
Mule networks don't just share entities; they force high volumes of coordinated transactions through them.
- **`shared_customer_volume_ratio`**: The percentage of a merchant's total transaction volume originating from customers they share with other merchants.
  - *Why:* The data generator forces 24-44% of mule transactions onto a core set of 6-13 shared customers.
- **`shared_infra_volume_ratio`**: The percentage of a merchant's transaction volume originating from shared IPs or Devices.
  - *Why:* Mules force 22-42% of volume through shared infra. Legitimate merchants might share an IP, but their volume is organically distributed.
- **`network_temporal_burst_overlap`**: Measures if a merchant's volume spikes occur in the exact same hour as their immediate graph neighbors.
  - *Why:* The generator injects `TEMPORAL_COORDINATION` by anchoring 10-18% of transactions across the network to a specific day and hour window.

All proposed features are strictly available at inference time (computable on split subgraphs) and directly map to the injected malicious topologies.

## 3. Synthetic Data Requirements
The current dataset (`merchants=500`, `transactions=10_000`, `mule_networks=10`) is too small to provide statistical confidence for advanced coordination features. 

**Recommendation: Redesign Dataset Sizing**
We must scale the dataset to ensure sufficient contrast between benign sharing and malicious coordination.
- **Merchants:** 5,000
- **Transactions:** 150,000
- **Mule Networks:** 75 (yielding ~500-600 mule merchants across various topologies).
- **Customers/Devices/IPs:** 10,000+ each to ensure a realistic sparse long-tail distribution for the rarity features to exploit.

The current `generators.py` logic successfully creates benign shared infrastructure (via `shared_fraction=0.10` in entity pools) and malicious coordination. We just need to scale the configuration.

## 4. Experimental Design
We will evaluate 5 distinct models using the leakage-safe simulated batch progression framework.

- **Model A (Baseline):** Behavioral features only (Volume, velocities, refunds).
- **Model B (Raw Network):** Behavior + current raw graph topology (Degree, PageRank, Concentration).
- **Model C (Rarity):** Behavior + Relationship Rarity features.
- **Model D (Coordination):** Behavior + Behavioral Coordination features.
- **Model E (Full Unified):** Behavior + Rarity + Coordination (No raw topology).

## 5. Evaluation Methodology
- **Metric Focus:** The primary success criteria will be **Precision** and **False Positive Rate (FPR)** at a fixed high recall, since the core issue is false positives.
- **Network-Level Evaluation:** We will track Network Recall and Network Precision.
- **Typology Breakdown:** We will report recall separately for `SHARED_INFRASTRUCTURE`, `SHARED_SETTLEMENT`, `CUSTOMER_OVERLAP`, and `TEMPORAL_COORDINATION` to understand which coordination features target which topologies.

## 6. Expected Failure Modes
1. **Rarity Noise:** In a finite synthetic dataset, a legitimate merchant might randomly share a rare IP simply due to the random number generator, leading to false positives.
2. **Temporal Coincidence:** Legitimate merchants in the same category (e.g., restaurants) have natural peak hours (e.g., 7 PM). The `network_temporal_burst_overlap` feature might accidentally penalize legitimate restaurants that happen to share a generic customer and spike at the same time.

## 7. Final Recommendation
**REDESIGN DATASET AND REDESIGN FEATURES.**
The current approach of relying on raw graph topology is fundamentally flawed for this domain because graph structure captures the *scale* of relationships but ignores the *context* and *intensity* of those relationships.

I recommend we proceed with generating a scaled-up dataset (5,000 merchants) and engineering the Rarity and Behavioral Coordination features as proposed above.
