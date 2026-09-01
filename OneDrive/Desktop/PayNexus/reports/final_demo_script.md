# MuleHunter: Final Demo Script

**Total estimated time: 3–4 minutes**

---

## Opening (15 seconds)

> "MuleHunter is merchant mule-network intelligence. It detects coordinated merchant fraud rings by analyzing how network connections form over time, not just what they look like at a single point."

---

## Scenario 1: Legitimate Merchant (45 seconds)

**Merchant:** `M00001`

### Actions:
1. Open the Dashboard at `/dashboard`
2. Type `M00001` into the merchant search field
3. Press Enter → navigates to `/merchant/M00001`

### What to show:
- **Risk Score**: ~18/100, **LOW** band (green indicator)
- **Case Summary tab**: "No immediate action required" guidance
- **Risk Evidence tab**: Point out low behavioral deltas — volume stable, refund rate flat, minimal device/IP churn
- **Network Intelligence tab**: Sparse network graph — few connections, mostly LOW-risk neighbors

### Talking point:
> "This merchant has high transaction volume but a completely stable network footprint. The model correctly identifies it as legitimate because there's no coordinated infrastructure change."

---

## Scenario 2: Mule Merchant (60 seconds)

**Merchant:** `M00109`

### Actions:
1. Click the browser back button or use the search bar
2. Type `M00109` → Enter

### What to show:
- **Risk Score**: ~92/100, **HIGH** band (red indicator)
- **Case Summary tab**: "Immediate review recommended" — show the investigation guidance
- **Risk Evidence tab**: Highlight the key evidence:
  - Elevated `network_growth` delta (network expanding rapidly)
  - High `device_churn` and `ip_churn` rates (infrastructure turnover)
  - Volume spike between T2→T3
- **Risk Timeline tab**: Click on earlier dates to show the risk was LOW 60 days ago, then spiked — the mule ring was forming

### Talking point:
> "This merchant's individual transaction behavior looks almost normal. But MuleHunter detected that its network connections are forming in a pattern consistent with a mule ring — rapid infrastructure convergence with synchronized behavioral shifts."

---

## Scenario 3: Network Investigation (60 seconds)

**Starting from:** `M00109` (still on screen)

### Actions:
1. Click the **Network Intelligence** tab
2. Point out the star topology showing `M00109` at center with connected merchants
3. Identify a HIGH-risk neighbor (red node) in the graph
4. Click **"Investigate Merchant"** on that neighbor → navigates to their page

### What to show:
- The connected merchant *also* has elevated risk
- Their evidence features show similar patterns: synchronized device churn, coordinated volume spikes
- This is the same network — multiple merchants exhibiting correlated temporal trajectories

### Talking point:
> "This is what distinguishes MuleHunter from per-merchant scoring. Following the network reveals that this isn't one bad merchant — it's a coordinated ring. Multiple merchants converged onto shared infrastructure simultaneously. A per-merchant system would evaluate each one independently and likely miss the pattern."

---

## Scenario 4: Type-D Blind Spot — Honest Limitation (45 seconds)

**Merchant:** `M00492`

### Actions:
1. Navigate to `M00492`

### What to show:
- **Risk Score**: Below threshold (~25/100), **LOW** band
- **Risk Timeline tab**: Risk oscillates but never sustainably crosses the 0.3263 threshold
- **Network Intelligence tab**: Show the expanding network connections — the merchant *is* connected to suspicious entities, but the behavioral signal is too gradual

### Talking point:
> "We want to be honest about our limitations. This is a Type-D behavioral-transition mule. It maintains perfectly stable infrastructure and only shifts its transaction behavior gradually. Our 30-day temporal window resets before the behavioral change accumulates enough signal. The model misses it. The dashboard's network graph gives an analyst a visual clue, but the automated scoring fails here. This is a documented blind spot, and it's where future research would focus."

---

## Closing (15 seconds)

> "MuleHunter combines temporal network evolution, point-in-time safety, and an investigator-first workflow to detect merchant mule rings that individual-level scoring misses. It achieves 86.5% recall at 1.5% false positive rate on our synthetic dataset. The system is honest about what it can and cannot detect."

---

## Demo Navigation Sequence

```
Dashboard
  ↓ search "M00001"
Legitimate Merchant (LOW risk, sparse network)
  ↓ search "M00109"
Mule Merchant (HIGH risk, evidence, timeline)
  ↓ click Network tab
Network Graph (connected HIGH-risk neighbors)
  ↓ click neighbor → Investigate
Connected Merchant (correlated evidence)
  ↓ search "M00492"
Type-D Blind Spot (honest limitation)
```

## Pre-Demo Checklist
1. Run `python src/demo_health_check.py` — must show ALL SYSTEMS GO
2. Confirm FastAPI is running on `localhost:8000`
3. Confirm Next.js dashboard is running on `localhost:3000`
4. Pre-load `M00001` in a browser tab to warm the API cache
