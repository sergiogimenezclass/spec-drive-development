from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask_jwt_extended import get_jwt_identity
from sqlalchemy import select

from ..core.errors import AuthenticationError, NotFoundError
from ..core.extensions import db
from ..models import Appointment, AppointmentStatus, BlockedSlot, User, WorkingHours
from ..models.base import ACTIVE_STATUSES


def current_professional() -> User:
    uid = get_jwt_identity()
    if not uid:
        raise AuthenticationError("No autenticado.")
    user = db.session.get(User, uid)
    if not user:
        raise AuthenticationError("El usuario del token ya no existe.")
    return user


def get_professional_or_404() -> User:
    # En mono-usuario el profesional autenticado es el único.
    return current_professional()


def weekly_hours_map(user: User) -> dict:
    return {
        wh.day_of_week: {"start_time": wh.start_time, "end_time": wh.end_time}
        for wh in user.working_hours
    }


def _day_window_utc(user: User, target_date):
    """Ventana [inicio, fin) del día en UTC para consultar bloqueos/turnos."""
    tz = ZoneInfo(user.timezone)
    start_local = datetime.combine(target_date, time(0, 0), tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(ZoneInfo("UTC")), end_local.astimezone(ZoneInfo("UTC"))


def busy_intervals(user: User, target_date, exclude_appointment_id=None):
    day_start, day_end = _day_window_utc(user, target_date)
    stmt = (
        select(Appointment)
        .where(
            Appointment.user_id == user.id,
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.start_time < day_end,
            Appointment.end_time > day_start,
        )
    )
    result = db.session.execute(stmt).scalars().all()
    intervals = [(a.start_time, a.end_time) for a in result if a.id != exclude_appointment_id]
    return intervals


def blocked_intervals(user: User, target_date):
    day_start, day_end = _day_window_utc(user, target_date)
    stmt = select(BlockedSlot).where(
        BlockedSlot.user_id == user.id,
        BlockedSlot.start_time < day_end,
        BlockedSlot.end_time > day_start,
    )
    result = db.session.execute(stmt).scalars().all()
    return [(b.start_time, b.end_time) for b in result]


def min_advance_until(user: User) -> datetime:
    return datetime.now(ZoneInfo("UTC")) + timedelta(minutes=user.min_advance_minutes)
