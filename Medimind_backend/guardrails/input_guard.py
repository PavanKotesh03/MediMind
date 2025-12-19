# guardrails/input_guard.py

import re
from guardrails.injection_patterns import INJECTION_PATTERNS
from guardrails.guard_exceptions import PromptInjectionError


def sanitize_user_input(text: str) -> str:
    """
    Cleans and validates user input before sending to LLM.
    """

    lowered = text.lower()

    # 🚫 Prompt injection detection
    for pattern in INJECTION_PATTERNS:
        if pattern in lowered:
            raise PromptInjectionError(
                "Unsafe instruction detected in input"
            )

    # 🔒 Remove role tags explicitly
    text = re.sub(r"<\s*/?\s*(system|assistant|user)\s*>", "", text)

    # 🔒 Remove markdown code blocks (often used for jailbreaks)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # 🔒 Collapse excessive whitespace
    text = re.sub(r"\s{3,}", " ", text).strip()

    return text
