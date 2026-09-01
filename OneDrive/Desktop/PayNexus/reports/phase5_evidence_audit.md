# Phase 5: Evidence Intelligence Redesign Audit

## Current Implementation
- **Location**: The evidence rendering is embedded within `dashboard/src/app/merchant/[merchantId]/page.tsx`.
- **Components**: `FeatureRow` function component handles individual signals. The tab content is rendered inside the `activeTab === "evidence"` condition.
- **Categorization**: Currently maps raw feature keys into `behavioral`, `network`, and `temporal` arrays.
- **Visuals**: Uses simple cards with `custom-scrollbar` and a basic `magnitude-bar`.

## Identified Weaknesses
- **Numerical Formatting**: The current `FeatureRow` arbitrarily multiplies `value * 100` and appends `%` for *all* features. This breaks for absolute counts (e.g., `shared_settlement_count`) or raw scores (e.g., `graph_pagerank_score`).
- **Zero Values**: Signals with a value of `0` take up the exact same visual weight and high-contrast typography as active signals, creating noise.
- **Hierarchy**: The Evidence tab lacks a "Why this merchant?" summarization block; it just dumps all categories into columns.
- **Filtering**: There is no way to filter the signals (no `[ALL] [BEHAVIORAL] ...` toggles).
- **Magnitude Bar**: `min(100, Math.abs(value) * 100)` is unsafe for features that don't operate on a `[0, 1]` or percentage scale.

## Proposed Investigator Workflow & Visual Hierarchy
1. **"Why this merchant?"**: The top of the Evidence tab will present a visually distinct area highlighting the absolute strongest signals (highest absolute values) across all categories.
2. **Evidence Filters**: Below the summary, a clean row of filters (`ALL`, `TEMPORAL`, `BEHAVIORAL`, `NETWORK`) to isolate signals.
3. **Smart Formatting**: 
   - Zero values will be muted (`0`, no bar, subdued text).
   - Percentages vs Counts will be formatted safely based on their keys (e.g., `_rate`, `_delta` as percentages, others as raw floats).
4. **Layout**: Move to a robust, asymmetric multi-column layout for desktop that intelligently collapses to a single column on mobile.
