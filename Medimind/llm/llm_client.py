# llm/llm_client.py

import os
import requests
import json

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL_NAME",
    "llama3.1:8b"
)

def call_llm(messages, temperature=0.2, max_tokens=256):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": True   # 🔥 Ollama streams by default
    }

    resp = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=300
    )
    resp.raise_for_status()

    final_text = []

    for line in resp.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "message" in data and "content" in data["message"]:
            final_text.append(data["message"]["content"])

        if data.get("done"):
            break

    return "".join(final_text).strip()
