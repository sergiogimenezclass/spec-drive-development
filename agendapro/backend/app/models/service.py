from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.extensions import db
from .base import Timestamps, UUIDPrimaryKey

if TYPE_CHECKING:
    from .appointment import Appointment


class Service(UUIDPrimaryKey, Timestamps, db.Model):
    """Servicio ofrecido por el profesional (database.md)."""

    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="services_user_id_name_key"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="services")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="service")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
        }
