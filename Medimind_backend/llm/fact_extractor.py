from rules.patient_facts import PatientFacts
import re


def extract_facts(history):
    facts = PatientFacts()

    text = " ".join(
        m["content"].lower()
        for m in history
        if m["role"] == "user"
    )

    # ======================
    # BASIC SYMPTOMS
    # ======================
    if "fever" in text:
        facts.symptoms.append("fever")
        facts.fever = True

    if "headache" in text:
        facts.symptoms.append("headache")
        facts.neuro = True

    if "cough" in text:
        facts.symptoms.append("cough")
        facts.respiratory = True

    # ======================
    # CHEST / CARDIAC
    # ======================
    if "chest pain" in text or "heart pain" in text:
        facts.symptoms.append("chest pain")
        facts.cardiac = True

    if "arm" in text or "radiate" in text:
        facts.symptoms.append("radiation")
        facts.cardiac = True

    if "shortness of breath" in text or "breathless" in text:
        facts.danger_signs.append("shortness of breath")
        facts.respiratory = True
        facts.cardiac = True

    if "sweat" in text or "cold sweat" in text:
        facts.danger_signs.append("sweating")
        facts.cardiac = True

    # ======================
    # GI
    # ======================
    if "vomit" in text:
        facts.symptoms.append("vomiting")
        facts.gi = True
        facts.danger_signs.append("vomiting")

    if "diarrhea" in text or "loose motion" in text:
        facts.symptoms.append("diarrhea")
        facts.gi = True
        facts.danger_signs.append("diarrhea")

    # ======================
    # DURATION
    # ======================
    days = re.findall(r"(\d+)\s*day", text)
    if days:
        facts.duration_days = int(days[0])

    hours = re.findall(r"(\d+)\s*(hour|hr)", text)
    if hours and facts.duration_days is None:
        facts.duration_days = 0

    # ======================
    # PAIN SEVERITY
    # ======================
    if "severe" in text:
        facts.pain_severity = 8
    elif "moderate" in text:
        facts.pain_severity = 5
    elif "mild" in text:
        facts.pain_severity = 3

    return facts
