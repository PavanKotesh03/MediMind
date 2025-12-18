from llm.llm_client import call_llm
from llm.prompts import EXPLANATION_SYSTEM_PROMPT


class MedicalExplanationAgent:
    def __init__(self, retriever):
        self.retriever = retriever

    def explain(self, disease: str, history: list) -> str:
        """
        disease: rule-engine selected disease
        history: full interview history
        """
        # 🔍 RAG QUERY IS DISEASE, NOT USER TEXT
        docs = self.retriever(disease, top_k=6)
        context = self._format_context(docs)

        history_text = "\n".join(
            f"- {m['content']}"
            for m in history if m["role"] == "user"
        )

        messages = [
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"TEXTBOOK CONTEXT:\n{context}"
            },
            {
                "role": "user",
                "content": f"""
Patient history:
{history_text}

Disease identified: {disease}

Explain this condition in simple terms.
Explain why the symptoms fit this condition.
Mention warning signs briefly.
"""
            }
        ]

        return call_llm(messages, max_tokens=450)

    def explain_multiple(self, disease: str, history: list, confidence: float, severity: str) -> str:
        """
        Generate a more probabilistic explanation for multiple possibilities
        """
        # 🔍 RAG QUERY IS DISEASE, NOT USER TEXT
        docs = self.retriever(disease, top_k=6)
        context = self._format_context(docs)

        history_text = "\n".join(
            f"- {m['content']}"
            for m in history if m["role"] == "user"
        )

        # Modify the prompt to be more probabilistic but detailed
        probabilistic_prompt = f"""
You are explaining possible health conditions to a general patient. The goal is to inform, not to diagnose.

Rules:
- Use simple, non-technical language.
- Present this as ONE POSSIBLE explanation, not a definite diagnosis.
- Explain what the condition generally means.
- Explain why symptoms might fit this condition, with bullet points like in the example.
- Mention warning signs in simple words, with bullet points like in the example.
- Be reassuring and emphasize that medical consultation is needed for actual diagnosis.
- Keep the explanation focused but comprehensive.
- Use the same format as the example provided.

Example format to follow:
"Let me explain what's going on.

[DISEASE NAME] is [brief definition].

The symptoms you're experiencing, like [symptom list], fit with this condition because:

* [Symptom explanation 1]
* [Symptom explanation 2]
* [Symptom explanation 3]

[Additional relevant information about the condition]

Some warning signs to watch out for include:

* [Warning sign 1]
* [Warning sign 2]
* [Warning sign 3]

If symptoms worsen or new warning signs appear,
medical evaluation is important."

End with exactly:
"If symptoms worsen or new warning signs appear,
medical evaluation is important."
"""

        messages = [
            {"role": "system", "content": probabilistic_prompt},
            {
                "role": "system",
                "content": f"TEXTBOOK CONTEXT:\n{context}"
            },
            {
                "role": "user",
                "content": f"""
Patient history:
{history_text}

Possible condition: {disease}
Confidence level: {confidence:.0%}
Severity level: {severity}

Explain this as one possible explanation for the symptoms.
Be reassuring and emphasize this is not a diagnosis.
Follow the format shown in the example exactly.
"""
            }
        ]

        return call_llm(messages, max_tokens=450)

    def _format_context(self, docs, max_chars=3500):
        blocks, total = [], 0
        for d in docs:
            text = d["text"]
            if total + len(text) > max_chars:
                break
            blocks.append(text)
            total += len(text)
        return "\n---\n".join(blocks)


# Export the explain method as a function for backward compatibility
explanation_agent_instance = None

def explain(disease: str, history: list) -> str:
    """
    Wrapper function to provide backward compatibility.
    Creates a singleton instance of MedicalExplanationAgent if needed.
    """
    global explanation_agent_instance
    if explanation_agent_instance is None:
        # Create a dummy retriever for now - this will be replaced by the actual one
        def dummy_retriever(query, top_k=5):
            print(f"⚠️ Using dummy retriever for explanation query: {query}")
            return []
        explanation_agent_instance = MedicalExplanationAgent(dummy_retriever)
    
    return explanation_agent_instance.explain(disease, history)

def explain_multiple(disease: str, history: list, confidence: float, severity: str) -> str:
    """
    Wrapper function for multiple explanations.
    Creates a singleton instance of MedicalExplanationAgent if needed.
    """
    global explanation_agent_instance
    if explanation_agent_instance is None:
        # Create a dummy retriever for now - this will be replaced by the actual one
        def dummy_retriever(query, top_k=5):
            print(f"⚠️ Using dummy retriever for explanation query: {query}")
            return []
        explanation_agent_instance = MedicalExplanationAgent(dummy_retriever)
    
    return explanation_agent_instance.explain_multiple(disease, history, confidence, severity)