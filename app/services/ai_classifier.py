import logging

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.core.config import settings
from app.prompts.ticket_analysis import SYSTEM_INSTRUCTION, build_ticket_analysis_prompt
from app.schemas.ticket import TicketAIAnalysis

logger = logging.getLogger(__name__)

_BLOCKED_FINISH_REASONS = frozenset(
    {
        "SAFETY",
        "PROHIBITED_CONTENT",
        "BLOCKLIST",
        "SPII",
        "RECITATION",
        "MALFORMED_FUNCTION_CALL",
    }
)


class AIClassifierError(Exception):
    """Exceção base para falhas na triagem por Inteligência Artificial."""


class AIConfigurationError(AIClassifierError):
    """Configuração da API do Gemini ausente ou inválida."""


class AITimeoutError(AIClassifierError):
    """Tempo limite excedido ao aguardar resposta da API do Gemini."""


class AIProviderError(AIClassifierError):
    """Erro de comunicação, transporte, cota ou disponibilidade na API do Gemini."""


class AIInvalidResponseError(AIClassifierError):
    """Resposta ausente, bloqueada, truncada ou incompatível com o schema esperado."""


def _extract_finish_reason_name(response: types.GenerateContentResponse) -> str | None:
    """Extrai o nome normalizado do finish_reason do primeiro candidato, se disponível."""
    candidates = getattr(response, "candidates", None)
    if not candidates:
        return None

    finish_reason = getattr(candidates[0], "finish_reason", None)
    if finish_reason is None:
        return None

    raw_name = getattr(finish_reason, "name", None) or str(finish_reason)
    return raw_name.split(".")[-1].upper()


def analyze_ticket_content(title: str, description: str) -> TicketAIAnalysis:
    """Envia título e descrição para o Gemini e retorna a triagem validada."""
    api_key = settings.gemini_api_key.strip()
    if not api_key:
        logger.warning("Triagem por IA ignorada: GEMINI_API_KEY não configurada.")
        raise AIConfigurationError("Chave da API do Gemini não configurada.")

    prompt = build_ticket_analysis_prompt(title=title, description=description)
    timeout_ms = settings.gemini_timeout_seconds * 1000

    try:
        http_options = types.HttpOptions(timeout=timeout_ms)
        client = genai.Client(
            api_key=api_key,
            http_options=http_options,
        )
    except ValueError as exc:
        logger.error("Parâmetros inválidos na inicialização do cliente Gemini.")
        raise AIConfigurationError("Configuração inválida para o cliente Gemini.") from exc
    except (httpx.HTTPError, OSError) as exc:
        logger.error("Falha de transporte ao inicializar cliente Gemini: %s", type(exc).__name__)
        raise AIProviderError("Falha ao inicializar comunicação com o serviço Gemini.") from exc

    try:
        with client:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
                    response_mime_type="application/json",
                    response_schema=TicketAIAnalysis,
                ),
            )
    except (httpx.TimeoutException, TimeoutError) as exc:
        logger.error("Timeout ao consultar API do Gemini (%ss).", settings.gemini_timeout_seconds)
        raise AITimeoutError("Tempo limite excedido na comunicação com o Gemini.") from exc
    except errors.APIError as exc:
        status_code = getattr(exc, "code", None)
        logger.error("Erro retornado pela API do Gemini (status=%s).", status_code)
        if status_code in (401, 403):
            raise AIConfigurationError("Credencial da API do Gemini inválida ou sem permissão.") from exc
        if status_code in (408, 504):
            raise AITimeoutError("Timeout reportado pelo provedor Gemini.") from exc
        raise AIProviderError("Falha de comunicação com o serviço Gemini.") from exc
    except (httpx.HTTPError, OSError) as exc:
        logger.error("Erro de transporte HTTP ao consultar API do Gemini: %s", type(exc).__name__)
        raise AIProviderError("Erro de rede na comunicação com o serviço Gemini.") from exc

    candidates = getattr(response, "candidates", None)
    if not candidates:
        logger.error("API do Gemini retornou resposta sem candidatos.")
        raise AIInvalidResponseError("O modelo não retornou candidatos de resposta.")

    finish_reason_name = _extract_finish_reason_name(response)
    if finish_reason_name in _BLOCKED_FINISH_REASONS:
        logger.warning(
            "Resposta do Gemini bloqueada ou encerrada por restrição (finish_reason=%s).",
            finish_reason_name,
        )
        raise AIInvalidResponseError(
            f"A resposta da IA foi bloqueada pelo modelo ({finish_reason_name})."
        )

    if finish_reason_name == "MAX_TOKENS":
        logger.warning(
            "Resposta do Gemini descartada por atingir o limite de tokens (finish_reason=MAX_TOKENS)."
        )
        raise AIInvalidResponseError(
            "A resposta da IA foi interrompida por limite de tokens e está incompleta."
        )

    try:
        raw_text = response.text
    except ValueError as exc:
        logger.error(
            "Conteúdo textual indisponível na resposta do Gemini (finish_reason=%s).",
            finish_reason_name,
        )
        raise AIInvalidResponseError("Conteúdo textual indisponível na resposta da IA.") from exc

    if not raw_text or not raw_text.strip():
        logger.error(
            "API do Gemini retornou conteúdo textual vazio (finish_reason=%s).",
            finish_reason_name,
        )
        raise AIInvalidResponseError("O modelo retornou uma resposta vazia.")

    try:
        return TicketAIAnalysis.model_validate_json(raw_text)
    except ValidationError as exc:
        logger.error(
            "Falha na validação Pydantic da resposta do Gemini (finish_reason=%s).",
            finish_reason_name,
        )
        raise AIInvalidResponseError("A resposta da IA não atendeu ao formato esperado.") from exc