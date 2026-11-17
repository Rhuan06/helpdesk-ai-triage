from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.endpoints.tickets import router as tickets_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models.ticket import Ticket  # Garante o registro da tabela na Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API inteligente para triagem e classificação de chamados de suporte técnico.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(
    tickets_router,
    prefix="/api/v1/tickets",
    tags=["Tickets"],
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Verifica se a API está operacional e retorna metadados básicos."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }