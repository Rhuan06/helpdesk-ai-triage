from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API inteligente para triagem e classificação de chamados de suporte técnico.",
    docs_url="/docs",
    redoc_url="/redoc",
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