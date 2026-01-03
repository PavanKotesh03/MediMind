# main.py

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts

from rules.disease_engine import DiseasePatternEngine

# Hybrid RAG retriever
from scripts.step4_query_system_hybrid import hybrid_search

logger = logging.getLogger(__name__)
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts

from rules.disease_engine import DiseasePatternEngine

# Hybrid RAG retriever
from scripts.step4_query_system_hybrid import hybrid_search


def retriever(query, top_k=5):
    """
    Wrapper over hybrid RAG search.
    Returns documents in a format suitable for agents.
    """
    results = hybrid_search(query)
    return [
        {
            "text": r["text"],
            "metadata": r.get("metadata", {})
        }
        for r in results[:top_k]
    ]


def main():
    logger.info("Starting Medical Assistant application")
    interview = MedicalInterviewAgent()
    explanation_agent = MedicalExplanationAgent(retriever)
    disease_engine = DiseasePatternEngine()

    print("\n🩺 Medical Assistant (Ctrl+C to exit)\n")

    # ================= INTERVIEW PHASE =================
    first = input("You: ")
    logger.info("Starting interview phase")
    print("AI:", interview.start(first))

    while True:
        user_input = input("You: ")
        response = interview.reply(user_input)

        if interview.finished:
            logger.info("Interview phase completed")
            break

        print("AI:", response)

    # ================= RULE ENGINE PHASE =================
    logger.info("Starting rule engine phase")
    facts = extract_facts(interview.history)
    matches = disease_engine.evaluate(facts)

    print("\n================ FINAL ASSESSMENT ================\n")

    #  SAFE FALLBACK IF NO DISEASE PATTERN MATCHES
    if not matches:
        logger.warning("No disease pattern matches found, using fallback")
        top = {
            "disease": "Undifferentiated Symptom Pattern",
            "severity": "MEDIUM",
            "reason": "Symptoms require further medical evaluation"
        }
    else:
        top = matches[0]
        logger.info(f"Disease pattern matched: {top['disease']}, severity: {top['severity']}")

    print("Condition Pattern :", top["disease"])
    print("Severity          :", top["severity"])
    print("Reason            :", top["reason"])

    #  EMERGENCY SHORT-CIRCUIT 
    if top["severity"] == "EMERGENCY":
        logger.critical("Emergency condition detected")
        print("\n EMERGENCY WARNING ")
        print("This condition may be serious or life-threatening.")
        print("Please seek immediate medical care.")
        return

    # ================= EXPLANATION PHASE =================
    logger.info("Starting explanation phase")
    print("\n================ EXPLANATION =====================\n")

    explanation = explanation_agent.explain(
        disease=top["disease"],
        history=interview.history
    )

    print(explanation)
    logger.info("Medical Assistant session completed successfully")


if __name__ == "__main__":
    main()
