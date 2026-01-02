import requests
import logging

logger = logging.getLogger(__name__)

# Use only llama3.1:8b
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"


def call_llm(messages, max_tokens=300, temperature=0.2):
    """
    Call Ollama LLM using /api/chat endpoint with llama3.1:8b
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens to generate (increased to 450 for detailed explanations)
        temperature: Sampling temperature (0.0 - 1.0)
    
    Returns:
        Dict with 'message' containing 'content' key
    """
    try:
        # Prepare payload for Ollama chat API
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        logger.info(f"Calling Ollama with model: {MODEL_NAME}, messages: {len(messages)}")
        
        # Call Ollama with increased timeout (3 minutes for explanation generation)
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        
        result = resp.json()
        
        # Extract response from Ollama format
        if "message" in result:
            response_text = result["message"].get("content", "")
        else:
            logger.warning(f"Unexpected Ollama response format: {result}")
            response_text = str(result)
        
        logger.info(f"LLM response received: {len(response_text)} chars")
        
        # Return in expected format
        return {
            "message": {
                "content": response_text.strip()
            }
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"LLM request timed out after 180s with model {MODEL_NAME}")
        raise Exception("LLM request timed out - model may be too slow")
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Ollama HTTP error: {e.response.status_code}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM request failed: {e}")
        raise Exception(f"Failed to connect to Ollama: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error calling LLM: {e}", exc_info=True)
        raise Exception(f"LLM error: {e}")


def call_llm_streaming(messages, max_tokens=150, temperature=0.2):
    """
    Call Ollama LLM with streaming support (for future use)
    
    Yields response chunks as they arrive
    """
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        logger.info(f"Starting streaming call to Ollama with model: {MODEL_NAME}")
        
        resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=180)
        resp.raise_for_status()
        
        import json
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    if content:
                        yield content
        
        logger.info("Streaming response completed")
        
    except Exception as e:
        logger.error(f"Streaming LLM error: {e}", exc_info=True)
        raise
