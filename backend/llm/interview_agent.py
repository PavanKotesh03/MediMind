from llm.llm_client import call_llm, call_llm_streaming
from llm.prompts import INTERVIEW_SYSTEM_PROMPT
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class MedicalInterviewAgent:
    def __init__(self):
        logger.debug("Initializing MedicalInterviewAgent")
        self.history = []
        self.finished = False
        self.min_questions = 5  # 🆕 Minimum questions before allowing completion

    def start(self, user_message: str) -> str:
        """Non-streaming start - backwards compatible"""
        logger.info("Starting medical interview")
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def reply(self, user_message: str) -> str:
        """Non-streaming reply - backwards compatible"""
        logger.debug("Processing user reply in interview")
        self.history.append({"role": "user", "content": user_message})
        return self._ask_next()

    def _ask_next(self) -> str:
        """Generate next question (non-streaming)"""
        logger.debug("Generating next interview question")
        
        # Count user messages (questions asked)
        user_messages = [m for m in self.history if m["role"] == "user"]
        questions_asked = len(user_messages)
        
        # 🆕 Build prompt with completion rules
        system_prompt = self._build_system_prompt(questions_asked)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.history,
        ]

        response_obj = call_llm(messages, max_tokens=150)
        
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
        
        self.history.append({"role": "assistant", "content": response})

        # 🆕 Check completion with minimum questions requirement
        if questions_asked >= self.min_questions and "<END_OF_INTERVIEW>" in response.upper():
            logger.info(f"Interview completed after {questions_asked} questions")
            self.finished = True
        elif len(self.history) >= 20:  # Maximum conversation length
            logger.info("Interview reached maximum length")
            self.finished = True

        return response

    async def start_streaming(self, user_message: str) -> AsyncGenerator[str, None]:
        """Start interview with streaming response"""
        logger.info("Starting medical interview with streaming")
        self.history.append({"role": "user", "content": user_message})
        
        async for token in self._ask_next_streaming():
            yield token

    async def reply_streaming(self, user_message: str) -> AsyncGenerator[str, None]:
        """Continue interview with streaming response"""
        logger.debug("Processing user reply in interview with streaming")
        self.history.append({"role": "user", "content": user_message})
        
        async for token in self._ask_next_streaming():
            yield token

    async def _ask_next_streaming(self) -> AsyncGenerator[str, None]:
        """Generate next question with streaming"""
        logger.debug("Generating next interview question (streaming)")
        
        # Count user messages
        user_messages = [m for m in self.history if m["role"] == "user"]
        questions_asked = len(user_messages)
        
        # 🆕 Build prompt with completion rules
        system_prompt = self._build_system_prompt(questions_asked)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.history,
        ]

        full_response = []
        
        async for token in call_llm_streaming(messages, max_tokens=150):
            full_response.append(token)
            yield token
        
        response = "".join(full_response).strip()
        logger.debug(f"Complete streaming response: {response[:100]}...")
        
        self.history.append({"role": "assistant", "content": response})

        # 🆕 Check completion with minimum questions requirement
        if questions_asked >= self.min_questions and "<END_OF_INTERVIEW>" in response.upper():
            logger.info(f"Interview completed after {questions_asked} questions")
            self.finished = True
        elif len(self.history) >= 20:
            logger.info("Interview reached maximum length")
            self.finished = True

    # 🆕 BUILD DYNAMIC SYSTEM PROMPT
    def _build_system_prompt(self, questions_asked: int) -> str:
        """Build system prompt based on interview progress"""
        
        base_prompt = INTERVIEW_SYSTEM_PROMPT
        
        if questions_asked < self.min_questions:
            # Force more questions
            completion_rules = f"""
IMPORTANT RULES:
- You MUST ask at least {self.min_questions - questions_asked} more questions before ending
- DO NOT say "<END_OF_INTERVIEW>" yet
- Keep gathering detailed symptom information
- Ask about: duration, severity, associated symptoms, aggravating/relieving factors
"""
        else:
            # Allow completion if enough info gathered
            completion_rules = """
COMPLETION RULES:
- If you have gathered sufficient information about:
  1. Main symptoms and duration
  2. Severity and progression
  3. Associated symptoms
  4. Medical history relevance
  5. Any danger signs
- Then you may say "<END_OF_INTERVIEW>" to conclude
- Otherwise, ask 1-2 more clarifying questions
"""
        
        return base_prompt + "\n\n" + completion_rules

    def _format_context(self, docs, max_chars=3000):
        """Format retrieval context (not used currently for speed)"""
        blocks, total = [], 0
        for d in docs:
            if total + len(d["text"]) > max_chars:
                break
            blocks.append(d["text"])
            total += len(d["text"])
        return "\n---\n".join(blocks)
