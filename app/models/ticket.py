from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TicketCategory(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    OPERATING_SYSTEMS = "operating_systems"
    PRINTERS_AND_PERIPHERALS = "printers_and_peripherals"
    ACCESS_AND_AUTHENTICATION = "access_and_authentication"
    OTHER = "other"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_ANALYSIS = "in_analysis"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    # Dados oficiais do chamado
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requester_name: Mapped[str] = mapped_column(String(100), nullable=False)

    category: Mapped[TicketCategory] = mapped_column(
        SQLEnum(TicketCategory, native_enum=False),
        default=TicketCategory.OTHER,
        nullable=False,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SQLEnum(TicketPriority, native_enum=False),
        default=TicketPriority.MEDIUM,
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, native_enum=False),
        default=TicketStatus.OPEN,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Sugestões opcionais produzidas pela IA
    ai_suggested_category: Mapped[TicketCategory | None] = mapped_column(
        SQLEnum(TicketCategory, native_enum=False),
        nullable=True,
    )
    ai_suggested_priority: Mapped[TicketPriority | None] = mapped_column(
        SQLEnum(TicketPriority, native_enum=False),
        nullable=True,
    )
    ai_technical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_possible_causes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_suggested_resolution: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)