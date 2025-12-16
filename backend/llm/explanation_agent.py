from llm.llm_client import call_llm
from llm.prompts import EXPLANATION_SYSTEM_PROMPT

class MedicalExplanationAgent:
    def __init__(self, retriever):
        self.retriever = retriever

    def explain(self, history: list) -> str:
        query = " ".join(
            m["content"] for m in history if m["role"] == "user"
        )

        docs = self.retriever(query, top_k=6)
        context = self._format_context(docs)

        history_text = "\n".join(
            f"- {m['content']}"
            for m in history if m["role"] == "user"
        )

        messages = [
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {"role": "system", "content": f"TEXTBOOK CONTEXT:\n{context}"},
            {
                "role": "user",
                "content": f"""
Patient history:
{history_text}

Explain the condition in simple terms.
"""
            }
        ]

        return call_llm(messages, max_tokens=400)

    def _format_context(self, docs, max_chars=3500):
        blocks, total = [], 0
        for d in docs:
            if total + len(d["text"]) > max_chars:
                break
            blocks.append(d["text"])
            total += len(d["text"])
        return "\n---\n".join(blocks)
