from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent

# import your hybrid RAG function
from scripts.step4_query_system_hybrid import hybrid_search


def retriever(query, top_k=5):
    results = hybrid_search(query, top_k=top_k)
    return [{"text": r["text"], "metadata": r.get("metadata", {})} for r in results]


def main():
    interview = MedicalInterviewAgent(retriever)
    explanation = MedicalExplanationAgent(retriever)

    print("\nMedical Assistant (Ctrl+C to exit)\n")

    first = input("You: ")
    print("AI:", interview.start(first))

    while True:
        user_input = input("You: ")
        response = interview.reply(user_input)

        if interview.finished:
            print("\nAI: Thank you. Here is a simple explanation:\n")
            print(explanation.explain(interview.history))
            break

        print("AI:", response)


if __name__ == "__main__":
    main()
