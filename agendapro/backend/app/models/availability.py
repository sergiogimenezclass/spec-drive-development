from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.extensions import db
from ..core.timeutil import to_iso_z
from .base import Timestamps, UUIDPrimaryKey


class WorkingHours(UUIDPrimaryKey, Timestamps, db.Model):
    """Horario de trabajo semanal regular del profesional (database.md)."""

    __tablename__ = "working_hours"
    __table_args__ = (
        UniqueConstraint("user_id", "day_of_week", name="working_hours_user_id_day_of_week_key"),
    )

    # 0 = Domingo, 1 = Lunes, ..., 6 = Sábado (database.md)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)    # "HH:MM"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="working_hours")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class BlockedSlot(UUIDPrimaryKey, Timestamps, db.Model):
    """Bloque de indisponibilidad (vacaciones, almuerzos, feriados)."""

    __tablename__ = "blocked_slots"

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="blocked_slots")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_time": to_iso_z(self.start_time),
            "end_time": to_iso_z(self.end_time),
            "reason": self.reason,
        }
