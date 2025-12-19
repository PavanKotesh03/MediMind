# guardrails/scope_guard.py

def ensure_medical_scope(text: str):
    non_medical_triggers = [
        "write code",
        "hack",
        "politics",
        "relationship advice",
        "legal advice",
        "investment",
        "crypto"
    ]

    lowered = text.lower()
    if any(t in lowered for t in non_medical_triggers):
        raise ValueError(
            "This assistant is restricted to medical symptom discussions only."
        )
