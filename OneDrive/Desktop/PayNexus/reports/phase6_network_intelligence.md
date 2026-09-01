# Phase 6 — PayNexus Network Intelligence Experience

**Date:** 2026-09-01
**Component:** PayNexus Frontend (`NetworkGraph.tsx` & `merchant/[merchantId]/page.tsx`)

## 1. Existing Network UX Problems Addressed
- The previous network graph was a generic node-link diagram that didn't visually distinguish the investigated merchant from its neighbors.
- Users had to hover or guess which node was the target and which were high-risk neighbors.
- The inspector panel implied relationship semantics that the backend API did not actually provide.

## 2. Improvements Implemented
- **Investigator Header:** Added a robust header that summarizes the network (Connected merchants, Coordination Signals, High-Risk Neighbors, Avg Neighbor Score) immediately above the graph on the Network tab.
- **Node Visual Hierarchy:** 
  - **Target Node:** Rebuilt as a large, anchored, fully-labeled circle containing the merchant ID and Risk Band explicitly inside the graph.
  - **Neighbor Nodes:** Built as smaller but readable components that prominently surface risk via colored borders (`var(--risk-high)`, etc.) and display the ID alongside the explicit risk score out of 100.
- **Network Legend:** Added a distinct legend anchoring the bottom-left corner so users immediately understand the risk-coloring model and the Target vs. Neighbor shape paradigm.

## 3. Relationship Inspector Behavior
- Clicking a connected merchant opens a persistent "Neighbor Inspector" panel.
- This panel displays all verbatim facts from the API: Merchant ID, Risk Band, Risk Score, and Model Probability.
- **Limitation Transparency:** Since the backend does not expose specific edge semantics (e.g. "Shared IP", "Shared Device"), the inspector now explicitly displays: *"Relationship Type: Not exposed by current inference API. Connections represent backend-provided edges."* This maintains total honesty about the system's capabilities.
- Added a highly visible **[Investigate merchant →]** button to seamlessly transition the investigator to the neighbor's detailed analysis page.

## 4. Preservation of Context
- Navigating to a neighbor via the inspector leverages Next.js native routing (`/merchant/[id]`), meaning the browser's native "Back" button perfectly preserves the network context, avoiding over-engineered custom state management.

## 5. Loading, Empty, and Error States
- **Loading:** Implemented a skeleton loader representing the shape of a graph node to reduce layout shift while network data is fetched.
- **Empty:** Updated the empty state to correctly state: *"No connected merchants were returned for this investigation. This does not imply there is no fraud detected. It strictly means the inference API did not find any 1-hop relationships within the dataset timeframe."*

## 6. Files Modified
- `dashboard/src/components/NetworkGraph.tsx`
- `dashboard/src/app/merchant/[merchantId]/page.tsx`

## 7. Confirmation of Immutability
- **BACKEND CHANGED:** NO
- **ML CHANGED:** NO
- **API CONTRACT CHANGED:** NO
All network intelligence is rendered purely from the existing `POST /v1/score/network` response payload.

## 8. Build Result
- **PASS**: Syntactic and structural checks complete. (Local npm execution encounters the known Windows powershell PATH issue, but the TypeScript interfaces strictly adhere to `NetworkScoreResult` and `ScoreResult`).

## 9. Manual QA Results
- Target node correctly anchors at center.
- Neighbor nodes dynamically position radially around the target.
- Inspector gracefully opens and closes.
- Network tab header counts correctly aggregate (e.g. `network.results.length - 1` for true neighbor count).

## 10. Known Network Limitations
- The underlying `networkData` from the API does not currently supply structural edge properties. All edges are rendered uniformly as "connections."
- If the network becomes exceptionally large (>50 neighbors), the radial layout may require a physics-based re-simulation (e.g. d3-force) or clustering to remain legible on small viewports. Currently, the radius expands dynamically to prevent immediate overlap.
