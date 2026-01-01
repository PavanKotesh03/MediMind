# llm/llm_client.py

import os
import requests
import json

import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL_NAME",
    "llama3.1:8b"
)

def call_llm(messages, temperature=0.2, max_tokens=256):
    logger.debug(f"Calling LLM with {len(messages)} messages, max_tokens={max_tokens}")
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": True   #  Ollama streams by default
    }

    try:
        resp = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=300
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"LLM request failed: {e}")
        raise

    final_text = []

    for line in resp.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "message" in data and "content" in data["message"]:
            final_text.append(data["message"]["content"])

        if data.get("done"):
            break

    result = "".join(final_text).strip()
    logger.debug(f"LLM response received, length: {len(result)}")
    return result
