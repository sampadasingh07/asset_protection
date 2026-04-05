# VeriLens Backend Scaffold

This repository contains a beginner-friendly FastAPI backend scaffold inspired by the backend guide:

- `FastAPI` for REST + WebSocket APIs
- `SQLAlchemy` models for organisations, users, assets, matches, and violations
- `Celery + Redis` task plumbing for background analysis
- adapter services for vector search and propagation tracking
- `Docker Compose` for local infrastructure

## Quick start

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Run the API with `uvicorn app.main:app --reload`.
5. Open [http://localhost:8000/docs](http://localhost:8000/docs).

## Useful commands

```powershell
pytest
alembic upgrade head
docker-compose up -d
```
