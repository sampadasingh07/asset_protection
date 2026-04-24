
asset_protection/          ← repo root (already exists)
│
├── workers/               ← NEW folder, create this
│   ├── __init__.py
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   ├── scrapers/          ← NEW subfolder
│   │   ├── __init__.py
│   │   ├── social_crawler.py
│   │   └── pirate_crawler.py
│   │
│   ├── tasks/             ← NEW subfolder
│   │   ├── __init__.py
│   │   └── celery_tasks.py
│   │
│   └── enforcement/       ← NEW subfolder
│       ├── __init__.py
│       ├── dmca_generator.py
│       └── high_risk_ledger.py
│
└── docker-compose.yml     ← NEW file, at repo root (same level as README.md)
