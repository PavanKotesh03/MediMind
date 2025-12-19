from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from llm.explanation_agent import explain


class MedicalDecisionPipeline:
    """
    Bridges:
    LLM Interview → Rule Engine → RAG Explanation
    """

    def __init__(self):
        self.engine = DiseasePatternEngine()

    def run(self, history: list[dict]) -> dict:
        """
        history: full LLM interview conversation
        returns: final structured output
        """

        # 1️⃣ Extract structured facts
        facts = extract_facts(history)

        # 2️⃣ Evaluate disease patterns
        matches = self.engine.evaluate(facts)

        if not matches:
            return {
                "disease": None,
                "severity": None,
                "explanation": "No clear disease pattern could be identified."
            }

        # 3️⃣ Pick highest severity disease
        top = matches[0]

        # 4️⃣ Generate explanation using RAG + LLM
        explanation = explain(top["disease"], history)

        return {
            "disease": top["disease"],
            "severity": top["severity"],
            "reason": top["reason"],
            "explanation": explanation
        }
