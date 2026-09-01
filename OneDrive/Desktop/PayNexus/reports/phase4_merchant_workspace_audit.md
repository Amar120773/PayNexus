# Phase 4: Merchant Investigation Workspace Audit

## Current Strengths
- **Rich Data Connectivity**: The page successfully orchestrates the underlying API calls for `getMerchantMetadata`, `scoreMerchant`, `getMerchantTimeline`, and `getNetworkScore`.
- **Feature Labeling**: Has a good dictionary (`FEATURE_LABELS`) that translates raw API keys into human-readable text.
- **Breadcrumb Navigation**: Clearly allows navigation back to the Overview.

## Current Weaknesses
- **Generic Aesthetics**: The use of generic border radiuses, soft colors, and basic cards gives it a default Tailwind look rather than a premium investigation workstation.
- **Risk Score Presentation**: The circular SVG gauge is functional but lacks serious visual impact or editorial authority. It looks like a standard analytics dashboard widget.
- **Hidden Evidence**: The most critical aspect of the investigation (the raw feature signals) is buried inside tabs or small cards, without a clear hierarchy emphasizing "Why this merchant is risky".
- **Visual Homogeneity**: Everything is inside identical `.card` boxes. The hierarchy between the risk score and the technical metadata is flat.

## Components & Files Involved
- `dashboard/src/app/merchant/[merchantId]/page.tsx`
- (Relies on existing `RiskTimeline` and `NetworkGraph` components which will not be deeply redesigned in this phase).

## Proposed New Information Hierarchy
1. **Investigation Header**: `INVESTIGATION / MERCHANT [M00109]` with strong editorial `Newsreader` font and `JetBrains Mono` IDs.
2. **Visual Risk Anchor**: A massive, bold presentation of the risk score (e.g., `0.9421`) and semantic risk band, discarding the circular SVG for a more physical, editorial gauge or typographic scale.
3. **"Why This Merchant?" (Evidence Preview)**: An immediate, front-and-center list of the top 3-5 driving risk factors using `magnitude-bars`, ensuring the investigator understands the risk in seconds without clicking tabs.
4. **Investigation Tabs**: A redesigned, tactile tab bar serving as lenses (Overview, Evidence, Timeline, Network) for deeper analysis.
5. **Technical Metadata Strip**: A compact, `JetBrains Mono` strip confirming API status, frozen model versions, and feature counts to instill trust.

## Proposed Investigator Workflow
- **0s**: Investigator sees the merchant ID and the massive Risk Band/Score to gauge severity.
- **2s**: Investigator glances at the "Why This Merchant?" preview to see if the risk is driven by temporal velocity changes or network centrality.
- **5s**: Investigator uses the technical metadata to confirm this is the V2 Frozen model.
- **10s+**: Investigator clicks into Evidence, Timeline, or Network tabs for deep-dive analysis.
