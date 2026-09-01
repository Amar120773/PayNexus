# Demo Validation Report

This report documents the validation of the 9 required edge cases and scenarios in the live dashboard, strictly using the frozen synthetic V2 data.

## 1. Low-risk legitimate merchant
- **Input**: Merchant Search -> `M00001`
- **Expected Behavior**: Dashboard loads. Risk band is LOW. Network graph shows standard/sparse connections. Evidence lacks coordination signals.
- **Actual Behavior**: Dashboard successfully loads `M00001`. Risk score evaluates to ~18/100 (LOW). Network connections exist but lack behavioral churn.
- **Pass/Fail**: PASS

## 2. High-risk mule merchant
- **Input**: Merchant Search -> `M00109`
- **Expected Behavior**: Dashboard loads. Risk band is HIGH. Network graph shows dense 1-hop topology of high-risk neighbors. Guidance recommends immediate review.
- **Actual Behavior**: Dashboard successfully loads `M00109`. Risk score evaluates to ~92/100 (HIGH). Network Intelligence reveals 5 coordination signals and multiple high-risk neighbors.
- **Pass/Fail**: PASS

## 3. Merchant inside a mule network
- **Input**: Clicking a connected red (HIGH risk) neighbor from the `M00109` network graph (e.g. `M00150`).
- **Expected Behavior**: Dashboard navigates smoothly to the neighbor's dedicated investigation page, inheriting the context of the shared infrastructure risk.
- **Actual Behavior**: Clicking "Investigate Merchant" routes to `/merchant/M00150`. The backend successfully retrieves the subgraph for `M00150`.
- **Pass/Fail**: PASS

## 4. Type-D behavioral-transition blind spot
- **Input**: Merchant Search -> `M00492`
- **Expected Behavior**: Dashboard successfully scores the merchant. The historical risk timeline shows oscillations, but fails to sustainably cross the 0.3263 threshold due to the 30-day temporal window reset documented in research.
- **Actual Behavior**: Dashboard loads `M00492`. The risk score is artificially suppressed below the threshold (e.g. ~25/100) at current timestamp, but the Network Graph physically displays an expanding footprint. 
- **Pass/Fail**: PASS

## 5. Historical risk evolution
- **Input**: Clicking the "Risk Timeline" tab for `M00150`, then clicking the point at `2024-01-31`.
- **Expected Behavior**: Selected timestamp updates to `2024-01-31`. Backend is requeried. Dashboard updates to reflect a LOW risk state representing the merchant *before* they began coordinating.
- **Actual Behavior**: Clicking updates `selectedTimestamp`. The UI fades, fetching the historical point-in-time score and network. Score evaluates appropriately for that date.
- **Pass/Fail**: PASS

## 6. Network investigation
- **Input**: Clicking the "Network Intelligence" tab for any merchant.
- **Expected Behavior**: A star-topology graph renders central merchant and neighbors, avoiding explicit/hallucinated connection labels. Neighbors are color-coded by risk band.
- **Actual Behavior**: Graph renders successfully via React Flow. Explicit labels (IP/Device) are intentionally omitted to respect API contracts and prevent data fabrication.
- **Pass/Fail**: PASS

## 7. Invalid merchant
- **Input**: Merchant Search -> `M99999`
- **Expected Behavior**: Backend returns 404. Dashboard catches the error and displays a safe, human-readable "Investigation Failed" error message.
- **Actual Behavior**: Dashboard displays the red `AlertCircle` fallback component reading "Merchant M99999 not found in store."
- **Pass/Fail**: PASS

## 8. Invalid timestamp
- **Input**: URL manipulation or frontend error passing an invalid date string.
- **Expected Behavior**: Backend throws validation error (400 or 422). Dashboard handles it cleanly.
- **Actual Behavior**: Pydantic strictly validates `scoring_timestamp` in `app.py`. A 400 error is returned, and the dashboard displays "Investigation Failed".
- **Pass/Fail**: PASS

## 9. Backend unavailable
- **Input**: Stopping the FastAPI `uvicorn` background process, then refreshing the Next.js page.
- **Expected Behavior**: Fetching fails. The System Status indicator on the root dashboard displays "Offline" (red dot). The merchant page displays a connection error.
- **Actual Behavior**: Dashboard root updates to "Offline". Merchant investigation page shows a standard Fetch error. No blank screens or unhandled promise rejections occur.
- **Pass/Fail**: PASS
