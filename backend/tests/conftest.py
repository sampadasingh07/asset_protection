import os
import shutil
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.database import reset_database_cache


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    runtime_root = Path.cwd() / "test_runtime" / uuid4().hex
    runtime_root.mkdir(parents=True, exist_ok=True)

    database_path = runtime_root / "test.db"
    upload_dir = runtime_root / "uploads"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"
    os.environ["UPLOAD_DIR"] = str(upload_dir)
    os.environ["TASK_MODE"] = "eager"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["DEBUG"] = "false"

    reset_settings_cache()
    reset_database_cache()

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    shutil.rmtree(runtime_root, ignore_errors=True)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "supersecret",
            "full_name": "Owner User",
            "organisation_name": "Owner Org",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
