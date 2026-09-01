# Dataset Comparison: V1 vs V2

To effectively evaluate the **Network Evolution Intelligence** hypothesis, we developed a parallel synthetic data pipeline (`src/data_generation_v2`). This document explicitly outlines the differences between the original static graph dataset (V1) and the new temporal graph dataset (V2).

## Core Architectural Differences

| Property | Dataset V1 (Static) | Dataset V2 (Evolution) |
| :--- | :--- | :--- |
| **Merchant-Entity Relationships** | Permanent static pools assigned at initialization. | Time-bounded intervals (`start_time`, `end_time`). |
| **Relationship Churn** | No. A merchant never adds or drops an IP/device. | Yes. Probabilistic natural device/IP churn implemented. |
| **Network Growth** | No. Density remains identical from Day 1 to Day 90. | Yes. Networks naturally add and lose merchants over time. |
| **Benign Ecosystem Evolution** | Limited to transaction volume variance. | Modeled explicitly (e.g. `BENIGN_FAST_GROWTH`, `BENIGN_SEASONAL_SPIKE`). |
| **Mule Lifecycle** | Static clusters injected at Day 1. | 4 explicit dynamic lifecycles (Types A, B, C, D). |
| **Temporal Evaluation boundaries** | Incomplete. Point-in-time state could not be queried. | Explicit Point-in-time snapshotting (T1, T2, T3) via `events.csv` state reconstruction. |

## Why V2 Was Necessary
In Dataset V1, if a test-set merchant shared an IP with a training-set merchant on Day 85, that connection implicitly existed on Day 1 (due to the static assignment). This meant temporal trajectory features were impossible to calculate without exposing the model to structural leakage. 

Dataset V2 resolves this by:
1. **Generating an explicit `events.csv` ledger.**
2. **Reconstructing bipartite graphs dynamically** only for the specific temporal snapshot (e.g., T1 = Days 1-30).
3. **Ensuring probabilistic overlap.** In V1, any fast network formation was a guaranteed mule. In V2, legitimate platforms also exhibit `BENIGN_FAST_GROWTH`, forcing the model to rely on combinations of behavior, relationship creation, and entity churn to separate benign ecosystems from mules.
