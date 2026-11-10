"""Testes automáticos do backend.

Rodar com:  python -m pytest
Nenhum teste chama a API real: usamos o modo demonstração ou um cliente falso,
então os testes são gratuitos e funcionam sem chave de API.
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import ai_client
from app.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "")


@pytest.fixture
def fake_ai(monkeypatch):
    """Simula a API de IA: guarda o que foi enviado e devolve uma resposta fixa."""
    monkeypatch.setattr(settings, "anthropic_api_key", "chave-de-teste")
    calls = []

    class FakeMessages:
        async def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Olá! Resposta da IA.")],
            )

    fake_client = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages()))
    monkeypatch.setattr(ai_client, "_get_client", lambda: fake_client)
    return calls


def test_pagina_inicial_e_servida():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Assistant" in response.text


def test_health_em_modo_demo(demo_mode):
    assert client.get("/api/health").json() == {"status": "ok", "mode": "demo"}


def test_chat_em_modo_demo_repete_a_pergunta(demo_mode):
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "demo"
    assert '"Oi"' in data["reply"]


def test_chat_com_ia_envia_historico_e_devolve_resposta(fake_ai):
    conversa = [
        {"role": "user", "content": "Meu nome é Luiz."},
        {"role": "assistant", "content": "Prazer, Luiz!"},
        {"role": "user", "content": "Qual é o meu nome?"},
    ]
    response = client.post("/api/chat", json={"messages": conversa})
    assert response.status_code == 200
    assert response.json() == {"reply": "Olá! Resposta da IA.", "mode": "ai"}
    assert fake_ai[0]["messages"] == conversa
    assert fake_ai[0]["model"] == settings.ai_model


def test_historico_que_comeca_com_assistente_e_ajustado(fake_ai):
    conversa = [
        {"role": "assistant", "content": "Mensagem antiga"},
        {"role": "user", "content": "Pergunta"},
    ]
    assert client.post("/api/chat", json={"messages": conversa}).status_code == 200
    assert fake_ai[0]["messages"] == [{"role": "user", "content": "Pergunta"}]


def test_recusa_da_ia_vira_erro_amigavel(fake_ai, monkeypatch):
    class RefusingMessages:
        async def create(self, **kwargs):
            return SimpleNamespace(stop_reason="refusal", content=[])

    fake_client = SimpleNamespace(beta=SimpleNamespace(messages=RefusingMessages()))
    monkeypatch.setattr(ai_client, "_get_client", lambda: fake_client)
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
    assert response.status_code == 422
    assert "reformulá-la" in response.json()["detail"]


def test_erro_da_ia_vira_erro_amigavel(monkeypatch):
    async def failing_reply(messages):
        raise ai_client.AIServiceError("Limite de uso da API atingido.", 429)

    monkeypatch.setattr("app.main.generate_reply", failing_reply)
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
    assert response.status_code == 429
    assert response.json()["detail"] == "Limite de uso da API atingido."


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": []},  # conversa vazia
        {"messages": [{"role": "user", "content": "   "}]},  # mensagem em branco
        {"messages": [{"role": "user", "content": "x" * 4001}]},  # mensagem longa demais
        {"messages": [{"role": "hacker", "content": "Oi"}]},  # papel inválido
    ],
)
def test_requisicoes_invalidas_sao_rejeitadas(demo_mode, payload):
    assert client.post("/api/chat", json=payload).status_code == 422


def test_ultima_mensagem_precisa_ser_do_usuario(demo_mode):
    conversa = [
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá!"},
    ]
    response = client.post("/api/chat", json={"messages": conversa})
    assert response.status_code == 422
    assert response.json()["detail"] == "A última mensagem deve ser do usuário."
