from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..core.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ..core.extensions import bcrypt, db
from ..core.validation import (
    parse_date,
    parse_hhmm,
    parse_iso_datetime,
    require,
    require_int,
    require_nonneg_int,
)
from ..models import (
    Appointment,
    AppointmentStatus,
    BlockedSlot,
    Service,
    WorkingHours,
)
from ..services.availability import is_slot_bookable
from ..services.notifications import send_cancellation, send_reschedule
from .helpers import (
    blocked_intervals,
    busy_intervals,
    current_professional,
    min_advance_until,
)

bp = Blueprint("professional", __name__, url_prefix="/api/v1/professional")


# ---------- Perfil ----------

@bp.get("")
@jwt_required()
def get_profile():
    return jsonify(current_professional().to_public_dict())


@bp.put("")
@jwt_required()
def update_profile():
    user = current_professional()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = require(data, "name")
        user.name = name
    if "phone" in data:
        phone = data.get("phone")
        user.contact_phone = phone.strip() if phone else None
    if "timezone" in data:
        user.timezone = require(data, "timezone")
    if "min_advance_minutes" in data:
        user.min_advance_minutes = require_int(data, "min_advance_minutes", minimum=0, maximum=100000)
    if "cancellation_cutoff_hours" in data:
        # cancel_policy_config.md: entero >= 0, sin máximo arbitrario.
        user.cancellation_cutoff_hours = require_nonneg_int(data, "cancellation_cutoff_hours")
    db.session.commit()
    return jsonify(user.to_public_dict())


@bp.put("/password")
@jwt_required()
def change_password():
    user = current_professional()
    data = request.get_json(silent=True) or {}
    from ..core.validation import require_password

    current = require(data, "current_password")
    if not bcrypt.check_password_hash(user.password, current):
        raise ValidationError(details=[{"field": "current_password", "message": "La contraseña actual es incorrecta."}])
    new = require_password(data, "new_password")
    confirm = require(data, "confirm_password")
    if new != confirm:
        raise ValidationError(details=[{"field": "confirm_password", "message": "Las contraseñas no coinciden."}])
    user.password = bcrypt.generate_password_hash(new).decode()
    db.session.commit()
    return jsonify({"message": "Contraseña cambiada correctamente."})


# ---------- Servicios ----------

@bp.get("/services")
@jwt_required()
def list_services():
    user = current_professional()
    items = db.session.execute(
        select(Service).where(Service.user_id == user.id).order_by(Service.name)
    ).scalars().all()
    return jsonify([s.to_dict() for s in items])


@bp.post("/services")
@jwt_required()
def create_service():
    user = current_professional()
    data = request.get_json(silent=True) or {}
    name = require(data, "name")
    duration = require_int(data, "duration_minutes", minimum=5, maximum=24 * 60)
    description = data.get("description")
    service = Service(
        name=name, duration_minutes=duration, description=description, user_id=user.id
    )
    db.session.add(service)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya existe un servicio con ese nombre.", code="SERVICE_NAME_TAKEN")
    return jsonify(service.to_dict()), 201


def _get_owned_service(service_id) -> Service:
    user = current_professional()
    service = db.session.get(Service, service_id)
    if not service or service.user_id != user.id:
        raise NotFoundError("Servicio no encontrado.")
    return service


@bp.get("/services/<service_id>")
@jwt_required()
def get_service(service_id):
    return jsonify(_get_owned_service(service_id).to_dict())


@bp.put("/services/<service_id>")
@jwt_required()
def update_service(service_id):
    service = _get_owned_service(service_id)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        service.name = require(data, "name")
    if "duration_minutes" in data:
        service.duration_minutes = require_int(data, "duration_minutes", minimum=5, maximum=24 * 60)
    if "description" in data:
        service.description = data.get("description")
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya existe un servicio con ese nombre.", code="SERVICE_NAME_TAKEN")
    return jsonify(service.to_dict())


@bp.delete("/services/<service_id>")
@jwt_required()
def delete_service(service_id):
    service = _get_owned_service(service_id)
    db.session.delete(service)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError(
            "No se puede eliminar un servicio con turnos asociados.", code="SERVICE_IN_USE"
        )
    return jsonify({"message": "Service deleted successfully"})


# ---------- Disponibilidad ----------

@bp.get("/availability")
@jwt_required()
def get_availability():
    user = current_professional()
    return jsonify(
        {
            "weekly_hours": [w.to_dict() for w in user.working_hours],
            "blocked_slots": [b.to_dict() for b in user.blocked_slots],
        }
    )


@bp.put("/availability/weekly-hours")
@jwt_required()
def set_weekly_hours():
    """Reemplaza el horario semanal completo. Body: lista de {day_of_week, start_time, end_time}."""
    user = current_professional()
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        raise ValidationError("Se esperaba una lista de horarios.")

    parsed = []
    seen_days = set()
    for item in data:
        day = require_int(item, "day_of_week", minimum=0, maximum=6)
        start = require(item, "start_time")
        end = require(item, "end_time")
        parse_hhmm(start, "start_time")
        parse_hhmm(end, "end_time")
        if day in seen_days:
            raise ValidationError(details=[{"field": "day_of_week", "message": "Día duplicado."}])
        seen_days.add(day)
        parsed.append((day, start, end))

    user.working_hours.clear()
    for day, start, end in parsed:
        user.working_hours.append(WorkingHours(day_of_week=day, start_time=start, end_time=end))
    db.session.commit()
    return jsonify([w.to_dict() for w in user.working_hours])


@bp.post("/availability/blocked-slots")
@jwt_required()
def create_blocked_slot():
    user = current_professional()
    data = request.get_json(silent=True) or {}
    start = parse_iso_datetime(require(data, "start_time"), "start_time")
    end = parse_iso_datetime(require(data, "end_time"), "end_time")
    if end <= start:
        raise ValidationError(details=[{"field": "end_time", "message": "La hora de fin debe ser posterior al inicio."}])
    block = BlockedSlot(
        start_time=start, end_time=end, reason=data.get("reason"), user_id=user.id
    )
    db.session.add(block)
    db.session.commit()
    return jsonify(block.to_dict()), 201


@bp.delete("/availability/blocked-slots/<block_id>")
@jwt_required()
def delete_blocked_slot(block_id):
    user = current_professional()
    block = db.session.get(BlockedSlot, block_id)
    if not block or block.user_id != user.id:
        raise NotFoundError("Bloqueo no encontrado.")
    db.session.delete(block)
    db.session.commit()
    return jsonify({"message": "Blocked slot deleted successfully"})


# ---------- Turnos (profesional) ----------

@bp.get("/appointments")
@jwt_required()
def list_appointments():
    user = current_professional()
    stmt = select(Appointment).where(Appointment.user_id == user.id)

    date_str = request.args.get("date")
    if date_str:
        target = parse_date(date_str)
        tz = ZoneInfo(user.timezone)
        day_start = datetime.combine(target, time(0, 0), tzinfo=tz).astimezone(ZoneInfo("UTC"))
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(Appointment.start_time >= day_start, Appointment.start_time < day_end)

    status_str = request.args.get("status")
    if status_str:
        try:
            stmt = stmt.where(Appointment.status == AppointmentStatus[status_str.upper()])
        except KeyError:
            raise ValidationError(details=[{"field": "status", "message": "Estado inválido."}])

    items = db.session.execute(stmt.order_by(Appointment.start_time)).scalars().all()
    return jsonify([a.to_dict(include_token=True) for a in items])


def _get_owned_appointment(appointment_id) -> Appointment:
    user = current_professional()
    appt = db.session.get(Appointment, appointment_id)
    if not appt or appt.user_id != user.id:
        raise NotFoundError("Turno no encontrado.")
    return appt


@bp.get("/appointments/<appointment_id>")
@jwt_required()
def get_appointment(appointment_id):
    return jsonify(_get_owned_appointment(appointment_id).to_dict(include_token=True))


@bp.put("/appointments/<appointment_id>/status")
@jwt_required()
def update_appointment_status(appointment_id):
    appt = _get_owned_appointment(appointment_id)
    data = request.get_json(silent=True) or {}
    status_str = require(data, "status")
    try:
        new_status = AppointmentStatus[status_str.upper()]
    except KeyError:
        raise ValidationError(details=[{"field": "status", "message": "Estado inválido."}])

    old_status = appt.status
    appt.status = new_status
    db.session.commit()
    if new_status == AppointmentStatus.CANCELLED and old_status != AppointmentStatus.CANCELLED:
        send_cancellation(appt, by="professional")
    return jsonify(appt.to_dict(include_token=True))


@bp.put("/appointments/<appointment_id>/reschedule")
@jwt_required()
def reschedule_appointment(appointment_id):
    user = current_professional()
    appt = _get_owned_appointment(appointment_id)
    data = request.get_json(silent=True) or {}
    new_start = parse_iso_datetime(require(data, "new_start_time"), "new_start_time")

    if appt.status not in (AppointmentStatus.BOOKED,):
        raise BusinessRuleError("Solo se pueden reagendar turnos activos.")

    duration = appt.end_time - appt.start_time
    new_end = new_start + duration
    target_date = new_start.astimezone(ZoneInfo(user.timezone)).date()

    ok, reason = is_slot_bookable(
        new_start, new_end,
        blocked_intervals(user, target_date),
        busy_intervals(user, target_date, exclude_appointment_id=appt.id),
        min_advance_until=None,  # el profesional puede reprogramar sin límite de anticipación
    )
    if not ok:
        raise ConflictError("El horario solicitado no está disponible.", code=reason)

    old_start = appt.start_time
    appt.start_time = new_start
    appt.end_time = new_end
    db.session.commit()
    send_reschedule(appt, by="professional", old_start=old_start)
    return jsonify(appt.to_dict(include_token=True))
