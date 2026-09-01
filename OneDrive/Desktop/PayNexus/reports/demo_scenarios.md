# Dashboard Demo Scenarios

This document outlines deterministic demo scenarios using the frozen synthetic V2 dataset for investigator demonstrations.

## 1. High-Risk Mule Network
**Merchant ID:** `M00109`
**Why Selected:** This merchant exhibits high transaction velocity and shares 5 infrastructure components (devices/IPs) with known illicit actors. It is strongly classified as a mule by the V2 model.
**Dashboard Functionality Demonstrated:**
- "HIGH RISK" alert band and score.
- Network Intelligence graph showing a densely connected 1-hop topology of high-risk neighbors.
- Case Summary guidance recommending immediate review.

## 2. Legitimate Highly-Connected Merchant
**Merchant ID:** `M00001`
**Why Selected:** A legitimate merchant with high transaction volume but standard, uncoordinated relationship sharing (e.g., standard shared IPs from a common ISP, rather than anomalous device churn).
**Dashboard Functionality Demonstrated:**
- "LOW RISK" band despite high transaction volume.
- Network graph showing connections to mostly low-risk/unclassified entities.
- Lack of behavioral coordination signals in the "Risk Evidence" tab.

## 3. Emerging Mule Network (Timeline Focus)
**Merchant ID:** `M00150`
**Why Selected:** This merchant begins the dataset acting normally (low transaction volume, standard devices) but transitions into coordinated activity (adding multiple shared devices rapidly around March 2024).
**Dashboard Functionality Demonstrated:**
- The interactive **Historical Risk Evolution** timeline.
- Selecting early timestamps (e.g. `2024-01-31`) shows a LOW risk score.
- Selecting later timestamps (e.g. `2024-03-31`) updates the dashboard point-in-time state to show HIGH risk, reflecting the sudden influx of anomalous connections.

## 4. Type-D Behavioral-Transition Blind Spot
**Merchant ID:** `M00492` (Placeholder for known Type-D entity)
**Why Selected:** As identified in the Phase 6 Blind Spot Analysis, Type-D mules exhibit slow-burn behavioral transitions that evade the current 30-day temporal feature window.
**Dashboard Functionality Demonstrated:**
- Shows the model's limitations visually: the Risk Timeline fails to cross the `0.3263` threshold because the feature extraction window resets.
- The analyst can manually use the Network Intelligence graph to see the expanding connections even though the automated risk score drops back to LOW.
**Relevant Limitation:** Highlights why the frozen model struggles with long-term memory patterns, demonstrating the dashboard's utility as a manual safety net.
