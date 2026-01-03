from rules.disease_engine import DiseasePatternEngine
from rules.patient_facts import PatientFacts

engine = DiseasePatternEngine()


def test_uncomplicated_viral_fever():
    facts = PatientFacts(
        fever=True,
        duration_days=2,
        danger_signs=[]
    )

    matches = engine.evaluate(facts)

    assert len(matches) > 0
    assert matches[0]["disease"] == "Uncomplicated Viral Fever"
    assert matches[0]["severity"] == "LOW"


def test_emergency_shortness_of_breath():
    facts = PatientFacts(
        fever=True,
        danger_signs=["shortness of breath"]
    )

    matches = engine.evaluate(facts)

    assert matches[0]["severity"] == "EMERGENCY"


def test_cardiac_high_risk():
    facts = PatientFacts(
        cardiac=True,
        pain_severity=7,
        symptoms=["radiation"],
        danger_signs=["sweating"]
    )

    matches = engine.evaluate(facts)

    assert matches[0]["severity"] in ["HIGH", "EMERGENCY"]
