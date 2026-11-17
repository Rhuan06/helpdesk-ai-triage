from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import ticket as _ticket_model  # noqa: F401
from app.models.ticket import TicketCategory, TicketPriority
from app.schemas.ticket import TicketAIAnalysis


@pytest.fixture
def default_ai_analysis() -> TicketAIAnalysis:
    """Retorna uma análise de IA válida e determinística para os testes."""
    return TicketAIAnalysis(
        suggested_category=TicketCategory.NETWORK,
        suggested_priority=TicketPriority.HIGH,
        technical_summary="Indisponibilidade de conectividade de rede reportada pelo usuário.",
        possible_causes=[
            "Falha na interface de rede ou cabo desconectado",
            "Problema de resolução DNS ou gateway inacessível",
        ],
        suggested_resolution=[
            "Verificar status da conexão e endereço IP atribuído",
            "Testar conectividade com o gateway padrão e servidor DNS",
        ],
    )


@pytest.fixture
def mock_ai_classifier(
    default_ai_analysis: TicketAIAnalysis,
) -> Generator[MagicMock, None, None]:
    """Substitui analyze_ticket_content no serviço de chamados para evitar chamadas reais à API."""
    with patch(
        "app.services.ticket_service.analyze_ticket_content",
        return_value=default_ai_analysis,
    ) as mock_fn:
        yield mock_fn


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Cria um banco SQLite em memória isolado por teste com StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(
    db_session: Session,
    mock_ai_classifier: MagicMock,
) -> Generator[TestClient, None, None]:
    """Fornece um TestClient com banco em memória e triagem de IA mockada por padrão."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)