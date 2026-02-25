import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env (optional but convenient)
load_dotenv()

app = Flask(__name__)

# Read Groq API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY. Put it in your .env or environment variables.")

# Create Groq client once at startup
groq_client = Groq(api_key=GROQ_API_KEY)

# Use the model you specified
GROQ_MODEL = "llama-3.3-70b-versatile"

# System prompt for the mechanic persona (sent on every request)
SYSTEM_PROMPT = """
You are "Torque", an expert car mechanic and diagnostic assistant.

Your job:
- Ask clarifying questions first when information is missing.
- Diagnose likely causes based on symptoms, vehicle context, and constraints.
- Provide a step-by-step checklist: simplest checks first, then advanced.
- Provide safety warnings when relevant (brakes, fuel smell, overheating, electrical issues).
- Give cost/risk estimates in rough tiers (low/medium/high) instead of exact prices.
- Keep answers practical and non-jargony. Use bullet points and short sections.

Boundaries:
- Do NOT encourage unsafe DIY for critical systems (brakes, airbags, steering).
- If the user reports dangerous symptoms, recommend professional inspection immediately.
- If uncertain, say what you’re uncertain about and what info would confirm it.

Output format (always):
1) Quick Summary (1–2 lines)
2) Most Likely Causes (bullets)
3) Quick Checks I Can Do Now (bullets)
4) If That Doesn’t Fix It (bullets)
5) Safety Note (1–2 lines)
""".strip()


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    """
    Expects JSON:
    {
      "message": "user text",
      "history": [{"role":"user|assistant","content":"..."} ...],   # optional
      "temperature": 0.3,  # optional
      "top_p": 0.9         # optional
    }

    Returns:
    { "reply": "assistant text" }
    """
    data = request.get_json(silent=True) or {}

    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # History comes from the browser; keep it short to avoid huge prompts
    history = data.get("history") or []
    if not isinstance(history, list):
        return jsonify({"error": "history must be a list of messages."}), 400

    # Only allow user/assistant roles from client history (system is controlled server-side)
    safe_history = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            safe_history.append({"role": role, "content": content.strip()})

    # Optional: cap history to last 12 messages (~6 turns)
    safe_history = safe_history[-12:]

    # Generation params
    try:
        temperature = float(data.get("temperature", 0.3))
        top_p = float(data.get("top_p", 0.9))
    except ValueError:
        return jsonify({"error": "temperature/top_p must be numbers."}), 400

    temperature = max(0.0, min(1.5, temperature))
    top_p = max(0.1, min(1.0, top_p))

    # Build Groq messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(safe_history)
    messages.append({"role": "user", "content": user_message})

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
        )
        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": f"Groq call failed: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))  # App Runner sets PORT
    app.run(host="0.0.0.0", port=port, debug=False)