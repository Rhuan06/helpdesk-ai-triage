from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ticket import TicketCategory, TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10, max_length=5000)
    requester_name: str = Field(..., min_length=2, max_length=100)
    category: TicketCategory = TicketCategory.OTHER
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("title", "description", "requester_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    requester_name: str | None = Field(default=None, min_length=2, max_length=100)
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None

    @field_validator("title", "description", "requester_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    requester_name: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    ai_suggested_category: TicketCategory | None
    ai_suggested_priority: TicketPriority | None
    ai_technical_summary: str | None
    ai_possible_causes: list[str] | None
    ai_suggested_resolution: list[str] | None
    created_at: datetime
    updated_at: datetime


class TicketAIAnalysis(BaseModel):
    suggested_category: TicketCategory = Field(
        ...,
        description="Categoria técnica mais adequada ao incidente relatado.",
    )
    suggested_priority: TicketPriority = Field(
        ...,
        description="Nível de prioridade sugerido com base no impacto e urgência.",
    )
    technical_summary: str = Field(
        ...,
        min_length=10,
        description="Resumo técnico objetivo do incidente em português.",
    )
    possible_causes: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Lista de 2 a 4 possíveis causas técnicas para o problema.",
    )
    suggested_resolution: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Passo a passo prático sugerido para diagnóstico e resolução.",
    )