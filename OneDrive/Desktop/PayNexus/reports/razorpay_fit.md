# MuleHunter: Razorpay Fit

## Why Merchant Mule-Network Risk Is Relevant to Razorpay

Razorpay serves as a payment aggregator for millions of merchants across India. This aggregator model means Razorpay onboards merchants at scale, facilitates their payment processing, and manages the financial risk of merchant fraud on behalf of acquiring banks and payment networks.

The aggregator model naturally creates an environment where merchant mule networks can operate:

1. **High onboarding velocity**: Rapid merchant onboarding is a competitive advantage, but it also creates windows where coordinated account creation (a hallmark of mule ring formation) may not be immediately distinguishable from legitimate growth.

2. **Shared infrastructure density**: Razorpay merchants legitimately share infrastructure — common API endpoints, platform-level device fingerprints, IP ranges from cloud providers and co-working spaces. This legitimate density is exactly what mule networks exploit: their abnormal infrastructure sharing hides within the noise of normal sharing patterns.

3. **Ecosystem-level risk**: When multiple merchant accounts are controlled by the same criminal organization, the risk is not at the individual merchant level — it is at the network level. A single mule merchant processing ₹50,000/month may appear unremarkable. Twenty such merchants in a coordinated ring represent a ₹1 crore/month laundering channel.

---

## Why Per-Merchant Transaction Fraud Detection Is Insufficient for This Problem

Traditional transaction-level and merchant-level risk systems excel at detecting individual anomalies: unusual velocity, geographic mismatches, card-testing patterns, high chargeback rates. These systems are essential infrastructure.

However, mule merchants are *designed* to evade individual-level detection:
- Each merchant processes volumes within normal bounds
- Each merchant maintains standard KYC documentation
- Each merchant's refund and chargeback rates are unremarkable in isolation

The fraud signal is *inter-merchant*: it lives in the relationships *between* accounts, not *within* any single account. A per-merchant system fundamentally cannot detect this because it evaluates each merchant independently.

---

## Where Network Intelligence Could Complement an Existing Payment-Risk Stack

MuleHunter is positioned as a **potential complement** to existing risk infrastructure, not a replacement. Specifically:

| Existing Layer | What It Detects | MuleHunter's Potential Addition |
| :--- | :--- | :--- |
| Transaction-level scoring | Individual payment anomalies | Coordinated multi-merchant patterns |
| KYC / onboarding checks | Identity fraud at sign-up | Post-onboarding network formation |
| Chargeback monitoring | High-risk merchants after losses | Pre-loss detection via network trajectory |
| Rule-based velocity checks | Per-merchant velocity violations | Cross-merchant synchronized velocity |

MuleHunter could act as an **investigation layer** that sits alongside these systems and surfaces questions like: *"These five merchants all adopted the same three device fingerprints in the last 14 days — is this a legitimate platform migration or a mule ring forming?"*

---

## What Data MuleHunter Would Require in a Real Razorpay Environment

To operate on real Razorpay data, MuleHunter would need access to the following data categories:

| Data Category | Specific Fields | Purpose |
| :--- | :--- | :--- |
| **Merchant profiles** | merchant_id, onboarding_date, category, KYC status | Merchant identification and segmentation |
| **Transactions** | merchant_id, timestamp, amount, status (completed/refunded) | Behavioral trajectory features (volume, refund deltas) |
| **Device fingerprints** | merchant_id, device_id, first_seen, last_seen | Device churn rate between time windows |
| **IP associations** | merchant_id, ip_address, first_seen, last_seen | IP churn rate between time windows |
| **Settlement accounts** | merchant_id, account_id | Optional — settlement account sharing as a strong mule signal |

All of these are standard operational data fields that a payment aggregator typically maintains.

---

## What Cannot Currently Be Demonstrated

The following limitations are inherent to the current MuleHunter prototype:

1. **Synthetic data only**: All 5,000 merchants, 150,000 transactions, and 298 mules are programmatically generated. The data was designed to be realistic but is not derived from real payment events.

2. **No real mule-network ground truth**: The mule labels are injected by the data generator based on four predefined lifecycle patterns. Real mule networks may exhibit behaviors not modeled in our synthetic scenarios.

3. **No production-scale testing**: The current system handles 5,000 merchants. Razorpay's real merchant base is orders of magnitude larger. Performance at scale (latency, memory, feature computation cost) is untested.

4. **No adversarial evasion testing**: The synthetic mules follow predefined behavioral patterns. Real criminals may actively adapt to detection signals — for example, deliberately avoiding synchronized infrastructure changes once they learn that churn rate is a detection feature.

5. **No integration testing with existing Razorpay systems**: MuleHunter operates as a standalone system. Integration with Razorpay's existing risk infrastructure, data pipelines, and investigation workflows has not been prototyped.

6. **No regulatory or compliance validation**: Anti-money-laundering (AML) and fraud detection systems in production must comply with regulatory requirements. MuleHunter has not been evaluated against any specific regulatory framework.

---

## Careful Positioning

MuleHunter demonstrates a **research hypothesis** — that temporal network evolution is a viable signal for mule-network detection — validated on synthetic data. It proposes a potential complement to existing payment-risk infrastructure.

It does **not** claim that Razorpay currently lacks mule-network detection capabilities, nor does it claim that MuleHunter would outperform any existing production system on real data.
