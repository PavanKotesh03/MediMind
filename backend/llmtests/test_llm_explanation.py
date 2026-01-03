from llm.explanation_agent import MedicalExplanationAgent


def dummy_retriever(query, top_k=5):
    return [{"text": "Fever is commonly caused by viral infections."}]


def test_explanation_contains_warning(monkeypatch):
    agent = MedicalExplanationAgent(dummy_retriever)

    def fake_llm(messages, **kwargs):
        return "If symptoms worsen or new warning signs appear, medical evaluation is important."

    monkeypatch.setattr("llm.explanation_agent.call_llm", fake_llm)

    explanation = agent.explain(
        disease="Uncomplicated Viral Fever",
        history=[{"role": "user", "content": "I have fever"}]
    )

    assert "medical evaluation is important" in explanation.lower()
