import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from app.schemas.ticket import TicketAIAnalysis, TicketCreate, TicketUpdate
from app.services.ai_classifier import AIClassifierError, analyze_ticket_content

logger = logging.getLogger(__name__)

ALLOWED_STATUS_TRANSITIONS: dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.OPEN: frozenset(
        {
            TicketStatus.IN_ANALYSIS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
        }
    ),
    TicketStatus.IN_ANALYSIS: frozenset(
        {
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
        }
    ),
    TicketStatus.IN_PROGRESS: frozenset(
        {
            TicketStatus.IN_ANALYSIS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
        }
    ),
    TicketStatus.RESOLVED: frozenset(
        {
            TicketStatus.IN_PROGRESS,
            TicketStatus.CLOSED,
        }
    ),
    TicketStatus.CLOSED: frozenset(),
}


class BusinessRuleError(Exception):
    """Violação de regra de negócio ou transição inválida de estado do chamado."""


def _ensure_ticket_is_editable(ticket: Ticket) -> None:
    """Impede alterações ou reprocessamentos em chamados já encerrados."""
    if ticket.status == TicketStatus.CLOSED:
        raise BusinessRuleError(
            f"O chamado #{ticket.id} está encerrado (closed) e não permite alterações ou reanálise."
        )


def _validate_status_transition(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    """Valida se a transição de status respeita a máquina de estados do domínio."""
    if new_status == current_status:
        return

    allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(current_status, frozenset())
    if new_status not in allowed_targets:
        allowed_labels = ", ".join(sorted(status.value for status in allowed_targets)) or "nenhuma"
        raise BusinessRuleError(
            f"Transição de status inválida: '{current_status.value}' -> '{new_status.value}'. "
            f"Transições permitidas a partir de '{current_status.value}': {allowed_labels}."
        )


def _apply_ai_analysis(ticket: Ticket, analysis: TicketAIAnalysis) -> None:
    """Atribui exclusivamente os campos de sugestão da IA ao modelo ORM."""
    ticket.ai_suggested_category = analysis.suggested_category
    ticket.ai_suggested_priority = analysis.suggested_priority
    ticket.ai_technical_summary = analysis.technical_summary
    ticket.ai_possible_causes = analysis.possible_causes
    ticket.ai_suggested_resolution = analysis.suggested_resolution


def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
    """Persiste o chamado primeiro e executa triagem por IA de forma não bloqueante."""
    ticket = Ticket(**ticket_data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    try:
        analysis = analyze_ticket_content(
            title=ticket.title,
            description=ticket.description,
        )
    except AIClassifierError as exc:
        logger.warning(
            "Chamado #%s criado sem triagem de IA (%s).",
            ticket.id,
            type(exc).__name__,
        )
        return ticket

    try:
        _apply_ai_analysis(ticket, analysis)
        db.commit()
        db.refresh(ticket)
    except SQLAlchemyError:
        db.rollback()
        logger.error(
            "Falha ao persistir resultados da IA no chamado #%s; chamado mantido sem análise.",
            ticket.id,
        )
        db.refresh(ticket)

    return ticket


def reanalyze_ticket(db: Session, ticket: Ticket) -> Ticket:
    """Reprocessa a triagem de IA de um chamado ativo preservando dados anteriores em caso de erro."""
    _ensure_ticket_is_editable(ticket)

    analysis = analyze_ticket_content(
        title=ticket.title,
        description=ticket.description,
    )
    _apply_ai_analysis(ticket, analysis)
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
    """Atualiza parcialmente um chamado validando regras de negócio e transições de status."""
    _ensure_ticket_is_editable(ticket)

    update_fields = ticket_data.model_dump(exclude_unset=True)
    allowed_fields = TicketUpdate.model_fields.keys()

    for field, value in update_fields.items():
        if field not in allowed_fields:
            continue
        if value is None:
            raise ValueError(f"O campo '{field}' não pode ser definido como nulo.")

    if "status" in update_fields:
        _validate_status_transition(ticket.status, update_fields["status"])

    for field, value in update_fields.items():
        if field not in allowed_fields:
            continue
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket(db: Session, ticket: Ticket) -> None:
    """Remove um chamado do banco de dados."""
    db.delete(ticket)
    db.commit()