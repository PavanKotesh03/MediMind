from llm.llm_client import call_llm
from llm.prompts import INTERVIEW_SYSTEM_PROMPT

class MedicalInterviewAgent:
    def __init__(self, retriever):
        self.retriever = retriever
        self.history = []
        self.finished = False

    def start(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def reply(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def _ask_next(self) -> str:
        query = " ".join(
            m["content"] for m in self.history if m["role"] == "user"
        )

        docs = self.retriever(query, top_k=5)
        context = self._format_context(docs)

        messages = [
            {"role": "system", "content": INTERVIEW_SYSTEM_PROMPT},
            {"role": "system", "content": f"TEXTBOOK CONTEXT:\n{context}"},
            *self.history,
        ]

        response = call_llm(messages, max_tokens=120)
        self.history.append({"role": "assistant", "content": response})

        if "<END_OF_INTERVIEW>" in response:
            self.finished = True

        return response

    def _format_context(self, docs, max_chars=3000):
        blocks, total = [], 0
        for d in docs:
            if total + len(d["text"]) > max_chars:
                break
            blocks.append(d["text"])
            total += len(d["text"])
        return "\n---\n".join(blocks)
