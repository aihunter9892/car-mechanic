const chatEl = document.getElementById("chat");
const formEl = document.getElementById("form");
const inputEl = document.getElementById("input");

const temperatureEl = document.getElementById("temperature");
const topPEl = document.getElementById("top_p");
const temperatureValEl = document.getElementById("temperatureVal");
const topPValEl = document.getElementById("topPVal");

const clearBtn = document.getElementById("clearBtn");

// History stored in browser memory (array of {role, content})
let history = [];

function addMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setSlidersText(){
  temperatureValEl.textContent = Number(temperatureEl.value).toFixed(2);
  topPValEl.textContent = Number(topPEl.value).toFixed(2);
}
temperatureEl.addEventListener("input", setSlidersText);
topPEl.addEventListener("input", setSlidersText);
setSlidersText();

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = inputEl.value.trim();
  if (!text) return;

  // Add user message to UI and local history
  addMessage("user", text);
  history.push({ role: "user", content: text });

  inputEl.value = "";
  inputEl.focus();

  // Show temporary bot message
  addMessage("bot", "Thinking…");
  const thinkingNode = chatEl.lastElementChild;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        message: text,
        history: history, // Send full history to backend each time
        temperature: Number(temperatureEl.value),
        top_p: Number(topPEl.value),
      })
    });

    const data = await res.json();
    thinkingNode.remove();

    if (!res.ok) {
      addMessage("bot", data.error || "Something went wrong.");
      return;
    }

    // Add assistant response to UI and local history
    addMessage("bot", data.reply);
    history.push({ role: "assistant", content: data.reply });

    // Prevent runaway history growth: keep last ~12 messages
    if (history.length > 12) history = history.slice(-12);

  } catch (err) {
    thinkingNode.remove();
    addMessage("bot", "Network error. Check backend console.");
  }
});

clearBtn.addEventListener("click", () => {
  // Clear only the UI + local history (backend is stateless anyway)
  chatEl.innerHTML = "";
  history = [];
  addMessage("bot", "Chat cleared. Describe your car issue and include make/model/year if possible.");
});