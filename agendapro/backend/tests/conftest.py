import os
from datetime import datetime, timedelta, timezone

import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://agendapro:agendapro@localhost:5432/agendapro"
)

from app import create_app  # noqa: E402
from app.core.extensions import db  # noqa: E402


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture(autouse=True)
def clean_db(app):
    """Limpia los datos antes de cada test (el esquema y la migración ya están aplicados)."""
    with app.app_context():
        db.session.execute(
            db.text(
                "TRUNCATE TABLE appointments, blocked_slots, working_hours, "
                "services, users, token_blocklist CASCADE"
            )
        )
        db.session.commit()
    yield


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    """Registra al profesional (mono-usuario) y devuelve headers con el access token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pro@example.com",
            "password": "Passw0rd123",
            "confirm_password": "Passw0rd123",
            "name": "Juan Pérez",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "pro@example.com", "password": "Passw0rd123"},
    )
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def next_weekday(target_weekday, weeks_ahead=2):
    """Devuelve la fecha (date) del próximo día de la semana `target_weekday` (0=Mon)."""
    today = datetime.now(timezone.utc).date()
    delta = (target_weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta + weeks_ahead * 7)


def iso_utc(dt):
    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
