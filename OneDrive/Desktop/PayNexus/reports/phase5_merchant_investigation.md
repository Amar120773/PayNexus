# Phase 5 — Merchant Investigation Experience

**Date:** 2026-09-01
**Component:** PayNexus Frontend (`merchant/[merchantId]/page.tsx`)

## 1. Existing UX Problems Addressed
- The previous design dumped 54 features onto the screen without clear guidance. The new design introduces a hierarchical triage workflow, prioritizing immediate comprehension via the **Overview** tab.
- Re-ordered the tabs to exactly match an investigator's workflow: `Overview → Evidence → Timeline → Network`.
- Integrated Timeline and Network Previews directly into the Overview, allowing the investigator to glance at historical escalation and structural risk without leaving the primary summary view.

## 2. New / Modified Components
- Restructured `dashboard/src/app/merchant/[merchantId]/page.tsx` entirely.
- Created the `Overview` tab content, effectively replacing the old "Summary" tab.
- Integrated `Timeline Preview`: Extracts historical risk trajectories directly from the `timeline` state (e.g. checking if `timeline[0].risk_band !== timeline[last].risk_band`) to give an immediate "Risk elevated" or "Stable" signal without hallucinating reasons.
- Integrated `Network Preview`: Extracts the exact count of connected merchants to provide immediate structural intelligence before the user navigates to the full graph.

## 3. Risk-Score Presentation Changes
- The Risk Score Ring (implemented natively in SVG) is the strongest visual element on the page.
- Risk bands strictly use typographical hierarchy and subtle background color/borders in the new tokens (`var(--risk-high-text)`, `var(--risk-high-bg)`) rather than glowing neons.

## 4. Evidence Hierarchy
- **Key Signals:** The top 3 features by absolute magnitude are extracted and displayed immediately on the Overview tab under "Observed Evidence". They are presented with neutral language.
- **Evidence Tab:** The full 54 features remain fully accessible via the Evidence tab, properly categorized into Temporal, Behavioral, and Network buckets using the `FeatureRow` component to visually indicate magnitude.

## 5. Loading States
- The `InvestigationSkeleton` contextual loader provides immediate structural preview and communicates exact analytical steps: *"Analyzing merchant... Loading network intelligence & reconstructing risk timeline"*.

## 6. Error States
- Uses a bordered danger card that gracefully handles API unavailability: *"Unable to retrieve merchant intelligence. The inference service did not return a response."*

## 7. Accessibility Improvements
- Maintained tabular numerals (`fontVariantNumeric: "tabular-nums"`) for all scores, probabilities, and evidence features.
- Keyboard navigation between tabs is preserved natively via `<button role="tab">`.

## 8. Responsive Improvements
- The Overview tab uses CSS grid with standard gaps, which will wrap on smaller viewports.
- The merchant identity header wraps cleanly on tablet views.

## 9. Files Modified
- `dashboard/src/app/merchant/[merchantId]/page.tsx`

## 10. Confirmation of Strict Integrity
- **BACKEND CHANGED:** NO
- **ML CHANGED:** NO
- **API CONTRACT CHANGED:** NO
The exact backend data structures are consumed safely. No fake relationships, dummy metrics, or hallucinatory AI summaries were introduced. All information is verifiably derived from the FastAPI endpoints.

## 11. Build Result
- **PASS** (Next.js 15 App Router standard strict compliance).

## 12. Manual QA Results
- Logic successfully accommodates edge cases like insufficient timeline data (shows "Insufficient data" preview instead of crashing).
- The top 3 signals correctly sort by absolute magnitude dynamically based on the point-in-time timestamp selected in the Risk Timeline tab.

## 13. Remaining Limitations
- Advanced brushing/scrubbing through time is not yet fully implemented; the user must click specific distinct points on the Timeline graph to update the analysis point.
- The Timeline and Network tabs themselves have not been radically overhauled in this phase per instructions.
