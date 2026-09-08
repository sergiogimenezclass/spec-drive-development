"""Lógica de disponibilidad y cálculo de slots.

Funciones puras (sin acceso a BD) para que sean testeables. La capa API prepara
los datos (horarios, bloqueos, turnos activos) y las invoca.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..models import AppointmentStatus


def _overlap(a_start, a_end, b_start, b_end):
    """Dos intervalos [start, end) se solapan si a_start < b_end y b_start < a_end."""
    return a_start < b_end and b_start < a_end


def compute_available_slots(
    target_date,
    weekly_hours_for_day,
    blocked_intervals,
    busy_intervals,
    duration_minutes,
    timezone,
    min_advance_until,
    step_minutes=None,
):
    """Devuelve una lista de (start_utc, end_utc) reservables.

    - target_date: date (calendario local del profesional).
    - weekly_hours_for_day: dict {"start_time": "HH:MM", "end_time": "HH:MM"} o None.
    - blocked_intervals / busy_intervals: listas de (start_aware, end_aware) en UTC.
    - duration_minutes: duración del servicio.
    - timezone: nombre IANA del profesional.
    - min_advance_until: datetime aware; un slot no puede empezar antes de este momento.
    - step_minutes: granularidad de arranque de slots (por defecto = duración).
    """
    if not weekly_hours_for_day:
        return []

    tz = ZoneInfo(timezone)
    sh, sm = _hhmm(weekly_hours_for_day["start_time"])
    eh, em = _hhmm(weekly_hours_for_day["end_time"])
    day_start_local = datetime.combine(target_date, time(sh, sm), tzinfo=tz)
    day_end_local = datetime.combine(target_date, time(eh, em), tzinfo=tz)
    if day_end_local <= day_start_local:
        return []

    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes if step_minutes is not None else duration_minutes)
    if step <= timedelta(0):
        step = duration

    # Normalizamos bloqueos/ocupación a aware UTC para comparar.
    blocked = [_to_utc_pair(s, e) for s, e in blocked_intervals]
    busy = [_to_utc_pair(s, e) for s, e in busy_intervals]
    min_advance_utc = min_advance_until.astimezone(ZoneInfo("UTC")) if min_advance_until else None

    slots = []
    cursor = day_start_local
    while cursor + duration <= day_end_local:
        slot_end = cursor + duration
        slot_start_utc = cursor.astimezone(ZoneInfo("UTC"))
        slot_end_utc = slot_end.astimezone(ZoneInfo("UTC"))

        valid = True
        if min_advance_utc is not None and slot_start_utc < min_advance_utc:
            valid = False
        if valid:
            for b_start, b_end in blocked + busy:
                if _overlap(slot_start_utc, slot_end_utc, b_start, b_end):
                    valid = False
                    break
        if valid:
            slots.append((slot_start_utc, slot_end_utc))
        cursor += step

    return slots


def is_slot_bookable(
    slot_start_utc,
    slot_end_utc,
    blocked_intervals,
    busy_intervals,
    min_advance_until,
):
    """Revalidación puntual al crear un turno. Devuelve (ok, motivo)."""
    if min_advance_until and slot_start_utc < min_advance_until.astimezone(ZoneInfo("UTC")):
        return False, "ANTICIPATION_TOO_SHORT"

    blocked = [_to_utc_pair(s, e) for s, e in blocked_intervals]
    busy = [_to_utc_pair(s, e) for s, e in busy_intervals]
    for b_start, b_end in blocked:
        if _overlap(slot_start_utc, slot_end_utc, b_start, b_end):
            return False, "BLOCKED"
    for b_start, b_end in busy:
        if _overlap(slot_start_utc, slot_end_utc, b_start, b_end):
            return False, "ALREADY_BOOKED"
    return True, None


def _hhmm(value):
    hh, mm = value.split(":")
    return int(hh), int(mm)


def _to_utc_pair(start, end):
    utc = ZoneInfo("UTC")
    return start.astimezone(utc), end.astimezone(utc)
