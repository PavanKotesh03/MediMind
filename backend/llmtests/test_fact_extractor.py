from llm.fact_extractor import extract_facts


def test_extract_fever_and_headache():
    history = [
        {"role": "user", "content": "I have fever and headache for 2 days"}
    ]

    facts = extract_facts(history)

    assert facts.fever is True
    assert "fever" in facts.symptoms
    assert "headache" in facts.symptoms
    assert facts.duration_days == 2


def test_extract_cardiac_symptoms():
    history = [
        {"role": "user", "content": "I have chest pain radiating to my arm and sweating"}
    ]

    facts = extract_facts(history)

    assert facts.cardiac is True
    assert "radiation" in facts.symptoms
    assert "sweating" in facts.danger_signs
