from rules.patient_facts import PatientFacts
import re


def extract_facts(history):
    facts = PatientFacts()
    text = " ".join(
        m["content"].lower()
        for m in history
        if m["role"] == "user"
    )

    # =====================================================
    # BASIC SYMPTOMS
    # =====================================================
    if "fever" in text:
        facts.symptoms.append("fever")

    if "body pain" in text or "body ache" in text or "pain in body" in text or "entire body" in text:
        facts.symptoms.append("body pain")
        facts.musculoskeletal = True
    if "headache" in text:
        facts.symptoms.append("headache")
        facts.neuro = True
        
        # Extract additional headache characteristics
        if "one side" in text or "unilateral" in text:
            facts.headache_severity = 7  # Higher severity for unilateral headaches
        elif "both sides" in text or "bilateral" in text:
            facts.headache_severity = 3  # Lower severity for bilateral headaches
            
        # Check for stress triggers
        if "stress" in text or "scold" in text or "boss" in text:
            facts.stress = True

    if "cough" in text:
        facts.symptoms.append("cough")
        facts.respiratory = True

    if "chest pain" in text:
        facts.symptoms.append("chest pain")
        facts.cardiac = True

    # =====================================================
    # CARDIOVASCULAR SYMPTOMS
    # =====================================================
    if "blood pressure" in text or "hypertension" in text or "high bp" in text:
        facts.symptoms.append("high blood pressure")
        facts.cardiac = True
        # Check for elevated values
        bp_values = re.findall(r"(\d{2,3})/(\d{2,3})", text)
        if bp_values:
            systolic, diastolic = int(bp_values[0][0]), int(bp_values[0][1])
            facts.blood_pressure_systolic = systolic
            facts.blood_pressure_diastolic = diastolic
            # Mark as danger sign if severely elevated
            if systolic > 180 or diastolic > 120:
                facts.danger_signs.append("severe hypertension")

    # =====================================================
    # MUSCULOSKELETAL SYMPTOMS
    # =====================================================
    if "lump" in text or "mass" in text or "swelling" in text:
        facts.symptoms.append("lump")
        facts.musculoskeletal = True
        facts.swelling = True

    # =====================================================
    # GI / ABDOMINAL
    # =====================================================
    if "stomach pain" in text or "abdominal pain" in text or "belly pain" in text:
        facts.symptoms.append("stomach pain")
        facts.gi = True

    if "discomfort" in text or "bloating" in text or "indigestion" in text:
        facts.symptoms.append("indigestion")
        facts.gi = True

    if "vomit" in text or "vomiting" in text:
        facts.symptoms.append("vomiting")
        facts.vomiting = True
        facts.gi = True
        facts.danger_signs.append("vomiting")

    if "nausea" in text:
        facts.symptoms.append("nausea")
        facts.gi = True

    if "diarrhea" in text or "loose motion" in text:
        facts.symptoms.append("diarrhea")
        facts.gi = True
        facts.danger_signs.append("diarrhea")

    # =====================================================
    # FOOD-RELATED TRIGGERS
    # =====================================================
    if any(word in text for word in ["fried", "spicy", "oily", "outside food", "junk", "street"]):
        facts.food_trigger = True
    # =====================================================
    # DANGER SIGNS
    # =====================================================
    if "confusion" in text:
        facts.danger_signs.append("confusion")
        facts.neuro = True

    if "breath" in text or "shortness of breath" in text:
        facts.danger_signs.append("shortness of breath")
        facts.respiratory = True
        facts.shortness_of_breath = True

    if "blood" in text:
        facts.danger_signs.append("bleeding")
    # =====================================================
    # DURATION (DAYS / HOURS)
    # =====================================================
    days = re.findall(r"(\d+)\s*day", text)
    if days:
        facts.duration_days = int(days[0])

    hours = re.findall(r"(\d+)\s*(hour|hr)", text)
    if hours and facts.duration_days is None:
        # less than a day → treat as acute
        facts.duration_days = 0

    # =====================================================
    # TEMPERATURE
    # =====================================================
    temp_c = re.findall(r"(\d+\.?\d*)\s*c", text)
    if temp_c:
        facts.temperature_c = float(temp_c[0])

    temp_f = re.findall(r"(\d+\.?\d*)\s*f", text)
    if temp_f:
        facts.temperature_c = round((float(temp_f[0]) - 32) * 5 / 9, 1)

    # =====================================================
    # PAIN SEVERITY (VERY BASIC)
    # =====================================================
    if "severe" in text:
        facts.pain_severity = 8
    elif "mild" in text:
        facts.pain_severity = 3

    return facts
