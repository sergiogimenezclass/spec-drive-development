from datetime import datetime, timezone


def to_iso_z(dt):
    """Serializa un datetime a ISO 8601 en UTC con sufijo 'Z' (convención de api.md)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
