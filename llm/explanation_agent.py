# llm/explanation_agent.py

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

    def _format_context(self, docs, max_chars=3500):
        blocks, total = [], 0
        for d in docs:
            text = d["text"]
            if total + len(text) > max_chars:
                break
            blocks.append(text)
            total += len(text)
        return "\n---\n".join(blocks)
