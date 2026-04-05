def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_read_me(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "hello@example.com",
            "password": "supersecret",
            "full_name": "Hello User",
            "organisation_name": "Hello Org",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        json={"email": "hello@example.com", "password": "supersecret"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "hello@example.com"


def test_asset_upload_and_stats(client, auth_headers):
    create_response = client.post(
        "/assets",
        headers=auth_headers,
        data={"title": "Original Asset", "vector": "[1.0, 0.0, 0.0]"},
        files={"file": ("asset.txt", b"hello world", "text/plain")},
    )
    assert create_response.status_code == 201
    asset = create_response.json()
    assert asset["title"] == "Original Asset"
    assert asset["status"] == "ready"

    detail_response = client.get(f"/assets/{asset['id']}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["file_name"] == "asset.txt"

    stats_response = client.get("/stats/dashboard", headers=auth_headers)
    assert stats_response.status_code == 200
    assert stats_response.json()["asset_count"] == 1


def test_vector_search_and_propagation(client, auth_headers):
    first_asset = client.post(
        "/assets",
        headers=auth_headers,
        data={"title": "Asset One", "vector": "[1.0, 0.0, 0.0]"},
        files={"file": ("one.txt", b"one", "text/plain")},
    ).json()
    second_asset = client.post(
        "/assets",
        headers=auth_headers,
        data={"title": "Asset Two", "vector": "[0.98, 0.02, 0.0]"},
        files={"file": ("two.txt", b"two", "text/plain")},
    ).json()

    search_response = client.post(
        "/search",
        headers=auth_headers,
        json={"asset_id": second_asset["id"], "limit": 3},
    )
    assert search_response.status_code == 200
    results = search_response.json()
    assert results
    assert results[0]["asset_id"] == first_asset["id"]

    propagation_response = client.get(
        f"/propagation/{second_asset['id']}",
        headers=auth_headers,
    )
    assert propagation_response.status_code == 200
    graph = propagation_response.json()
    assert len(graph["nodes"]) >= 2
    assert any(edge["source"] == first_asset["id"] for edge in graph["edges"])


def test_websocket_alert_for_high_similarity_violation(client, auth_headers):
    client.post(
        "/assets",
        headers=auth_headers,
        data={"title": "Seed Asset", "vector": "[1.0, 0.0, 0.0]"},
        files={"file": ("seed.txt", b"seed", "text/plain")},
    )

    with client.websocket_connect("/ws/alerts") as websocket:
        response = client.post(
            "/assets",
            headers=auth_headers,
            data={"title": "Possible Copy", "vector": "[0.99, 0.01, 0.0]"},
            files={"file": ("copy.txt", b"copy", "text/plain")},
        )
        assert response.status_code == 201

        alert = websocket.receive_json()
        assert alert["event"] == "violation.detected"
        assert alert["severity"] in {"high", "critical"}

