from datetime import datetime, timedelta, timezone

from conftest import iso_utc, next_weekday


def setup_week_and_service(client, auth_headers):
    # Horario: lunes (day_of_week=1) de 09:00 a 17:00.
    r = client.put(
        "/api/v1/professional/availability/weekly-hours",
        headers=auth_headers,
        json=[{"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}],
    )
    assert r.status_code == 200
    svc = client.post(
        "/api/v1/professional/services",
        headers=auth_headers,
        json={"name": "Consulta", "duration_minutes": 60, "description": "Sesión"},
    )
    assert svc.status_code == 201
    return svc.get_json()["id"]


def first_slot(client, service_id, monday):
    resp = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    )
    assert resp.status_code == 200
    slots = resp.get_json()
    assert len(slots) > 0
    return slots


def book(client, service_id, start_iso, name="Ana Client", email="ana@client.com"):
    return client.post(
        "/api/v1/public/appointments",
        json={
            "service_id": service_id,
            "start_time": start_iso,
            "client_name": name,
            "client_email": email,
            "client_phone": "112233",
        },
    )


def test_service_crud_and_duplicate(client, auth_headers):
    setup_week_and_service(client, auth_headers)
    dup = client.post(
        "/api/v1/professional/services",
        headers=auth_headers,
        json={"name": "Consulta", "duration_minutes": 30},
    )
    assert dup.status_code == 409
    assert dup.get_json()["code"] == "SERVICE_NAME_TAKEN"

    listing = client.get("/api/v1/professional/services", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.get_json()) == 1


def test_public_services_and_slots(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    pub = client.get("/api/v1/public/services")
    assert pub.status_code == 200
    assert pub.get_json()[0]["id"] == service_id

    monday = next_weekday(0)
    slots = first_slot(client, service_id, monday)
    # 09:00-17:00 con 60 min → 8 slots.
    assert len(slots) == 8
    assert slots[0]["start_time"].endswith("Z")


def test_booking_and_double_booking(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slot = first_slot(client, service_id, monday)[0]

    created = book(client, service_id, slot["start_time"])
    assert created.status_code == 201
    appt = created.get_json()
    assert appt["status"] == "BOOKED"
    assert appt["booking_token"]

    # El mismo slot ya no debe estar disponible.
    remaining = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    ).get_json()
    assert slot["start_time"] not in [s["start_time"] for s in remaining]

    # Intento de doble reserva → 409.
    again = book(client, service_id, slot["start_time"], email="otro@client.com")
    assert again.status_code == 409
    assert again.get_json()["code"] == "ALREADY_BOOKED"


def test_cancel_via_token_frees_slot(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slot = first_slot(client, service_id, monday)[0]
    appt = book(client, service_id, slot["start_time"]).get_json()

    cancel = client.put(f"/api/v1/public/appointments/{appt['booking_token']}/cancel")
    assert cancel.status_code == 200
    assert cancel.get_json()["status"] == "CANCELLED"

    # El slot vuelve a estar disponible.
    slots = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    ).get_json()
    assert slot["start_time"] in [s["start_time"] for s in slots]


def test_reschedule_via_token(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slots = first_slot(client, service_id, monday)
    appt = book(client, service_id, slots[0]["start_time"]).get_json()

    new_start = slots[2]["start_time"]
    res = client.put(
        f"/api/v1/public/appointments/{appt['booking_token']}/reschedule",
        json={"new_start_time": new_start},
    )
    assert res.status_code == 200
    assert res.get_json()["start_time"] == new_start


def test_cancellation_cutoff_blocks_client(client, auth_headers):
    # Cutoff de 1000 h (~41 días) > turno a ~2 semanas → el cliente no puede cancelar (Regla #4).
    client.put(
        "/api/v1/professional",
        headers=auth_headers,
        json={"cancellation_cutoff_hours": 1000},
    )
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slot = first_slot(client, service_id, monday)[0]
    appt = book(client, service_id, slot["start_time"]).get_json()

    cancel = client.put(f"/api/v1/public/appointments/{appt['booking_token']}/cancel")
    assert cancel.status_code == 422
    assert cancel.get_json()["code"] == "SELF_MANAGE_DEADLINE_PASSED"


def test_min_advance_blocks_near_slots(client, auth_headers):
    # Min advance de 100000 minutos → ningún slot cercano es reservable.
    client.put(
        "/api/v1/professional",
        headers=auth_headers,
        json={"min_advance_minutes": 100000},
    )
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slots = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    ).get_json()
    assert slots == []


def test_blocked_slot_removes_availability(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slots = first_slot(client, service_id, monday)
    target = slots[0]

    client.post(
        "/api/v1/professional/availability/blocked-slots",
        headers=auth_headers,
        json={
            "start_time": target["start_time"],
            "end_time": target["end_time"],
            "reason": "Almuerzo",
        },
    )
    after = client.get(
        "/api/v1/public/available-slots",
        query_string={"serviceId": service_id, "date": monday.isoformat()},
    ).get_json()
    assert target["start_time"] not in [s["start_time"] for s in after]


def test_professional_status_and_reschedule(client, auth_headers):
    service_id = setup_week_and_service(client, auth_headers)
    monday = next_weekday(0)
    slots = first_slot(client, service_id, monday)
    appt = book(client, service_id, slots[0]["start_time"]).get_json()

    # Listar turnos del profesional.
    listing = client.get(
        "/api/v1/professional/appointments",
        headers=auth_headers,
        query_string={"date": monday.isoformat()},
    )
    assert listing.status_code == 200
    assert len(listing.get_json()) == 1

    # Marcar completado.
    done = client.put(
        f"/api/v1/professional/appointments/{appt['id']}/status",
        headers=auth_headers,
        json={"status": "COMPLETED"},
    )
    assert done.status_code == 200
    assert done.get_json()["status"] == "COMPLETED"
