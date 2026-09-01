# Feasibility Analysis: Network Evolution Intelligence

## 1. Objective
To determine whether the existing PayNexus synthetic dataset supports the **Network Evolution Hypothesis**—specifically, whether analyzing the temporal deltas of network structure (new connections, relationship velocity, network growth) can distinguish camouflaged mule networks from legitimate shared-infrastructure ecosystems.

## 2. Experimental Setup
We divided the 90-day transaction dataset into three 30-day snapshots:
- **T1:** Days 1–30
- **T2:** Days 31–60
- **T3:** Days 61–90

For each snapshot, we calculated absolute structural metrics (active nodes, edges, shared IPs/devices) and behavioral metrics (volume, refund rates) for both Mule Networks and Benign Networks. We then calculated the $\Delta$ (delta) between T1 $\rightarrow$ T2 and T2 $\rightarrow$ T3.

## 3. Results (Averages per Network)

| Metric | Benign Ecosystems | Mule Networks |
| :--- | :--- | :--- |
| **$\Delta$ Nodes (T1 $\rightarrow$ T2)** | -0.003 | +0.100 |
| **$\Delta$ Edges (T1 $\rightarrow$ T2)** | -0.466 | -0.100 |
| **$\Delta$ Volume (T1 $\rightarrow$ T2)**| +13,097 | +2,092 |
| **$\Delta$ Refund Rate (T1 $\rightarrow$ T2)** | -0.43% | +0.58% |
| **$\Delta$ Nodes (T2 $\rightarrow$ T3)** | -0.053 | -0.100 |
| **$\Delta$ Edges (T2 $\rightarrow$ T3)** | +0.190 | -0.100 |
| **$\Delta$ Volume (T2 $\rightarrow$ T3)**| -15,328 | -9,200 |

*Note: The structural $\Delta$s for both classes are statistically zero. The only variance comes from whether a merchant randomly had zero transactions in a 30-day window.*

## 4. Addressing Core Questions

**1. Can mule networks be distinguished by their evolution?**
**No.** The current dataset cannot support this hypothesis because it does not simulate structural evolution. 

**2. Which temporal network features differ?**
Only the **behavioral features** (volume and refund rates) exhibit temporal deltas. The structural network features (edges, shared IPs, shared devices, new customer connections) exhibit zero meaningful change across the 90-day period.

**3. Which features also occur in benign ecosystems?**
Both Benign and Mule networks display completely static structural relationships over time.

**4. Are the differences statistically meaningful?**
**No.** The structural relationship velocity (`new_device_connections`, `network_growth_rate`) is effectively zero for all merchants.

**5. Can the signal be measured before the mule network reaches peak activity?**
**N/A.** Because there is no gradual network formation, there is no "early" structural signal to measure.

**6. Can the experiment support a network-level detection objective?**
**NO.** The current synthetic data architecture is fundamentally incompatible with Network Evolution Intelligence.

## 5. Root Cause Analysis
The synthetic data generator (`src/data_generation/generators.py`) utilizes a **static assignment model**. 
When the dataset is initialized, each merchant is permanently assigned a pool of device IDs and IP IDs (`merchant_device_pools` and `merchant_ip_pools`). Every transaction randomly samples from these static pools. 
Consequently, merchants do not "evolve" or dynamically form new relationships over time. They don't migrate to new infrastructure, nor do they sequentially onboard new entities. 

## 6. Conclusion & Recommendation
**VERDICT: NOT PROMISING (DATASET REDESIGN REQUIRED)**

Do **NOT** implement Network Evolution Intelligence on the current codebase.

To test this hypothesis, we would first need to completely overhaul the synthetic data generator to simulate **Dynamic Graph Evolution** (e.g., Markov chains for infrastructure migration, time-decaying relationships, and sequential merchant onboarding). Until the data reflects time-varying connectivity, any temporal graph features will simply be zero.
