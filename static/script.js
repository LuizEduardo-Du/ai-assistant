// Lógica da interface de chat: envia mensagens ao backend e mostra as respostas.

const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const messagesBox = document.getElementById("messages");
const errorBox = document.getElementById("error");
const modeBadge = document.getElementById("mode-badge");

// Histórico da conversa. A API de IA não tem memória, então enviamos
// todas as mensagens anteriores junto com cada pergunta nova.
const history = [];
// O backend aceita até 50 mensagens. Usamos 49 (número ímpar) para que o
// trecho enviado sempre comece com uma mensagem do usuário, como a API exige.
const MAX_HISTORY = 49;

// Adiciona um balão de mensagem na tela.
// Usamos textContent (e não innerHTML) para que nenhum texto vire código HTML.
function addMessage(role, text, extraClass = "") {
  const bubble = document.createElement("div");
  bubble.className = `message ${role} ${extraClass}`.trim();
  bubble.textContent = text;
  messagesBox.appendChild(bubble);
  messagesBox.scrollTop = messagesBox.scrollHeight;
  return bubble;
}

function showError(text) {
  errorBox.textContent = text;
  errorBox.hidden = false;
}

function hideError() {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  input.disabled = isLoading;
  sendButton.textContent = isLoading ? "Enviando..." : "Enviar";
}

// Mostra no topo se o servidor está usando a IA real ou o modo demonstração.
async function checkMode() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    modeBadge.textContent = data.mode === "ai" ? "IA conectada" : "modo demonstração";
    modeBadge.className = `badge ${data.mode}`;
  } catch {
    modeBadge.textContent = "servidor offline";
  }
}

async function sendMessage(text) {
  hideError();
  addMessage("user", text);
  history.push({ role: "user", content: text });

  const loadingBubble = addMessage("assistant", "Pensando...", "loading");
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history.slice(-MAX_HISTORY) }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      // O backend devolve a explicação do erro no campo "detail".
      const detail = typeof data.detail === "string" ? data.detail : "Mensagem inválida.";
      throw new Error(detail);
    }

    loadingBubble.remove();
    addMessage("assistant", data.reply);
    history.push({ role: "assistant", content: data.reply });
  } catch (error) {
    loadingBubble.remove();
    // Tira a pergunta que falhou do histórico, para o usuário poder tentar de novo.
    history.pop();
    const message =
      error instanceof TypeError
        ? "Não foi possível falar com o servidor. Ele está rodando?"
        : error.message;
    showError(message);
  } finally {
    setLoading(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault(); // impede o navegador de recarregar a página
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  input.style.height = "auto";
  sendMessage(text);
});

// Enter envia; Shift+Enter quebra a linha.
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

// A caixa de texto cresce conforme o usuário digita.
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
});

checkMode();
input.focus();
