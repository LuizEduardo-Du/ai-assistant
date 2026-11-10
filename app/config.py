"""Configurações da aplicação, lidas de variáveis de ambiente.

Os valores vêm do arquivo .env (que nunca vai para o GitHub) ou das
variáveis de ambiente do sistema. Nenhuma chave fica escrita no código.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Lê o arquivo .env da pasta do projeto, se ele existir.
load_dotenv()


@dataclass
class Settings:
    # Chave da API da Anthropic. Vazia = o app roda em "modo demonstração".
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    # Modelo de IA usado nas respostas.
    ai_model: str = os.getenv("AI_MODEL", "claude-opus-5-5").strip()
    # Esforço de raciocínio do modelo: low, medium, high, xhigh ou max.
    # "low" é suficiente para conversa e gasta menos.
    ai_effort: str = os.getenv("AI_EFFORT", "low").strip()
    # Limite de tokens da resposta.
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "16000"))

    @property
    def demo_mode(self) -> bool:
        return not self.anthropic_api_key


settings = Settings()
