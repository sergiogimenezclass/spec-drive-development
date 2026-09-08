import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.extensions import db


class AppointmentStatus(enum.Enum):
    """Estados de un turno (sin pagos, según product.md Regla #5: borrado lógico).

    Se reconcilian database.md (BOOKED/CANCELLED/COMPLETED) y product.md CU-P04
    (marcar "no presentados") añadiendo NO_SHOW.
    """

    BOOKED = "BOOKED"        # Reservado y confirmado
    CANCELLED = "CANCELLED"  # Cancelado por cliente, profesional o sistema
    COMPLETED = "COMPLETED"  # Turno realizado
    NO_SHOW = "NO_SHOW"      # Cliente no se presentó


# Estados que SIGUEN ocupando el slot de tiempo (activos).
ACTIVE_STATUSES = {AppointmentStatus.BOOKED}


def new_uuid() -> str:
    return str(uuid.uuid4())


class UUIDPrimaryKey:
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=new_uuid
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
