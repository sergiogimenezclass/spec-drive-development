def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "pro@example.com",
            "password": "Passw0rd123",
            "confirm_password": "Passw0rd123",
            "name": "Juan Pérez",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["user"]["email"] == "pro@example.com"
    assert "access_token" in body

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "pro@example.com", "password": "Passw0rd123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.get_json()


def test_register_requires_strong_password(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "weak", "confirm_password": "weak", "name": "X"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


def test_register_password_mismatch(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "a@b.com",
            "password": "Passw0rd123",
            "confirm_password": "Passw0rd124",
            "name": "X",
        },
    )
    assert resp.status_code == 400


def test_mono_user_only_one_professional(client):
    payload = {
        "email": "pro@example.com",
        "password": "Passw0rd123",
        "confirm_password": "Passw0rd123",
        "name": "Uno",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    second = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "otro@example.com"},
    )
    assert second.status_code == 409
    assert second.get_json()["code"] == "PROFESSIONAL_EXISTS"


def test_login_wrong_credentials(client, auth_headers):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "pro@example.com", "password": "Nope12345"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "AUTHENTICATION_FAILED"


def test_protected_requires_token(client):
    assert client.get("/api/v1/professional/services").status_code == 401


def test_account_lockout_after_failed_logins(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pro@example.com",
            "password": "Passw0rd123",
            "confirm_password": "Passw0rd123",
            "name": "X",
        },
    )
    max_attempts = app.config["MAX_FAILED_LOGINS"]
    last = None
    for _ in range(max_attempts):
        last = client.post(
            "/api/v1/auth/login",
            json={"email": "pro@example.com", "password": "Bad12345x"},
        )
    assert last.status_code == 401
    # Ahora la cuenta está bloqueada aunque la contraseña sea correcta.
    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "pro@example.com", "password": "Passw0rd123"},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["code"] == "ACCOUNT_LOCKED"
