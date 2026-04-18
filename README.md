# DAP Shield — Integrated Asset Protection Platform

This repository now runs as an integrated multi-module system:

- `ai_engine/` for fingerprint and morph scoring pipelines
- `backend/` for FastAPI APIs, task processing, and alerting
- `frontend/` for the React + Vite dashboard used by the team

## Features Developed

Based on the `gdg.md` assignment specifications, the following components and core responsibilities were fully implemented:

### 1. Modern Glassmorphism UI
* **Custom Design System:** Built entirely with vanilla CSS (`index.css`) featuring a custom black-and-white (monochrome) glassmorphism theme.
* **Layout Engine:** Responsive sidebar navigation, top header with global search, and fluid grid layouts for complex dashboard widgets.
* **Theming Engine:** Uses CSS variables for absolute control over translucency (`rgba()`), borders (`rgba(255,255,255,0.x)`), and animated neon-glow shadows.

### 2. D3.js Viral Propagation Network (Module 4A)
* Implemented in `PropagationGraph.jsx` using `d3-force`.
* **Interactive Visualization:** Renders the relationship between Source URLs and Piracy Accounts.
* **Rich Interactions:** Drag-and-drop nodes, scroll-to-zoom, and visual link differentiators (Posted vs. Shared).
* **Risk Representation:** High-risk nodes are styled with dynamic SVG glow filters and concentric rings.

### 3. Real-Time Alert System (Module 4B)
* Implemented via `AlertPanel.jsx` and the `useAlerts.js` custom hook.
* **Backend WebSockets:** The hook now connects to the backend `/ws/alerts` endpoint and consumes real violation alerts.
* **Framer Motion Integration:** Smooth entrance/exit animations for new incoming alerts in the live feed.
* **State Management:** Tracking read/unread status across the entire application, updating the global sidebar notification badges.

### 4. Morph Score Analytics (Module 4C)
* Implemented in `MorphScoreCard.jsx`.
* **Radial Gauges:** Pure CSS/SVG animated circular progress bars for overall Morph Score, GAN Score, DCT Frequency, and Temporal Analysis.
* **Recharts Integration:** An area sparkline dynamically visualizes the 24-hour historical morph score trajectory with smooth gradient fills and Cartesian grids.

### 5. High-Risk Account Management
* Built `HighRiskTable.jsx` and `HighRiskPage.jsx`.
* **Interactive Data Table:** Features client-side column sorting and an expandable drill-down "accordion" view for deeper analytics on serial infringers.
* **Distribution Charts:** Uses Recharts Bar Charts to visualize the distribution of accounts across platforms (YouTube, Piracy Sites, etc.) and their assigned risk buckets.

### 6. Asset Upload Flow
* Built `AssetUpload.jsx`.
* **Drag-and-Drop:** Seamless file drop zones using `react-dropzone`.
* **Simulated Pipeline:** A staged, animated pipeline representing the backend process: Uploading -> Keyframe Extraction -> AI Fingerprinting -> Milvus Indexing -> Protection Complete.

### 7. Enforcement Action Center
* Implemented in `EnforcementModal.jsx` and `EnforcementPage.jsx`.
* **Evidence Bundle View:** A comprehensive modal detailing cosine similarity metrics, deepfake / AI transformation flags, platform URLs, and mock Blockchain Provenance (transaction hashes).
* **Action Routing:** UI elements representing "Auto-Takedown" vs. "Human Review" paths.

## Integration Status

- Dashboard stats are loaded from backend `/stats/dashboard`.
- Assets list and uploads are wired to backend `/assets`.
- Live alerts are wired to backend websocket `/ws/alerts`.
- Backend analysis pipeline now attempts AI fingerprint and morph scoring when vectors are missing.
- If optional AI runtime packages are unavailable, backend uses a deterministic fallback vector so workflows remain functional.

## Tech Stack
- **Frameworking:** React 18 / Vite 6
- **Styling:** Vanilla CSS3 (Custom Properties & Glassmorphism)
- **Data Visualization 1:** D3.js (Force-directed networks)
- **Data Visualization 2:** Recharts (React wrapper around D3 for business charts)
- **Animation:** Framer Motion (Orchestrating layout shifts and alert feeds)
- **Icons:** Lucide React

## Setup & Running Locally

1. Start backend infra and API from `backend/`.
2. Start frontend from `frontend/`.

Frontend quick start:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173/`.

> [!NOTE]
> The UI utilizes advanced CSS `backdrop-filter` properties. Ensure you view the dashboard in a modern browser (Chrome, Edge, Safari, Firefox) for the complete glassmorphism experience.
