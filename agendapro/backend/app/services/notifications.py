import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from ..core.extensions import db
from ..models import Appointment, User


def _send(to_addr, subject, html):
    cfg = current_app.config
    if not cfg.get("EMAIL_ENABLED", True):
        current_app.logger.info("EMAIL_ENABLED=false; se omite envío a %s (%s)", to_addr, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = to_addr
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        host, port = cfg["SMTP_HOST"], cfg["SMTP_PORT"]
        if cfg.get("SMTP_SSL"):
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if cfg.get("SMTP_STARTTLS"):
                server.starttls()
        if cfg.get("SMTP_USER"):
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
        server.sendmail(cfg["MAIL_FROM"], [to_addr], msg.as_string())
        server.quit()
        current_app.logger.info("Email enviado a %s: %s", to_addr, subject)
        return True
    except Exception:  # noqa: BLE001 - no debe tumbar la operación de negocio
        current_app.logger.exception("Fallo al enviar email a %s", to_addr)
        return False


def _manage_link(appointment):
    base = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
    return f"{base}/manage/{appointment.booking_token}"


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def _layout(title, rows):
    body = "".join(
        f"<tr><td style='padding:6px 12px;color:#555'>{k}</td>"
        f"<td style='padding:6px 12px;font-weight:600'>{v}</td></tr>"
        for k, v in rows
    )
    return (
        f"<div style='font-family:system-ui,Arial;max-width:520px;margin:auto'>"
        f"<h2 style='color:#111'>{title}</h2>"
        f"<table style='border-collapse:collapse'>{body}</table></div>"
    )


def _notify_professionals(appointment, subject, html):
    pro = db.session.get(User, appointment.user_id)
    if pro:
        _send(pro.email, subject, html)


def send_booking_confirmation(appointment):
    link = _manage_link(appointment)
    rows = [
        ("Servicio", appointment.service.name if appointment.service else "-"),
        ("Fecha y hora", _fmt(appointment.start_time)),
        ("Hasta", _fmt(appointment.end_time)),
        ("Profesional", appointment.user.name if appointment.user else "-"),
    ]
    html = (
        _layout("Turno confirmado", rows)
        + f"<p style='font-family:system-ui'>¿Necesitás cancelar o reagendar? Usá tu enlace personal:"
        f"<br><a href='{link}'>{link}</a></p>"
    )
    _send(appointment.client_email, "Tu turno está confirmado", html)
    _notify_professionals(
        appointment,
        f"Nueva reserva: {appointment.client_name}",
        _layout("Nueva reserva recibida", rows + [("Cliente", appointment.client_name),
                                                    ("Email cliente", appointment.client_email)]),
    )


def send_cancellation(appointment, by):
    who = "el cliente" if by == "client" else "el profesional"
    rows = [
        ("Servicio", appointment.service.name if appointment.service else "-"),
        ("Fecha original", _fmt(appointment.start_time)),
        ("Cancelado por", who),
    ]
    html = _layout("Turno cancelado", rows)
    _send(appointment.client_email, "Tu turno fue cancelado", html)
    _notify_professionals(appointment, "Turno cancelado", html)


def send_reschedule(appointment, by, old_start=None):
    who = "el cliente" if by == "client" else "el profesional"
    rows = [
        ("Servicio", appointment.service.name if appointment.service else "-"),
        ("Nueva fecha", _fmt(appointment.start_time)),
        ("Hasta", _fmt(appointment.end_time)),
        ("Modificado por", who),
    ]
    if old_start:
        rows.insert(1, ("Fecha anterior", _fmt(old_start)))
    link = _manage_link(appointment)
    html = _layout("Turno reagendado", rows) + (
        f"<p style='font-family:system-ui'>Enlace de autogestión: <a href='{link}'>{link}</a></p>"
    )
    _send(appointment.client_email, "Tu turno fue reagendado", html)
    _notify_professionals(appointment, "Turno reagendado", html)


def send_reminder(appointment):
    rows = [
        ("Servicio", appointment.service.name if appointment.service else "-"),
        ("Fecha y hora", _fmt(appointment.start_time)),
    ]
    link = _manage_link(appointment)
    html = _layout("Recordatorio de turno", rows) + (
        f"<p style='font-family:system-ui'>Enlace de autogestión: <a href='{link}'>{link}</a></p>"
    )
    _send(appointment.client_email, "Recordatorio de tu turno", html)
