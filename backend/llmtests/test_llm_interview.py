from llm.interview_agent import MedicalInterviewAgent


def test_interview_flow_end_marker(monkeypatch):
    agent = MedicalInterviewAgent()
    agent.min_questions = 0

    def fake_llm(messages, **kwargs):
        return "<END_OF_INTERVIEW>"

    monkeypatch.setattr("llm.interview_agent.call_llm", fake_llm)

    response = agent.start("I have fever")

    assert agent.finished is True
    assert "<END_OF_INTERVIEW>" in response
