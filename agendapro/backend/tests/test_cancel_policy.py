"""Tests para cancel_policy_config.md (Política de Cancelación por Antelación)."""
from datetime import datetime, timedelta, timezone

from app.core.extensions import db
from app.models import Appointment

from conftest import iso_utc, next_weekday


def setup(client, auth_headers):
    client.put(
        "/api/v1/professional/availability/weekly-hours",
        headers=auth_headers,
        json=[{"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}],
    )
    svc = client.post(
        "/api/v1/professional/services",
        headers=auth_headers,
        json={"name": "Consulta", "duration_minutes": 60},
    )
    service_id = svc.get_json()["id"]
    monday = next_weekday(0)
    slots = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    ).get_json()
    book = client.post(
        "/api/v1/public/appointments",
        json={
            "service_id": service_id,
            "start_time": slots[0]["start_time"],
            "client_name": "Ana",
            "client_email": "ana@client.com",
        },
    ).get_json()
    return book


def test_default_cutoff_is_zero(client, auth_headers):
    prof = client.get("/api/v1/professional", headers=auth_headers).get_json()
    assert prof["cancellation_cutoff_hours"] == 0


def test_zero_cutoff_allows_cancel_anytime_before_start(client, auth_headers):
    book = setup(client, auth_headers)
    cancel = client.put(f"/api/v1/public/appointments/{book['booking_token']}/cancel")
    assert cancel.status_code == 200
    assert cancel.get_json()["status"] == "CANCELLED"


def test_cutoff_persists_and_preloads(client, auth_headers):
    r = client.put(
        "/api/v1/professional",
        headers=auth_headers,
        json={"cancellation_cutoff_hours": 12},
    )
    assert r.status_code == 200
    assert r.get_json()["cancellation_cutoff_hours"] == 12
    prof = client.get("/api/v1/professional", headers=auth_headers).get_json()
    assert prof["cancellation_cutoff_hours"] == 12


def test_cutoff_blocks_within_window_and_flags_state(client, auth_headers):
    client.put(
        "/api/v1/professional",
        headers=auth_headers,
        json={"cancellation_cutoff_hours": 1000},
    )
    book = setup(client, auth_headers)
    token = book["booking_token"]

    state = client.get(f"/api/v1/public/appointments/{token}").get_json()["self_management"]
    assert state["can_cancel"] is False
    assert state["started"] is False
    assert state["cancellation_cutoff_hours"] == 1000

    cancel = client.put(f"/api/v1/public/appointments/{token}/cancel")
    assert cancel.status_code == 422
    assert cancel.get_json()["code"] == "SELF_MANAGE_DEADLINE_PASSED"


def test_can_cancel_flag_true_when_zero_cutoff(client, auth_headers):
    book = setup(client, auth_headers)
    state = client.get(f"/api/v1/public/appointments/{book['booking_token']}").get_json()["self_management"]
    assert state["can_cancel"] is True


def test_invalid_cutoff_values_rejected(client, auth_headers):
    for bad in (-1, 12.5, "abc"):
        resp = client.put(
            "/api/v1/professional",
            headers=auth_headers,
            json={"cancellation_cutoff_hours": bad},
        )
        assert resp.status_code == 400, f"valor {bad!r} no debería aceptarse"
        assert "entero mayor o igual a 0" in resp.get_json()["details"][0]["message"]


def test_started_appointment_has_priority_message(client, auth_headers):
    book = setup(client, auth_headers)
    token = book["booking_token"]

    # Forzar un turno ya iniciado (en el pasado) conservando status BOOKED.
    with client.application.app_context():
        appt = db.session.get(Appointment, book["id"])
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        appt.start_time = past
        appt.end_time = past + timedelta(hours=1)
        db.session.commit()

    cancel = client.put(f"/api/v1/public/appointments/{token}/cancel")
    assert cancel.status_code == 422
    assert cancel.get_json()["code"] == "APPOINTMENT_STARTED"
    state = client.get(f"/api/v1/public/appointments/{token}").get_json()["self_management"]
    assert state["started"] is True
    assert state["can_cancel"] is False
