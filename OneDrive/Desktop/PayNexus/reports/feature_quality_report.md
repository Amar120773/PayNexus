# MuleHunter Feature Quality & Leakage Audit Report

**Audit Summary**: Evaluated 72 features across 500 merchants.

## 1. Data Completeness & Integrity
- **Total Merchants**: `500`
- **Total Engineered Features**: `72`
- **Duplicate Merchant IDs**: `0`
- **Duplicate Feature Rows**: `0`
- **Missing Value Columns**: `0`
- **Infinite Value Columns**: `0`

> [!NOTE]
> Zero missing values detected across all engineered feature columns.

## 2. Low-Variance & Constant Feature Detection
- **Constant Features Detected**: `0`
All engineered features demonstrate positive variance.

## 3. Multicollinearity Analysis (|r| > 0.95)
- **Highly Correlated Feature Pairs**: `19`

| Feature A | Feature B | Pearson Correlation | Explanation |
| :--- | :--- | :--- | :--- |
| `transaction_count` | `unique_customer_count` | `0.9713` | Expected structural overlap between graph topology or activity aggregates. |
| `total_transaction_volume` | `total_settlement_volume` | `0.9991` | Expected structural overlap between graph topology or activity aggregates. |
| `average_transaction_amount` | `average_daily_volume` | `0.9554` | Expected structural overlap between graph topology or activity aggregates. |
| `average_transaction_amount` | `average_transaction_amount_zscore_vs_peers` | `0.9569` | Expected structural overlap between graph topology or activity aggregates. |
| `unique_customer_count` | `active_days_count` | `0.9705` | Expected structural overlap between graph topology or activity aggregates. |
| `unique_customer_count` | `shared_customer_count` | `0.9787` | Expected structural overlap between graph topology or activity aggregates. |
| `unique_customer_count` | `active_days_ratio` | `0.9705` | Expected structural overlap between graph topology or activity aggregates. |
| `unique_device_count` | `shared_device_count` | `0.9694` | Expected structural overlap between graph topology or activity aggregates. |
| `unique_ip_count` | `shared_ip_count` | `0.9586` | Expected structural overlap between graph topology or activity aggregates. |
| `active_days_count` | `shared_customer_count` | `0.9632` | Expected structural overlap between graph topology or activity aggregates. |
| `active_days_count` | `active_days_ratio` | `1.0` | Expected structural overlap between graph topology or activity aggregates. |
| `failure_rate` | `failure_rate_zscore_vs_peers` | `0.9789` | Expected structural overlap between graph topology or activity aggregates. |
| `refund_rate` | `refund_rate_zscore_vs_peers` | `0.9578` | Expected structural overlap between graph topology or activity aggregates. |
| `shared_customer_count` | `active_days_ratio` | `0.9632` | Expected structural overlap between graph topology or activity aggregates. |
| `connected_merchant_count` | `merchant_degree` | `1.0` | Expected structural overlap between graph topology or activity aggregates. |
| `connected_merchant_count` | `weighted_network_degree` | `0.9567` | Expected structural overlap between graph topology or activity aggregates. |
| `merchant_degree` | `weighted_network_degree` | `0.9567` | Expected structural overlap between graph topology or activity aggregates. |
| `shared_customer_volume_ratio` | `customer_sharing_concentration` | `0.9584` | Expected structural overlap between graph topology or activity aggregates. |
| `transaction_count_zscore_vs_peers` | `unique_customer_count_zscore_vs_peers` | `0.9752` | Expected structural overlap between graph topology or activity aggregates. |

## 4. Ground-Truth Label Leakage & Suspicion Audit
- **Forbidden Target Columns Found**: `0`
> [!IMPORTANT]
> PASS: No ground truth label columns (`is_mule`, `mule_type`, `network_id`) are present in the feature table.

- **Suspicious Features (|r_target| > 0.90)**: `0`
No single feature provides an artificial shortcut or trivial separability for mule classification.
