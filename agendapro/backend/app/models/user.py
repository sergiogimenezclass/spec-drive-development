from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.extensions import db
from .base import Timestamps, UUIDPrimaryKey


class User(UUIDPrimaryKey, Timestamps, db.Model):
    """Profesional (proveedor de servicio). Aplicación mono-usuario."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Reglas de negocio configurables por el profesional (product.md Reglas #3 y #4 +
    # cancel_policy_config.md). cutoff 0 = el cliente puede cancelar hasta el inicio.
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    min_advance_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    cancellation_cutoff_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Seguridad: bloqueo por intentos fallidos (professional-auth.md §3.2).
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    services: Mapped[List["Service"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    working_hours: Mapped[List["WorkingHours"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    blocked_slots: Mapped[List["BlockedSlot"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.contact_phone,
            "timezone": self.timezone,
            "min_advance_minutes": self.min_advance_minutes,
            "cancellation_cutoff_hours": self.cancellation_cutoff_hours,
        }
