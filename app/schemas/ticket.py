from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketCategory, TicketPriority, TicketStatus

class TicketCreate(BaseModel):
    title: str = Field(..., min_lenght=3, max_lenght=150)
    description: str = Field(..., min_lenght=10)
    requester_name: str = Field(..., min_lenght=2, max_lenght=100)
    category: TicketCategory = TicketCategory.OTHER
    priority: TicketPriority = TicketPriority.MEDIUM

class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10)
    requester_name: str | None = Field(default=None, min_length=2, max_length=100)
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None

class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    requester_name: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime

    ai_suggested_category: TicketCategory | None = None
    ai_suggested_priority: TicketPriority | None = None
    ai_technical_summary: str | None = None
    ai_possible_causes: list[str] | None = None
    ai_suggested_resolution: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)

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
        min_length=2,
        max_length=4,
        description="Lista de 2 a 4 possíveis causas técnicas para o problema.",
    )
    suggested_resolution: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Passo a passo prático sugerido para diagnóstico e resolução.",
    )
