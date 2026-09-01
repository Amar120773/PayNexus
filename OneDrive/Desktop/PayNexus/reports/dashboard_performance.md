# Dashboard Performance Metrics

Measurements represent local point-in-time inference times across the FastAPI backend without caching, demonstrating the pure compute latency of the ML pipeline when executed interactively.

## Latency Tests
- **Merchant Scoring (`POST /v1/score/merchant`):** 2145.52 ms
- **Network Retrieval (`POST /v1/score/network`):** 2073.14 ms
- **Timeline Request (`POST /v1/score/merchant/timeline`):** 2329.08 ms
- **Dashboard Initial Load:** ~3500 ms (dependent on React state aggregation of the initial 5 endpoints required for a full investigation view)

## Observations
The scoring pipeline executes reasonably fast (~2s) for deep subgraph extraction over 90 days of synthetic transactional context. Due to parallel fetching in `Promise.all` across Next.js Server/Client components, the total initial dashboard load time is roughly bounded by the slowest endpoint, making the UX responsive.
