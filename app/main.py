"""Servidor web do AI Assistant (FastAPI).

Rotas:
- GET  /api/health -> informa se o servidor está no ar e em qual modo.
- POST /api/chat   -> recebe a conversa e devolve a resposta da IA.
- GET  /           -> entrega a interface de chat (pasta static/).
"""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.ai_client import AIServiceError, generate_reply
from app.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="AI Assistant", description="Chat web com inteligência artificial.")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("a mensagem não pode estar vazia")
        return value


class ChatRequest(BaseModel):
    # Histórico da conversa; a última mensagem é a pergunta atual.
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)


class ChatResponse(BaseModel):
    reply: str
    mode: Literal["ai", "demo"]


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "mode": "demo" if settings.demo_mode else "ai"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="A última mensagem deve ser do usuário.")

    history = [message.model_dump() for message in request.messages]
    # A API de IA exige que a conversa comece com uma mensagem do usuário.
    while history[0]["role"] != "user":
        history.pop(0)
    try:
        reply, mode = await generate_reply(history)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    return ChatResponse(reply=reply, mode=mode)


# Montado por último, para não "esconder" as rotas /api acima.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
