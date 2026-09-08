from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..core.errors import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from ..core.extensions import db
from ..core.timeutil import to_iso_z
from ..core.validation import parse_date, parse_iso_datetime, require, require_email
from ..models import Appointment, AppointmentStatus, Service, User
from ..services.availability import compute_available_slots, is_slot_bookable
from ..services.notifications import send_booking_confirmation, send_cancellation, send_reschedule
from .helpers import (
    blocked_intervals,
    busy_intervals,
    min_advance_until,
    weekly_hours_map,
)

bp = Blueprint("public", __name__, url_prefix="/api/v1/public")


def _the_professional() -> User:
    user = db.session.execute(select(User)).scalars().first()
    if not user:
        raise NotFoundError("El profesional no está configurado todavía.")
    return user


@bp.get("/services")
def public_services():
    user = _the_professional()
    items = db.session.execute(
        select(Service).where(Service.user_id == user.id).order_by(Service.name)
    ).scalars().all()
    return jsonify([s.to_dict() for s in items])


@bp.get("/available-slots")
def available_slots():
    user = _the_professional()
    service_id = request.args.get("serviceId") or request.args.get("service_id")
    date_str = request.args.get("date")
    if not service_id or not date_str:
        raise ValidationError("Se requieren serviceId y date (YYYY-MM-DD).")

    service = db.session.get(Service, service_id)
    if not service or service.user_id != user.id:
        raise NotFoundError("Servicio no encontrado.")

    target = parse_date(date_str)
    weekday = target.weekday()  # 0=Monday
    # database.md usa 0=Domingo; convertimos.
    dow_sunday_based = (weekday + 1) % 7
    wh = weekly_hours_map(user).get(dow_sunday_based)

    slots = compute_available_slots(
        target_date=target,
        weekly_hours_for_day=wh,
        blocked_intervals=blocked_intervals(user, target),
        busy_intervals=busy_intervals(user, target),
        duration_minutes=service.duration_minutes,
        timezone=user.timezone,
        min_advance_until=min_advance_until(user),
    )
    return jsonify(
        [{"start_time": to_iso_z(s), "end_time": to_iso_z(e)} for s, e in slots]
    )


@bp.post("/appointments")
def create_appointment():
    user = _the_professional()
    data = request.get_json(silent=True) or {}
    service_id = require(data, "service_id")
    start = parse_iso_datetime(require(data, "start_time"), "start_time")
    client_name = require(data, "client_name")
    client_email = require_email(data, "client_email")
    client_phone = data.get("client_phone")

    service = db.session.get(Service, service_id)
    if not service or service.user_id != user.id:
        raise NotFoundError("Servicio no encontrado.")

    start_utc = start.astimezone(ZoneInfo("UTC"))
    end_utc = start_utc + timedelta(minutes=service.duration_minutes)
    target_date = start_utc.astimezone(ZoneInfo(user.timezone)).date()

    ok, reason = is_slot_bookable(
        start_utc,
        end_utc,
        blocked_intervals(user, target_date),
        busy_intervals(user, target_date),
        min_advance_until(user),
    )
    if not ok:
        if reason == "ANTICIPATION_TOO_SHORT":
            raise BusinessRuleError(
                f"La reserva debe hacerse con al menos {user.min_advance_minutes} minutos de anticipación."
            )
        raise ConflictError("El horario solicitado ya no está disponible.", code=reason)

    appt = Appointment(
        start_time=start_utc,
        end_time=end_utc,
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        status=AppointmentStatus.BOOKED,
        notes=data.get("notes"),
        service_id=service.id,
        user_id=user.id,
    )
    db.session.add(appt)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El horario solicitado ya no está disponible.", code="ALREADY_BOOKED")

    send_booking_confirmation(appt)
    return jsonify(appt.to_dict(include_token=True)), 201


def _appointment_by_token(token: str) -> Appointment:
    appt = db.session.execute(
        select(Appointment).where(Appointment.booking_token == token)
    ).scalars().first()
    if not appt:
        raise NotFoundError("Turno no encontrado.")
    return appt


def _now_utc():
    return datetime.now(ZoneInfo("UTC"))


def _self_management_state(appt: Appointment) -> dict:
    """Estado de autogestión para el cliente (cancel_policy_config.md §2.2)."""
    user = appt.user
    now = _now_utc()
    started = now >= appt.start_time
    cutoff = appt.start_time - timedelta(hours=user.cancellation_cutoff_hours)
    # C-EDGE-01: en el límite exacto (now == cutoff) SÍ se permite -> bloqueamos solo si now > cutoff.
    within_window = now > cutoff
    can_cancel = appt.status == AppointmentStatus.BOOKED and not started and not within_window
    return {
        "cancellation_cutoff_hours": user.cancellation_cutoff_hours,
        "cancel_deadline": to_iso_z(cutoff),
        "started": started,
        "can_cancel": can_cancel,
    }


def _assert_can_self_manage(appt: Appointment, action: str):
    """Valida que el cliente pueda autogestionar (cancelar/reagendar) su turno.

    Regla de prioridad (C-EDGE-02): un turno ya iniciado/pasado NO es gestionable,
    y ese mensaje tiene prioridad sobre el de la política de antelación.
    """
    user = appt.user
    now = _now_utc()
    if now >= appt.start_time:
        raise BusinessRuleError(
            "El turno ya comenzó o finalizó; no podés gestionarlo de forma autónoma. "
            "Contactá al profesional.",
            code="APPOINTMENT_STARTED",
        )
    cutoff = appt.start_time - timedelta(hours=user.cancellation_cutoff_hours)
    if now > cutoff:
        raise BusinessRuleError(
            f"El plazo para {action} en línea venció: debe hacerse con al menos "
            f"{user.cancellation_cutoff_hours} h de anticipación. Contactá al profesional.",
            code="SELF_MANAGE_DEADLINE_PASSED",
        )


@bp.get("/appointments/<token>")
def get_appointment(token):
    appt = _appointment_by_token(token)
    data = appt.to_dict()
    data["self_management"] = _self_management_state(appt)
    return jsonify(data)


@bp.put("/appointments/<token>/cancel")
def cancel_appointment(token):
    appt = _appointment_by_token(token)
    if appt.status != AppointmentStatus.BOOKED:
        raise BusinessRuleError("Este turno ya no está activo.")
    _assert_can_self_manage(appt, "cancelar")
    appt.status = AppointmentStatus.CANCELLED
    db.session.commit()
    send_cancellation(appt, by="client")
    data = appt.to_dict()
    data["self_management"] = _self_management_state(appt)
    return jsonify(data)


@bp.put("/appointments/<token>/reschedule")
def reschedule_appointment(token):
    user = _the_professional()
    appt = _appointment_by_token(token)
    if appt.status != AppointmentStatus.BOOKED:
        raise BusinessRuleError("Este turno ya no está activo.")
    _assert_can_self_manage(appt, "reagendar")

    data = request.get_json(silent=True) or {}
    new_start = parse_iso_datetime(require(data, "new_start_time"), "new_start_time")
    duration = appt.end_time - appt.start_time
    new_start_utc = new_start.astimezone(ZoneInfo("UTC"))
    new_end_utc = new_start_utc + duration
    target_date = new_start_utc.astimezone(ZoneInfo(user.timezone)).date()

    ok, reason = is_slot_bookable(
        new_start_utc,
        new_end_utc,
        blocked_intervals(user, target_date),
        busy_intervals(user, target_date, exclude_appointment_id=appt.id),
        min_advance_until(user),
    )
    if not ok:
        if reason == "ANTICIPATION_TOO_SHORT":
            raise BusinessRuleError(
                f"El nuevo horario debe respetar {user.min_advance_minutes} minutos de anticipación."
            )
        raise ConflictError("El horario solicitado no está disponible.", code=reason)

    old_start = appt.start_time
    appt.start_time = new_start_utc
    appt.end_time = new_end_utc
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El horario solicitado ya no está disponible.", code="ALREADY_BOOKED")
    send_reschedule(appt, by="client", old_start=old_start)
    out = appt.to_dict()
    out["self_management"] = _self_management_state(appt)
    return jsonify(out)
