# guardrails/output_guard.py

def validate_llm_output(text: str) -> str:
    """
    Final safety net on LLM responses.
    """

    forbidden_phrases = [
        "you should take",
        "start medication",
        "increase dosage",
        "stop taking",
        "I diagnose you",
        "this confirms",
    ]

    lowered = text.lower()
    for phrase in forbidden_phrases:
        if phrase in lowered:
            return (
                "I cannot provide treatment or diagnosis. "
                "Medical evaluation by a professional is important."
            )

    return text
