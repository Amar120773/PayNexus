# MuleHunter: Coordination Intelligence Layer Experiment

## 1. Hypothesis
**"Raw merchant connectivity is insufficient for identifying mule networks because legitimate businesses can share infrastructure. Coordinated behavior across relationships may provide stronger evidence of mule activity."**

This experiment sought to move beyond raw graph topology by engineering features that measure the rarity of relationships and the degree of behavioral coordination between merchants sharing those relationships.

## 2. Feature Definitions
We engineered the following Coordination Intelligence Layer features, strictly adhering to test-set leakage boundaries:
- **Relationship Rarity (`avg_ip_rarity`, `avg_device_rarity`, `avg_customer_rarity`)**: Measures the IDF (Inverse Document Frequency) of entities used by a merchant. High rarity indicates usage of isolated, dedicated infrastructure, calculated as `1 / entity_merchant_frequency`.
- **Infrastructure Dependence (`shared_ip_volume_ratio`, `shared_device_volume_ratio`, `shared_customer_volume_ratio`)**: The percentage of a merchant's total transaction volume that flows through entities shared by at least one other merchant.
- **Temporal Burstiness (`volume_burstiness`)**: The Gini coefficient of a merchant's daily transaction volume, capturing intense synchronized activity windows.

## 3. Data-Generation Changes
The synthetic dataset was scaled and updated to strictly enforce the presence of benign shared infrastructure:
- **Scale**: Increased to 5,000 merchants, 150,000 transactions, and 75 mule networks.
- **Benign Aggregators**: Explicitly added dense legitimate clustering where 40% of merchants randomly share tight clusters of entities (e.g., shared office networks, aggregator platforms) without malicious behavior.
- **Subtle Mules**: Mule injection was updated to ensure that malicious networks combine multiple subtle signals (rare entities + temporal spikes + volume).

## 4. Experimental Design
A rigorous 5-way ablation study was conducted using the leakage-safe simulated batch progression framework.
- **Model A**: Behavior Only (Baseline)
- **Model B**: Behavior + Raw Network
- **Model C**: Behavior + Relationship Rarity
- **Model D**: Behavior + Coordination
- **Model E**: Behavior + Network + Coordination (Full)

## 5. Results & 6. Ablation
Evaluating on unseen test splits (strict network-level holdout):

| Model | Precision | Recall | F1 Score | ROC-AUC | FPR | Network Recall |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Model A: Behavior (Baseline)** | 0.0290 | 0.4000 | 0.0541 | 0.6095 | 35.26% | 100.0% |
| **Model B: Behavior + Raw Net** | 0.0348 | 0.8000 | 0.0667 | 0.6653 | 58.42% | 100.0% |
| **Model C: Behavior + Rarity** | 0.0238 | 0.4000 | 0.0449 | 0.5853 | 43.16% | 100.0% |
| **Model D: Behavior + Coord** | 0.0220 | 0.4000 | 0.0417 | 0.5316 | 46.84% | 100.0% |
| **Model E: Full Architecture** | 0.0286 | 0.6000 | 0.0545 | 0.6084 | 53.68% | 100.0% |

**Key Finding:** The Coordination (Model D) and Rarity (Model C) feature subsets *actively harmed* precision and F1 compared to the Baseline, while significantly increasing the False Positive Rate (FPR).

## 7. False-Positive Analysis
Why did coordination features fail? The error analysis on False Positives reveals:
- **Genuine Behavioral Similarity**: Legitimate merchants sharing a platform (e.g., 5 restaurants on a food-delivery aggregator) inherently possess high `shared_device_volume_ratio` (100% of their volume goes through the aggregator's infrastructure).
- **Temporal Coordination**: These same restaurants experience natural, synchronized volume spikes (e.g., Friday night dinners), leading to high `volume_burstiness`.
- **Conclusion**: Coordination signals for benign aggregators look statistically identical to malicious mule networks in this dataset.

## 8. False-Negative Analysis
- Mule networks employing `SHARED_INFRASTRUCTURE` alone without extreme volume spikes were missed by the Rarity and Coordination models, because the rarity signal was drowned out by the sheer volume of legitimate merchants utilizing long-tail, low-frequency devices organically.

## 9. Network-Level Evaluation
All models successfully flagged at least one merchant in the held-out mule networks (`Network Recall = 100.0%`). However, this comes at the cost of immense network-level false positives, where entire benign aggregator clusters are flagged as mule syndicates.

## 10. Limitations
- **Graph Expressiveness**: Standard ML features (ratios, averages, Gini coefficients) struggle to capture the complex, multi-hop sub-graph structures required to differentiate a benign hub-and-spoke aggregator from a malicious dense-mesh mule ring.

## 11. Final Conclusion

**C. COORDINATION SIGNAL NOT SUPPORTED**

The hypothesis that behavioral coordination and relationship rarity provide stronger evidence than raw topology is fundamentally rejected for this dataset. Legitimate shared-infrastructure merchants exhibit organic behavioral coordination (similar timing, identical shared entities, high volume through shared pipes) that perfectly mimics the engineered mule signals. Adding coordination features only serves to further confuse the model, increasing the False Positive Rate without improving legitimate detection.
