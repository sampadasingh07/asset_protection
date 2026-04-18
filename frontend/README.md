# Frontend Workspace

This folder contains the React/Vite dashboard for team collaboration.

## Team Workflow

1. Work only inside this folder for UI changes.
2. Use backend APIs from `http://localhost:8000` by default.
3. Keep API calls centralized in `src/lib/api.js`.

## Setup

```bash
npm install
npm run dev
```

## Environment

Create `.env` from `.env.example` if you need a custom backend URL.

## Current Live Integrations

- Dashboard stats: `GET /stats/dashboard`
- Assets list: `GET /assets`
- Asset upload: `POST /assets`
- Alerts stream: `WS /ws/alerts?token=...`
