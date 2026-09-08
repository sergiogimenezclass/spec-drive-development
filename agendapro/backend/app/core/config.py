import os
from datetime import timedelta


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Config:
    """Configuración base leída desde variables de entorno."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://agendapro:agendapro@localhost:5432/agendapro",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=_int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES"), 3600)
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=_int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS"), 30)
    )
    JWT_TOKEN_LOCATION = ["headers"]

    # Zona horaria por defecto del profesional (para calcular disponibilidad).
    TIMEZONE = os.environ.get("TIMEZONE", "America/Argentina/Buenos_Aires")

    # Reglas de negocio por defecto (editables por el profesional en su perfil).
    DEFAULT_MIN_ADVANCE_MINUTES = _int(os.environ.get("DEFAULT_MIN_ADVANCE_MINUTES"), 60)
    # Política de cancelación por antelación (cancel_policy_config.md): default 0 = el cliente
    # puede cancelar en cualquier momento hasta el inicio del turno.
    DEFAULT_CANCELLATION_CUTOFF_HOURS = _int(
        os.environ.get("DEFAULT_CANCELLATION_CUTOFF_HOURS"), 0
    )

    # Email (SMTP). En desarrollo apunta a MailHog.
    SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
    SMTP_PORT = _int(os.environ.get("SMTP_PORT"), 1025)
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_STARTTLS = _bool(os.environ.get("SMTP_STARTTLS"), False)
    SMTP_SSL = _bool(os.environ.get("SMTP_SSL"), False)
    MAIL_FROM = os.environ.get("MAIL_FROM", "AgendaPro Simple <no-reply@agendapro.local>")
    EMAIL_ENABLED = _bool(os.environ.get("EMAIL_ENABLED"), True)

    # URL pública usada para construir los enlaces de autogestión en los emails.
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8080")

    # Seguridad de autenticación.
    MAX_FAILED_LOGINS = _int(os.environ.get("MAX_FAILED_LOGINS"), 5)
    LOCKOUT_MINUTES = _int(os.environ.get("LOCKOUT_MINUTES"), 15)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    # Los tests corren contra Postgres en contenedor; se sobreescribe con env si hace falta.
    DEBUG = False
    # En tests unitarios no se envían emails reales (se verifica por MailHog en la integración).
    EMAIL_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


_config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return _config_by_name.get(name, DevelopmentConfig)
