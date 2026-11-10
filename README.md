# AI Assistant — Intelligent Chat

Aplicação web de chat com inteligência artificial. O usuário conversa pelo navegador, e um backend em Python (FastAPI) envia a conversa à API do Claude, da Anthropic, e devolve a resposta.

O projeto também funciona **sem chave de API**, em *modo demonstração*: o servidor responde com uma mensagem simulada, o que permite testar toda a aplicação sem custo.

## Funcionalidades

- Interface de chat responsiva, com tema claro e escuro automáticos.
- Envio por botão ou pela tecla Enter (Shift+Enter quebra a linha).
- Histórico da conversa: a IA lembra o que foi dito antes.
- Indicador de modo: "IA conectada" ou "modo demonstração".
- Mensagens de erro claras (chave inválida, limite de uso, falha de conexão etc.).
- Chave da API protegida: ela fica no arquivo `.env`, que nunca vai para o GitHub.
- Validação das mensagens no backend (tamanho, conteúdo vazio, formato).
- Testes automáticos que não gastam créditos da API.

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Backend | Python, FastAPI, Uvicorn |
| IA | API do Claude (SDK oficial `anthropic`) |
| Frontend | HTML, CSS, JavaScript (sem frameworks) |
| Testes | pytest |
| Configuração | python-dotenv |

## Arquitetura

```
Navegador (static/)          Backend FastAPI (app/)            API do Claude
┌──────────────────┐  POST  ┌──────────────────────────┐     ┌──────────────┐
│ index.html       │ /api/  │ main.py: rotas e         │     │              │
│ style.css        │ chat   │   validação              │ ──> │  Anthropic   │
│ script.js        │ ─────> │ ai_client.py: chamada    │ <── │              │
│ (guarda o        │ <───── │   à IA e erros           │     └──────────────┘
│  histórico)      │  JSON  │ config.py: lê o .env     │
└──────────────────┘        └──────────────────────────┘
```

1. O `script.js` envia o histórico da conversa para `POST /api/chat`.
2. O `main.py` valida os dados e chama `generate_reply()`.
3. O `ai_client.py` chama a API do Claude, ou responde em modo demonstração se não houver chave, e converte erros da API em mensagens amigáveis.
4. A resposta volta como JSON e aparece na tela.

A API de IA não guarda memória entre chamadas. Por isso o frontend envia o histórico inteiro a cada pergunta.

## Estrutura de pastas

```
ai-assistant/
├── app/
│   ├── __init__.py      # marca a pasta como pacote Python
│   ├── config.py        # configurações lidas do .env
│   ├── ai_client.py     # comunicação com a API de IA
│   └── main.py          # servidor FastAPI e rotas
├── static/
│   ├── index.html       # estrutura da página de chat
│   ├── style.css        # aparência
│   └── script.js        # envio de mensagens e exibição das respostas
├── tests/
│   └── test_api.py      # testes automáticos do backend
├── .env.example         # modelo do arquivo de configuração
├── .gitignore           # arquivos que não vão para o GitHub
├── pytest.ini           # configuração dos testes
├── requirements.txt     # bibliotecas do projeto
└── README.md
```

## Como rodar

Pré-requisitos: Windows com Python 3.10 ou mais recente e Git. Os comandos abaixo são para o PowerShell, executados na pasta do projeto.

**1. Criar e ativar o ambiente virtual**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação por causa da política de execução, rode uma vez `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

**2. Instalar as dependências**

```powershell
pip install -r requirements.txt
```

**3. Configurar (opcional)**

```powershell
copy .env.example .env
```

Abra o `.env` e preencha `ANTHROPIC_API_KEY` com sua chave, criada em [console.anthropic.com](https://console.anthropic.com). Se você deixar o campo vazio, o app roda em modo demonstração.

**4. Iniciar o servidor**

```powershell
uvicorn app.main:app --reload
```

Abra **http://localhost:8000** no navegador. O `--reload` reinicia o servidor sozinho sempre que você salva um arquivo. Para parar o servidor, pressione `Ctrl + C`.

## Configurações (`.env`)

| Variável | Padrão | Para que serve |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | vazio | Chave da API. Vazio = modo demonstração. |
| `AI_MODEL` | `claude-opus-5-5` | Modelo de IA usado. |
| `AI_EFFORT` | `low` | Esforço de raciocínio (`low`, `medium`, `high`, `xhigh`, `max`). Mais esforço gera respostas mais elaboradas, porém mais lentas e caras. |
| `AI_MAX_TOKENS` | `16000` | Tamanho máximo da resposta. |

A chamada à API usa o recurso de *fallback* do servidor: se o modelo principal recusar uma pergunta, a própria API tenta responder com outro modelo.

## Testes

```powershell
python -m pytest
```

Resultado esperado: `12 passed`. Os testes usam o modo demonstração ou um cliente de IA simulado, então não precisam de chave e não geram custo.

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/api/health` | Retorna `{"status": "ok", "mode": "ai" \| "demo"}`. |
| `POST` | `/api/chat` | Recebe `{"messages": [{"role": "user", "content": "..."}]}` e retorna `{"reply": "...", "mode": "..."}`. |

A documentação interativa gerada pelo FastAPI fica em **http://localhost:8000/docs**.

## Segurança

- A chave da API fica só no `.env`, que está no `.gitignore`. Nunca coloque a chave no código.
- A chave é usada apenas no backend. O navegador nunca a recebe.
- O frontend exibe as mensagens com `textContent`, o que impede que um texto seja interpretado como HTML ou script.

## Próximos passos

- Mostrar a resposta aos poucos, enquanto é gerada (streaming).
- Formatar Markdown nas respostas (listas, código, negrito).
- Salvar o histórico das conversas.
- Publicar o projeto online.

## Autor

**Luiz Eduardo**, estudante de Análise e Desenvolvimento de Sistemas.
GitHub: [LuizEduardo-Du](https://github.com/LuizEduardo-Du)
