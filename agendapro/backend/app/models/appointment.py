import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.extensions import db
from ..core.timeutil import to_iso_z
from .base import AppointmentStatus, Timestamps, UUIDPrimaryKey


class Appointment(UUIDPrimaryKey, Timestamps, db.Model):
    """Turno/reserva realizada por un cliente (database.md + api.md)."""

    __tablename__ = "appointments"
    __table_args__ = (
        Index("appointments_user_id_start_time_idx", "user_id", "start_time"),
        Index("appointments_client_email_idx", "client_email"),
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status", native_enum=True),
        nullable=False,
        default=AppointmentStatus.BOOKED,
    )
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Token único para autogestión del cliente (cancelar/reagendar por enlace).
    booking_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(24)
    )

    service_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    service: Mapped["Service"] = relationship(back_populates="appointments")
    user: Mapped["User"] = relationship(back_populates="appointments")

    def to_dict(self, include_token: bool = False) -> dict:
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "start_time": to_iso_z(self.start_time),
            "end_time": to_iso_z(self.end_time),
            "client_name": self.client_name,
            "client_email": self.client_email,
            "client_phone": self.client_phone,
            "status": self.status.value,
            "notes": self.notes,
        }
        if include_token:
            data["booking_token"] = self.booking_token
        return data
