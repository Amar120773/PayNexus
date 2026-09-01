# Phase 6: Temporal Risk Intelligence Redesign Audit

## 1. Available Historical Points
- The timeline accepts an array of `ScoreResult` objects.
- The `ScoreResult` contains `scoring_timestamp`, `risk_score`, `risk_band`, `probability`, and `evidence_features`.
- Specifically, the `page.tsx` passes a hardcoded array of 5 timeline timestamps (`2026-01-31` to `2026-03-31`).

## 2. API Data
- The backend fully supplies historical risk scores, risk bands, and evidence features for each timestamp.
- The threshold is supplied by `getModelMetadata()`.

## 3. Current Slider / State Handling
- The current implementation uses Recharts `LineChart` `onClick` to update the `selectedTimestamp`. 
- There is no physical "scrubber" (like a slider input), it relies entirely on clicking invisible points on the graph.

## 4. Current Risk Graph Visuals
- Displays an unstyled line with arbitrary threshold references (`threshold * 100`, which implies `risk_score` is on a 0-100 scale but in Phase 4/5 we saw the score is around `0.9421` — wait, `page.tsx` Risk Ring `min(100, score)`. It seems in Phase 4 I rendered the raw float (e.g., `0.9421`), but Recharts multiplies `threshold * 100` and domains to `[0, 100]`. Wait, if the risk score is actually a float `0..1` or `0..100`? Let's fix this discrepancy: if the score is `0.9421` (Float), then the Y-Axis domain `[0, 100]` will crush the line flat. I need to check the API payload or simply adapt to the raw value).
- The graph lacks a strong "What Changed?" summary.

## 5. Mobile Behavior & Responsiveness
- The graph uses `ResponsiveContainer` but doesn't adapt its axis margins for mobile, which can cause clipping.

## 6. Proposed Information & Visual Hierarchy
1. **Hero**: "RISK EVOLUTION" heading with a neutral "How the merchant's risk profile changed across observed time."
2. **Current Snapshot Panel**: A dedicated left/top column showing the exact `TIMESTAMP`, `SCORE`, and `BAND` of the currently selected node in heavy JetBrains Mono.
3. **What Changed Panel**: Compute simple absolute differences between the selected point and the *previous* point (if available) safely on the frontend.
4. **Graph Redesign**: Remove the `[0, 100]` hardcoded domain. Auto-scale or use `[0, 1]` if it's a float. Remove dashed grid lines to make it purely editorial. Use a clean, singular brand color line with semantic dot markers.
5. **Tactile Controls**: Use a `<input type="range">` custom scrubber below the graph to allow dragging through time natively, replacing the purely click-based interaction.
