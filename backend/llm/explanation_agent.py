# llm/explanation_agent.py

from llm.llm_client import call_llm
from llm.prompts import EXPLANATION_SYSTEM_PROMPT


class MedicalExplanationAgent:
    def __init__(self, retriever):
        self.retriever = retriever

    def explain(self, disease: str, history: list) -> str:
        """
        Generates explanation using:
        - Disease-based RAG if disease is known
        - Symptom-based RAG if disease is undifferentiated
        """

        #  Build symptom-based query from history
        symptom_query = self._build_symptom_query(history)

        #  Decide RAG query
        if disease.lower().startswith("undifferentiated"):
            rag_query = symptom_query
            explanation_mode = "symptom-based"
        else:
            rag_query = disease
            explanation_mode = "disease-based"

        #  RAG retrieval
        docs = self.retriever(rag_query, top_k=6)
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
Patient symptoms:
{history_text}

Current assessment: {disease}

Explain the symptoms in simple terms.
Explain possible physiological reasons for these symptoms
without confirming a diagnosis.
Explain why the severity level is appropriate.
Mention warning signs briefly.

(Explanation mode: {explanation_mode})
"""
            }
        ]

        return call_llm(messages, max_tokens=450)

    def _build_symptom_query(self, history):
        """
        Extracts key symptom keywords from conversation
        to drive RAG when disease is undifferentiated.
        """
        keywords = set()

        for m in history:
            if m["role"] != "user":
                continue

            text = m["content"].lower()

            symptom_terms = [
                "breathing", "shortness of breath", "cough", "chest pain",
                "fever", "sweating", "lying down", "orthopnea",
                "wheezing", "tightness", "fatigue", "dizziness",
                "vomiting", "nausea"
            ]

            for term in symptom_terms:
                if term in text:
                    keywords.add(term)

        # Fallback if nothing detected
        if not keywords:
            return "general symptoms medical explanation"

        return " ".join(sorted(keywords))

    def _format_context(self, docs, max_chars=3500):
        blocks, total = [], 0
        for d in docs:
            text = d["text"]
            if total + len(text) > max_chars:
                break
            blocks.append(text)
            total += len(text)
        return "\n---\n".join(blocks)
