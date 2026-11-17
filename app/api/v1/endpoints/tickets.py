from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services import ticket_service
from app.services.ai_classifier import (
    AIClassifierError,
    AIConfigurationError,
    AITimeoutError,
)
from app.services.ticket_service import BusinessRuleError

router = APIRouter()


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar chamado com triagem inteligente",
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Cria um chamado e executa triagem automática pelo Gemini de forma não bloqueante."""
    ticket = ticket_service.create_ticket(db=db, ticket_data=ticket_in)
    return TicketResponse.model_validate(ticket)


@router.post(
    "/{ticket_id}/analyze",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocessar triagem de IA do chamado",
)
def analyze_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Executa sob demanda uma nova análise de IA para um chamado ativo."""
    ticket = ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chamado com ID {ticket_id} não encontrado.",
        )

    try:
        analyzed_ticket = ticket_service.reanalyze_ticket(db=db, ticket=ticket)
    except BusinessRuleError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AIConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AITimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except AIClassifierError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return TicketResponse.model_validate(analyzed_ticket)


@router.get(
    "",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar chamados",
)
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    priority: TicketPriority | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    """Retorna a lista de chamados cadastrados com suporte a filtros e paginação."""
    tickets = ticket_service.list_tickets(
        db=db,
        status=status_filter,
        category=category,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar chamado por ID",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Busca os detalhes de um chamado específico pelo seu identificador."""
    ticket = ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chamado com ID {ticket_id} não encontrado.",
        )
    return TicketResponse.model_validate(ticket)


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar chamado parcialmente",
)
def update_ticket(
    ticket_id: int,
    ticket_in: TicketUpdate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Atualiza apenas os campos informados respeitando regras de negócio e transições de status."""
    ticket = ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chamado com ID {ticket_id} não encontrado.",
        )

    try:
        updated_ticket = ticket_service.update_ticket(
            db=db,
            ticket=ticket,
            ticket_data=ticket_in,
        )
    except BusinessRuleError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return TicketResponse.model_validate(updated_ticket)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir chamado",
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Exclui um chamado existente e retorna 204 No Content sem corpo."""
    ticket = ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chamado com ID {ticket_id} não encontrado.",
        )

    ticket_service.delete_ticket(db=db, ticket=ticket)
    return Response(status_code=status.HTTP_204_NO_CONTENT)