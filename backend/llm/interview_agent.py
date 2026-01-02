from llm.llm_client import call_llm
from llm.prompts import INTERVIEW_SYSTEM_PROMPT

import logging

logger = logging.getLogger(__name__)


class MedicalInterviewAgent:
    def __init__(self, retriever):
        logger.debug("Initializing MedicalInterviewAgent")
        self.retriever = retriever
        self.history = []
        self.finished = False

    def start(self, user_message: str) -> str:
        logger.info("Starting medical interview")
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def reply(self, user_message: str) -> str:
        logger.debug("Processing user reply in interview")
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def _ask_next(self) -> str:
        logger.debug("Generating next interview question")
        query = " ".join(
            m["content"] for m in self.history if m["role"] == "user"
        )

        # Removed RAG search during interview for speed
        # docs = self.retriever(query, top_k=5)
        # context = self._format_context(docs)

        messages = [
            {"role": "system", "content": INTERVIEW_SYSTEM_PROMPT},
            # Removed textbook context for faster responses
            # {"role": "system", "content": f"TEXTBOOK CONTEXT:\n{context}"},
            *self.history,
        ]

        # 🔧 FIX: Call LLM and extract string content
        response_obj = call_llm(messages, max_tokens=120)
        
        # Extract text from response object
        if isinstance(response_obj, dict):
            if "message" in response_obj and "content" in response_obj["message"]:
                response = response_obj["message"]["content"]
            elif "content" in response_obj:
                response = response_obj["content"]
            else:
                logger.error(f"Unexpected LLM response format: {response_obj}")
                response = str(response_obj)
        else:
            response = str(response_obj)
        
        logger.debug(f"Extracted response text: {response[:100]}...")
        
        # Store string content in history
        self.history.append({"role": "assistant", "content": response})

        if "<END_OF_INTERVIEW>" in response.upper():
            logger.info("Interview completed")
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
