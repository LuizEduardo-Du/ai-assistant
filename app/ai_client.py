"""Comunicação com a API de inteligência artificial (Claude, da Anthropic).

Este é o único arquivo que conhece a API de IA. O resto da aplicação só chama
generate_reply(). Assim, trocar de provedor no futuro exige mudar só este arquivo.
"""

import anthropic

from app.config import settings

SYSTEM_PROMPT = (
    "Você é o AI Assistant, um assistente virtual prestativo. "
    "Responda sempre em português do Brasil, de forma clara, educada e objetiva."
)

_client: anthropic.AsyncAnthropic | None = None


class AIServiceError(Exception):
    """Erro amigável, com a mensagem e o código HTTP que o frontend vai receber."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_client() -> anthropic.AsyncAnthropic:
    """Cria o cliente da API uma única vez e o reutiliza nas próximas chamadas."""
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _demo_reply(messages: list[dict]) -> str:
    """Resposta simulada, usada quando não há chave de API configurada."""
    last_question = messages[-1]["content"]
    return (
        f'[Modo demonstração] Você disse: "{last_question}". '
        "Para receber respostas reais da IA, configure a variável "
        "ANTHROPIC_API_KEY no arquivo .env (veja o README)."
    )


async def generate_reply(messages: list[dict]) -> tuple[str, str]:
    """Recebe o histórico da conversa e devolve (resposta, modo).

    O modo é "demo" (resposta simulada) ou "ai" (resposta real da IA).
    A API é "sem memória": por isso enviamos o histórico inteiro a cada pergunta.
    """
    if settings.demo_mode:
        return _demo_reply(messages), "demo"

    try:
        response = await _get_client().beta.messages.create(
            model=settings.ai_model,
            max_tokens=settings.max_tokens,
            system=SYSTEM_PROMPT,
            messages=messages,
            output_config={"effort": settings.ai_effort},
            # Se o modelo principal recusar a pergunta, a própria API tenta
            # outro modelo automaticamente ("fallback").
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        raise AIServiceError(
            "A chave da API é inválida. Confira o ANTHROPIC_API_KEY no arquivo .env.", 401
        )
    except anthropic.PermissionDeniedError:
        raise AIServiceError("A chave da API não tem permissão para usar este modelo.", 403)
    except anthropic.NotFoundError:
        raise AIServiceError(
            f"O modelo '{settings.ai_model}' não foi encontrado. Confira o AI_MODEL no .env.", 502
        )
    except anthropic.RateLimitError:
        raise AIServiceError(
            "Limite de uso da API atingido. Aguarde um pouco ou confira seus créditos.", 429
        )
    except anthropic.BadRequestError as error:
        raise AIServiceError(f"A API recusou a requisição: {error.message}", 400)
    except anthropic.APIStatusError as error:
        raise AIServiceError(
            f"O serviço de IA está com problemas (erro {error.status_code}). Tente de novo.", 502
        )
    except anthropic.APIConnectionError:
        raise AIServiceError(
            "Não foi possível conectar à API de IA. Verifique sua internet.", 503
        )

    if response.stop_reason == "refusal":
        raise AIServiceError("A IA não pôde responder a essa pergunta. Tente reformulá-la.", 422)

    reply = "".join(block.text for block in response.content if block.type == "text").strip()
    if not reply:
        raise AIServiceError("A IA não retornou texto. Tente perguntar de novo.", 502)
    return reply, "ai"
