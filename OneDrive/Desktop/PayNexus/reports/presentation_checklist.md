# MuleHunter: Presentation Checklist

This checklist specifies the exact screenshots and materials needed for the Razorpay Buildathon presentation.

---

## Screenshots Required

### 1. Dashboard Overview
- **What**: The root `/dashboard` page showing system status, merchant search, and any summary statistics
- **How to capture**: Navigate to `localhost:3000/dashboard`

### 2. High-Risk Merchant Profile
- **What**: The `/merchant/M00109` page showing the HIGH risk score banner, risk band, and probability
- **How to capture**: Search `M00109` from the dashboard

### 3. Evidence Panel
- **What**: The "Risk Evidence" tab for `M00109` showing the 10 evolution features with behavioral, network, and temporal groupings
- **How to capture**: Click the "Risk Evidence" tab on the `M00109` investigation page

### 4. Risk Timeline
- **What**: The "Risk Timeline" tab for `M00150` showing the historical risk evolution chart with the threshold line and the time slider
- **How to capture**: Navigate to `M00150`, click "Risk Timeline", interact with the slider to show LOW→HIGH transition

### 5. Network Investigation
- **What**: The "Network Intelligence" tab for `M00109` showing the React Flow star-topology graph with color-coded risk bands on neighbor nodes
- **How to capture**: Click "Network Intelligence" on the `M00109` page

### 6. Mule Network (Connected Merchant)
- **What**: After clicking "Investigate Merchant" on a HIGH-risk neighbor of `M00109`, show the neighbor's investigation page with correlated evidence features
- **How to capture**: From the `M00109` network graph, click a red (HIGH) neighbor → their investigation page

### 7. Architecture Diagram
- **What**: A clean version of Diagram 1 from `reports/final_architecture_diagram_spec.md`
- **How to create**: Render the ASCII diagram specification as a polished visual using a diagramming tool (draw.io, Figma, or similar)
- **Note**: Do NOT use the raw ASCII art in the presentation. The spec document is the *specification*; the slide needs a rendered graphic.

### 8. Evaluation Results
- **What**: The 5-model ablation table from `reports/final_metrics.md` showing the progression from behavioral baseline (F1=0.157) to full evolution model (F1=0.821)
- **How to create**: Format the table as a clean slide. Highlight the final model row. Include the synthetic-data disclaimer.

### 9. Temporal Safety
- **What**: Terminal output showing `pytest tests/test_phase8_temporal_safety.py -v` passing both adversarial tests
- **How to capture**: Run the command and screenshot the terminal output

### 10. Demo Health Check
- **What**: Terminal output showing `python src/demo_health_check.py` with all checks passing and "ALL SYSTEMS GO" message
- **How to capture**: Run the command and screenshot the terminal output

---

## Slide Structure Recommendation

| Slide | Content | Duration |
| :--- | :--- | :--- |
| 1 | Title: "MuleHunter — Merchant Mule-Network Intelligence" | 10s |
| 2 | Problem: Why per-merchant scoring misses coordinated rings | 30s |
| 3 | Architecture diagram (Screenshot #7) | 30s |
| 4 | Evaluation results table (Screenshot #8) | 30s |
| 5 | **LIVE DEMO** (Screenshots #1–6 happen live) | 3 min |
| 6 | Known limitations (Type-D, synthetic data, 60-day window) | 20s |
| 7 | Razorpay relevance + next steps | 20s |

---

## Critical Reminders

- [ ] Do NOT generate fake screenshots or mock data
- [ ] Do NOT fabricate results — use only verified metrics from `reports/final_metrics.md`
- [ ] Do NOT claim production-scale performance
- [ ] Do NOT hide the Type-D blind spot
- [ ] Include the synthetic-data disclaimer on every metrics slide
- [ ] Run `python src/demo_health_check.py` immediately before presenting
- [ ] Ensure both `localhost:8000` (FastAPI) and `localhost:3000` (Next.js) are running
- [ ] Pre-warm the API by loading `M00001` before the demo starts
