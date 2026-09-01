# Phase 7: Network Intelligence Redesign Audit

## 1. Current Network Implementation
- The UI is powered by `NetworkGraph.tsx` using `@xyflow/react` (React Flow).
- The network data provided via API is a flat `NetworkScoreResult` containing an array of `ScoreResult` objects (these represent the 1-hop neighborhood of the central merchant).
- Currently, relationships are purely implicit: The graph renders edges named `e-{centralId}-{neighborId}` and the backend does NOT explicitly declare edge semantics like "Shared Device" or "Shared IP". 
- The existing UI explicitly states: *"Not exposed by current inference API. Connections represent backend-provided edges."*

## 2. Weaknesses & Usability Problems
- The graph uses a primitive radial layout (`x = 400 + radius * cos(angle)`) which is rigid and doesn't utilize physics/force-directed layouts.
- It displays risk score as `... / 100` (e.g. `0.8123 / 100`) which is mathematically inaccurate since the backend score is `0.9421` natively (it's not out of 100).
- The legend and inspection panels use basic inline styling that doesn't fully align with the editorial/tactile design system established in Phases 2-6.
- The `page.tsx` wrapper for the Network tab has a generic "Network Stats" grid on top of the graph which clutters the workspace.
- The inspection panel relies on standard buttons instead of the `.btn-tactile` design system.

## 3. Proposed Investigator Workflow & Visual Hierarchy
1. **Network Investigation Hero**: Cleanly integrated into `page.tsx` or `NetworkGraph.tsx` showing the absolute count of connections and high-risk neighbors in the new JetBrains Mono styling.
2. **Graph Workspace**: Make the graph visually dominant. Ensure the node styles align precisely with Phase 4/6 (Emerald/Amber/Crimson borders, Off-white surface). Fix the score display (don't append `/ 100`).
3. **Legend & Controls**: Positioned out of the way (bottom-left) but adhering to the deep slate/off-white color palette.
4. **Node Inspection**: A polished slide-in or overlaid panel on the right side that provides the exact snapshot data (Score, Probability, Band) of the selected node and a massive tactile `[ INVESTIGATE MERCHANT → ]` button to trigger navigation.
5. **No Fake Data**: I will strictly maintain the API boundary and will not invent "Shared IP" labels since the API doesn't provide them.
