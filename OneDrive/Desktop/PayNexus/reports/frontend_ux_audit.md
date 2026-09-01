# PayNexus Frontend UX Audit

**Audit Date:** 2026-09-01  
**Scope:** `dashboard/src/` — all pages, components, lib, and styles  
**Constraint:** ML pipeline, backend API contracts, inference logic are FROZEN. Audit is frontend-only.

---

## Files Audited

| File | Role |
|---|---|
| `app/layout.tsx` | Global shell, navigation header |
| `app/globals.css` | Design tokens, utilities |
| `app/page.tsx` | Home/search page |
| `app/merchant/[merchantId]/page.tsx` | Core investigation page |
| `components/RiskTimeline.tsx` | Risk evolution chart |
| `components/NetworkGraph.tsx` | Network visualization |
| `lib/api.ts` | API contracts/fetching |
| `package.json` | Dependencies |

---

## Current Strengths

1. **Dark mode foundation is solid.** The `#06070a` background with radial gradient and `glass-panel` utility creates a genuinely premium dark aesthetic.
2. **Risk badge color coding works.** HIGH/MEDIUM/LOW bands using red/orange/emerald are applied consistently across the header badge, case summary, and evidence panel.
3. **Tab-based investigation layout is clean.** The four-tab structure (Case Summary → Evidence → Timeline → Network) maps naturally to the investigator's cognitive workflow.
4. **Point-in-time interaction exists.** Clicking a timeline point re-fetches scores at that moment — a technically sophisticated and novel UI capability. The blur transition during refetch is a nice touch.
5. **API integrity is maintained.** `api.ts` uses `NEXT_PUBLIC_API_URL`, no hardcoded localhost. TypeScript interfaces correctly mirror API contracts.
6. **Neighbor inspector prevents fabrication.** The note in `NetworkGraph.tsx` — "Explicit shared entities are omitted as the backend does not expose relationship edges natively" — is scientifically honest and correct.

---

## Current Weaknesses

### A. Visual Hierarchy

**W1. Risk score is buried in a side-by-side flex container.**  
The most important signal — the mule risk score (e.g., `87.3 / 100 HIGH`) — shares horizontal space with merchant metadata. An investigator's eye has to travel right to find it. It does not visually dominate on first load.

**W2. "CASE SUMMARY" heading is redundant.**  
The tab already says "Case Summary." The all-caps `h3` inside the panel repeats it, wasting 40px of vertical space before meaningful content.

**W3. Home page "Global Dashboard" title communicates nothing.**  
"Global Dashboard" is a generic placeholder. A PayNexus-specific title like _"Merchant Mule Risk Intelligence"_ would immediately establish product identity.

**W4. Evidence labels are raw ML API keys.**  
Features like `graph_pagerank_score`, `transaction_burst_score`, `shared_settlement_count` are rendered verbatim. These are machine-feature names, not investigator-readable labels. They look like debug output, not a professional evidence console.

---

### B. Information Overload

**W5. Evidence tab dumps all features with no visual weight.**  
Three columns of scroll-locked feature dumps present 20–40 raw floats with identical visual treatment. There is no way to understand which signals are most damning at a glance.

**W6. No visual magnitude encoding.**  
Every feature value is shown as `blue monospace font`. A signal with value `0.0001` looks identical to `0.9823`. There is no bar, gradient, or color band to convey relative importance.

**W7. Case Summary repeats header content.**  
The header badge already shows `87.3 / 100 HIGH RISK`. The Case Summary tab then re-shows the same score, the risk band, and the analysis timestamp. 3 of 4 summary rows duplicate header info. The tab adds almost no new information.

---

### C. Network Graph

**W8. Fixed-radius circular layout is rigid.**  
All neighbor nodes are placed on a perfect circle at `radius = 200`. For merchants with 8+ neighbors, nodes overlap. For 1–2 neighbors, the layout looks sparse and center-heavy.

**W9. Empty state is informative but visually dead.**  
"No network connections detected" uses a muted gray `ShieldAlert`. This is an important investigative outcome ("merchant operates in isolation") that deserves a structured, readable card.

**W10. No legend exists on the graph.**  
Nodes are color-coded green/amber/red by risk band but there is no legend. A first-time viewer — such as a judge — would not understand the node color semantics.

**W11. ReactFlow Controls styling is mismatched.**  
The zoom/pan controls use inline `backgroundColor: '#1e2128'` and do not match the glass-panel design language of the rest of the app.

---

### D. Risk Timeline

**W12. Chart height is fixed at `h-72` (288px) — too short.**  
For a data-dense risk evolution chart, 288px is cramped. The threshold reference line overlaps the axis label when the score is near the threshold value.

**W13. Threshold label shows no value.**  
The dashed red line says "Threshold" but not the actual value. The investigator's key question is "how far above threshold is this merchant?" The label should read `Threshold: 32.6`.

**W14. No click-selection visual feedback on the timeline.**  
When the user clicks a point to trigger a point-in-time refetch, there is no visual indication that the point is "selected." The dot does not change. Only the timestamp box at the top updates.

**W15. `isAnimationActive={false}` makes chart feel static.**  
Animation was disabled (presumably for performance). This makes the chart feel lifeless on initial render.

---

### E. Loading & Error States

**W16. Loading state is a bare spinner with generic text.**  
`"Loading merchant investigation..."` below a blue spinner is generic. A branded skeleton layout would feel more polished.

**W17. The `isRefetchingTime` blur looks like a crash.**  
`blur-[2px] opacity-50` on the entire content area when clicking a timeline point looks like an error/render failure rather than a purposeful loading state.

**W18. Error state has no navigation escape.**  
The "Investigation Failed" screen shows the error and a "Retry" button — but no "Back to Search" link. A user who typed a bad merchant ID is completely trapped.

---

### F. Home Page

**W19. "Recent Investigations" is permanently empty.**  
The placeholder card uses `ShieldAlert` and italic text. Since there is no session storage, this panel is always empty. It wastes ~200px of prime real estate and signals to judges that a feature is incomplete.

**W20. System Status sidebar exposes internal model metadata.**  
The sidebar shows `Risk Threshold: 0.3263` and `Features: 54 active`. These are internal ML parameters, not information an investigator needs on the landing page.

---

### G. Navigation & Responsiveness

**W21. Navigation has no active-page indicator or breadcrumb.**  
On a merchant investigation page, the header shows only the PayNexus logo. There is no breadcrumb, back button, or current-context label.

**W22. Inconsistent max-width across pages.**  
Home page: `max-w-5xl`. Merchant page: `max-w-6xl`. The layout shifts on navigation, which feels unpolished.

**W23. Mobile responsiveness is not considered.**  
The 3-column evidence grid collapses to 1 column on mobile with no visual adjustment. The network graph's `h-[600px]` overflows on smaller screens. The tab bar wraps awkwardly on narrow viewports.

---

## Prioritized Recommendations

### P0 — Critical (Direct Submission Impact)

| ID | Issue | File | Recommended Fix |
|---|---|---|---|
| P0-1 | Evidence labels are raw ML keys | `merchant/[merchantId]/page.tsx` | Add a `FEATURE_LABELS` lookup map (e.g. `graph_pagerank_score` → `"Network Centrality"`) |
| P0-2 | No visual magnitude encoding | `merchant/[merchantId]/page.tsx` | Add a horizontal bar behind each feature value, scaled to 0–1 range |
| P0-3 | Home page title is generic | `app/page.tsx` | Replace "Global Dashboard" with a PayNexus branded hero with subtext |
| P0-4 | "Recent Investigations" always empty | `app/page.tsx` | Replace with "Demo Merchants" quick-access panel with 3 pre-set IDs (HIGH/MEDIUM/LOW) |
| P0-5 | No timeline click-selection feedback | `components/RiskTimeline.tsx` | Track selected timestamp; highlight selected dot with a different fill/ring |

### P1 — High (Polish)

| ID | Issue | File | Recommended Fix |
|---|---|---|---|
| P1-1 | Risk score should dominate visually | `merchant/[merchantId]/page.tsx` | Move risk badge above the tab bar, full-width, with a circular SVG score ring |
| P1-2 | Threshold label shows no value | `components/RiskTimeline.tsx` | Change label to `Threshold: {(threshold * 100).toFixed(1)}` |
| P1-3 | `isRefetchingTime` blur looks like crash | `merchant/[merchantId]/page.tsx` | Replace with a small spinner on the specific updating panels only |
| P1-4 | Error state has no escape route | `merchant/[merchantId]/page.tsx` | Add `← Back to Search` link next to Retry button |
| P1-5 | No network graph legend | `components/NetworkGraph.tsx` | Add a 3-item inline legend (green/amber/red = LOW/MEDIUM/HIGH) |
| P1-6 | Navigation lacks context | `app/layout.tsx` | Add breadcrumb context when on investigation page |
| P1-7 | Inconsistent max-width | both pages | Standardize to `max-w-6xl` across all pages |

### P2 — Nice-to-Have (Extra Polish)

| ID | Issue | File | Recommended Fix |
|---|---|---|---|
| P2-1 | ReactFlow controls mismatch design | `components/NetworkGraph.tsx` | Apply glass-panel CSS to ReactFlow Controls element |
| P2-2 | Chart height too short | `components/RiskTimeline.tsx` | Increase to `h-96`; add area fill under the risk line |
| P2-3 | Case Summary duplicates header | `merchant/[merchantId]/page.tsx` | Replace score/band rows with new info: behavioral_risk, network_risk, scoring agent |
| P2-4 | Loading state is generic | `merchant/[merchantId]/page.tsx` | Add skeleton layout with pulsing glass-panel shapes |
| P2-5 | System Status sidebar shows ML internals | `app/page.tsx` | Remove threshold/feature count; keep only API health + model version |
| P2-6 | Fixed circular graph layout | `components/NetworkGraph.tsx` | Scale radius dynamically with neighbor count |
| P2-7 | Chart animation disabled | `components/RiskTimeline.tsx` | Re-enable with a short 600ms entry animation |

---

## Proposed Visual Design System

### Typography (additions to existing Inter)

```
Page Title (H1):     Inter ExtraBold 36px, tracking-tight
Section (H2):        Inter Bold 24px
Card Header (H3):    Inter SemiBold 16px, tracking-wide
Label:               Inter SemiBold 11px, tracking-widest, UPPERCASE, slate-400
Body:                Inter Medium 14px, slate-200
Mono Data:           font-mono 14px, blue-400 or white
```

### Color Tokens (additions to `globals.css`)

```css
--risk-high:         #ef4444;   /* red-500  */
--risk-medium:       #f59e0b;   /* amber-500 */
--risk-low:          #10b981;   /* emerald-500 */
--signal-strong:     #f8fafc;   /* white — high magnitude */
--signal-weak:       #475569;   /* slate-600 — near-zero */
--accent-primary:    #3b82f6;   /* blue-500 */
--accent-secondary:  #818cf8;   /* indigo-400 */
```

### Feature Label Map (for P0-1, frontend-only — no backend changes)

```typescript
const FEATURE_LABELS: Record<string, string> = {
  graph_pagerank_score:        "Network Centrality",
  transaction_burst_score:     "Transaction Burst",
  shared_settlement_count:     "Shared Settlements",
  coordinated_activity_score:  "Coordination Score",
  velocity_change_30d:         "30-Day Velocity Change",
  churn_rate:                  "Customer Churn Rate",
  // ... extend as needed
};
const labelFor = (key: string) => FEATURE_LABELS[key] ?? key.replace(/_/g, " ");
```

---

## Proposed Investigator Workflow

### Current Tab Order
`Case Summary → Evidence → Timeline → Network`

### Recommended Tab Order
`Timeline → Summary → Evidence → Network`

**Rationale:**

```
1. SCORE (always visible, above tabs — not in a tab)
   → Risk score ring, band, probability, scoring timestamp

2. TIMELINE (first tab — primary triage)
   → "Is this merchant escalating over time?"
   → Click point to lock all panels to that timestamp

3. SUMMARY (second tab — why is it high?)
   → Top 3 signals, investigation guidance, behavioral vs network risk

4. EVIDENCE (third tab — deep dive)
   → Full feature breakdown with magnitude bars and human-readable labels
   → Behavioral / Network / Temporal categories

5. NETWORK (last tab — trace connections)
   → "Who is this merchant connected to?"
   → Color-coded neighbors, click to pivot investigation
```

This matches the real risk investigator triage order: **triage → diagnose → trace**.

---

## Summary

The PayNexus frontend has a strong visual foundation (dark mode, glass panels, color-coded risk bands, point-in-time interactivity) but reads as an early prototype on close inspection.

**Two changes would have the highest submission impact:**

1. **Feature label map (P0-1):** Raw ML feature keys visible to judges signal the product UI is unfinished. A simple `Record<string, string>` lookup table completely transforms the Evidence tab into an investigator-readable console.

2. **Demo Merchant shortcuts on home page (P0-4):** Replacing the permanently-empty "Recent Investigations" panel with 3 pre-loaded demo merchant IDs (HIGH / MEDIUM / LOW risk) means a judge can explore the full product in seconds without knowing the merchant ID format.

These two changes alone are pure frontend work, require no backend changes, and would significantly improve first impressions during judging.
