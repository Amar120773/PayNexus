# Phase 3: Homepage Audit

## Current Strengths
- **Functional API Integration**: The search safely routes to dynamic merchant investigation pages (`/merchant/[id]`).
- **Clear Demo Concepts**: Pre-defined demo cases (`M00109`, `M00150`, etc.) correctly explain their purpose (high-risk, temporal, blind spot, baseline).
- **Responsive Shell**: The layout structure handles resizing gracefully.

## Current Weaknesses
- **Generic Aesthetic**: Relies heavily on centered text, default icons, and basic card grids. Feels like a generic Next.js template rather than a premium investigation tool.
- **Weak Search Hierarchy**: The search bar looks like a secondary filter input rather than the primary tool for "Command Center" investigations.
- **Identical Card Grid**: The four investigation shortcuts are perfectly symmetrical, removing any sense of editorial narrative or prioritization.
- **Missing Technical Metadata**: No visible context proving the system's underlying capabilities (e.g., number of features analyzed, frozen model state).

## Components & Files to Change
- `dashboard/src/app/page.tsx`: This is the sole file responsible for the homepage. It will be completely rewritten.

## Intended Redesign Structure
1. **Hero Header**: Asymmetric, editorial typography (`Newsreader`) stating "Investigate how merchant risk evolves."
2. **Investigation Search Module**: A massive, tactile search input acting as the focal point of the page, leveraging `JetBrains Mono` for inputs.
3. **Investigation Cases Index**: A vertical, asymmetrical list or stylized grid of cases (01, 02, etc.) using crisp borders, hover translations, and semantic risk badges.
4. **System Snapshot Panel**: A terminal-like status readout showing "V2 FROZEN", "54 SIGNALS", and "ONLINE" statuses aligned to the right or integrated into the hero. 
