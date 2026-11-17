from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services import ticket_service

router = APIRouter()


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar chamado",
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Cria um novo chamado técnico sem executar triagem de IA."""
    ticket = ticket_service.create_ticket(db=db, ticket_data=ticket_in)
    return TicketResponse.model_validate(ticket)


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
    """Atualiza apenas os campos informados no corpo da requisição."""
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
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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