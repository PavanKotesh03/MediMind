from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from llm.explanation_agent import explain_multiple


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
        returns: final structured output with multiple possibilities
        """

        # 1️⃣ Extract structured facts
        facts = extract_facts(history)

        # 2️⃣ Evaluate disease patterns
        matches = self.engine.evaluate(facts)

        if not matches:
            return {
                "matches": [],
                "explanation": "No clear disease patterns could be identified based on the symptoms discussed."
            }

        # 3️⃣ Limit to top 3 matches for clarity
        top_matches = matches[:3]

        # 4️⃣ Generate explanations for all top matches
        explanations = []
        for match in top_matches:
            explanation = explain_multiple(match["disease"], history, match["confidence"], match["severity"])
            explanations.append({
                "disease": match["disease"],
                "severity": match["severity"],
                "confidence": match["confidence"],
                "reason": match["reason"],
                "explanation": explanation
            })

        return {
            "matches": explanations,
            "explanation": self._format_probabilistic_explanation(explanations)
        }

    def _format_probabilistic_explanation(self, matches: list) -> str:
        """Format multiple possibilities in a reassuring, probabilistic way"""
        if not matches:
            return "No clear patterns identified."
        
        explanation = "Based on the symptoms you've described, here are some possibilities to consider:\n\n"
        
        for i, match in enumerate(matches, 1):
            confidence_desc = self._confidence_to_description(match["confidence"])
            severity_desc = match["severity"].lower()
            
            explanation += f"{i}. {match['disease']} ({confidence_desc} likelihood, {severity_desc} severity)\n"
        
        explanation += "\n📝 Simple Explanations:\n\n"
        # Add detailed explanations for all conditions
        for i, match in enumerate(matches, 1):
            explanation += f"{i}. {match['disease']}:\n"
            explanation += match["explanation"]
            explanation += "\n"
        
        return explanation

    def _confidence_to_description(self, confidence: float) -> str:
        """Convert numerical confidence to descriptive terms"""
        if confidence >= 0.9:
            return "high"
        elif confidence >= 0.7:
            return "moderate"
        elif confidence >= 0.5:
            return "low"
        else:
            return "very low"