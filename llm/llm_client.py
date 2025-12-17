# llm/llm_client.py

import os
import requests

LLAMA_API_URL = os.getenv(
    "LLAMA_API_URL",
    "http://localhost:11434/v1/chat/completions"
)
LLAMA_MODEL = os.getenv(
    "LLAMA_MODEL_NAME",
    "llama3.1:8b"
)

def call_llm(messages, temperature=0.2, max_tokens=256):
    payload = {
        "model": LLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = requests.post(
        LLAMA_API_URL,
        json=payload,
        timeout=120
    )
    resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"].strip()
