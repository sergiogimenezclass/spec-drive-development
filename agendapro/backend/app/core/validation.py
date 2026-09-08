import re
from datetime import datetime

from .errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Mínimo 8 caracteres, una mayúscula, una minúscula y un número (professional-auth.md §2.1).
_PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


def require(data, field, *, type_=None, allow_empty=False):
    """Valida presencia y tipo de un campo. Devuelve el valor (trim en strings)."""
    if data is None or field not in data:
        raise ValidationError(details=[{"field": field, "message": "Este campo es obligatorio."}])
    value = data[field]
    if isinstance(value, str):
        value = value.strip()
    if value in (None, "") and not allow_empty:
        raise ValidationError(details=[{"field": field, "message": "Este campo es obligatorio."}])
    if type_ is not None and not isinstance(value, type_):
        raise ValidationError(
            details=[{"field": field, "message": f"Debe ser de tipo {type_.__name__}."}]
        )
    return value


def require_email(data, field="email"):
    value = require(data, field, type_=str)
    if not _EMAIL_RE.match(value):
        raise ValidationError(details=[{"field": field, "message": "Introduce un email válido."}])
    return value


def require_password(data, field="password"):
    value = require(data, field, type_=str)
    if not _PASSWORD_RE.match(value):
        raise ValidationError(
            details=[
                {
                    "field": field,
                    "message": (
                        "La contraseña debe tener al menos 8 caracteres, "
                        "incluyendo una mayúscula, una minúscula y un número."
                    ),
                }
            ]
        )
    return value


def require_int(data, field, minimum=None, maximum=None):
    value = require(data, field)
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValidationError(details=[{"field": field, "message": "Debe ser un número entero."}])
    if minimum is not None and ivalue < minimum:
        raise ValidationError(details=[{"field": field, "message": f"Debe ser >= {minimum}."}])
    if maximum is not None and ivalue > maximum:
        raise ValidationError(details=[{"field": field, "message": f"Debe ser <= {maximum}."}])
    return ivalue


_NONNEG_INT_MSG = "El valor debe ser un número entero mayor o igual a 0."


def require_nonneg_int(data, field):
    """Entero >= 0 (cancel_policy_config.md P-ERR-01). Rechaza negativos, decimales y no numéricos."""
    value = require(data, field)
    if isinstance(value, bool):
        raise ValidationError(details=[{"field": field, "message": _NONNEG_INT_MSG}])
    if isinstance(value, int):
        ivalue = value
    elif isinstance(value, float):
        if not value.is_integer():
            raise ValidationError(details=[{"field": field, "message": _NONNEG_INT_MSG}])
        ivalue = int(value)
    elif isinstance(value, str):
        if not re.fullmatch(r"\d+", value.strip()):
            raise ValidationError(details=[{"field": field, "message": _NONNEG_INT_MSG}])
        ivalue = int(value.strip())
    else:
        raise ValidationError(details=[{"field": field, "message": _NONNEG_INT_MSG}])
    if ivalue < 0:
        raise ValidationError(details=[{"field": field, "message": _NONNEG_INT_MSG}])
    return ivalue


def parse_hhmm(value, field):
    if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", value or ""):
        raise ValidationError(
            details=[{"field": field, "message": "Formato de hora inválido (HH:MM)."}]
        )
    hh, mm = value.split(":")
    return int(hh), int(mm)


def parse_iso_datetime(value, field):
    if not isinstance(value, str):
        raise ValidationError(details=[{"field": field, "message": "Fecha/hora inválida."}])
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        raise ValidationError(details=[{"field": field, "message": "Fecha/hora inválida (ISO 8601)."}])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt


def parse_date(value, field="date"):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value or ""):
        raise ValidationError(details=[{"field": field, "message": "Fecha inválida (YYYY-MM-DD)."}])
    return datetime.strptime(value, "%Y-%m-%d").date()
