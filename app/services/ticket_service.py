from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate


def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
    """Cria e persiste um novo chamado no banco de dados."""
    ticket = Ticket(**ticket_data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_tickets(
    db: Session,
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Ticket]:
    """Lista chamados aplicando filtros opcionais e paginação."""
    stmt = select(Ticket).order_by(Ticket.created_at.desc())

    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    if category is not None:
        stmt = stmt.where(Ticket.category == category)
    if priority is not None:
        stmt = stmt.where(Ticket.priority == priority)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_ticket_by_id(db: Session, ticket_id: int) -> Ticket | None:
    """Busca um chamado específico pelo seu ID."""
    stmt = select(Ticket).where(Ticket.id == ticket_id)
    return db.scalars(stmt).first()


def update_ticket(
    db: Session,
    ticket: Ticket,
    ticket_data: TicketUpdate,
) -> Ticket:
    """Atualiza parcialmente um chamado apenas com os campos enviados na requisição."""
    update_fields = ticket_data.model_dump(exclude_unset=True)
    allowed_fields = TicketUpdate.model_fields.keys()

    for field, value in update_fields.items():
        if field not in allowed_fields:
            continue
        if value is None:
            raise ValueError(f"O campo '{field}' não pode ser definido como nulo.")
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket(db: Session, ticket: Ticket) -> None:
    """Remove um chamado do banco de dados."""
    db.delete(ticket)
    db.commit()