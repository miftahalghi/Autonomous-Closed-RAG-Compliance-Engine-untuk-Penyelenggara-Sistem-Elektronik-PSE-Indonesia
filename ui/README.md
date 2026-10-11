# Audit PDP Engine — UI

React + Vite + Tailwind CSS dashboard for the PDP Compliance Audit Engine.

## Quick Start

```bash
cd ui
npm install
npm run dev
```

Open http://localhost:5173

## Modes

| Mode | Description |
|------|-------------|
| **Offline Demo Mode** | Instantly loads pre-baked mock results (safe for demos, no backend needed) |
| **Live Endpoint (Langflow)** | Calls `http://localhost:7860` via Vite proxy (`/api → /`) |

## File Structure

```
ui/src/
├── App.jsx                    # Root state + routing between phases
├── mockData.js                # Pre-baked audit result + 3 sample policies
├── index.css                  # Tailwind base + dark theme
└── components/
    ├── Header.jsx             # Branding, mode toggle, quick-load samples
    ├── InputPanel.jsx         # Document name + text input + audit trigger
    ├── ProgressStepper.jsx    # Animated 5-phase stepper with elapsed timer
    ├── ResultsDashboard.jsx   # Executive summary + filter tabs + export
    ├── ComplianceGauge.jsx    # SVG circular score gauge
    ├── PillarCard.jsx         # Accordion card per pillar + copy revision
    └── AIFooter.jsx           # Responsible AI disclaimer + export buttons
```

## Features

- **5-phase animated progress stepper** with elapsed timer (covers 50–60s live API wait)
- **Circular compliance score gauge** (green/yellow/red based on score)
- **Filter tabs**: Semua / Perlu Perhatian / Patuh
- **Per-pillar accordion** with original clause ↔ legal reference split view
- **One-click copy** of ready-to-use revision clause with toast notification
- **Export JSON** — downloads full audit report as `.json`
- **Print / Export PDF** — triggers `window.print()` with print-hidden nav
- **Demo Mode** — simulates all 5 steps with realistic timing, loads mock KRITIS scenario
