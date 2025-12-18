# rules/disease_engine.py

class DiseasePatternEngine:
    """
    Rule-based disease / risk pattern engine.
    IMPORTANT:
    - This does NOT diagnose
    - It classifies symptom patterns + risk
    """

    def evaluate(self, facts):
        matches = []

        # ==========================
        # 🔴 CARDIAC / CHEST PAIN
        # ==========================
        if facts.cardiac:
            high_risk = False

            if facts.pain_severity and facts.pain_severity >= 4:
                high_risk = True

            if "shortness of breath" in facts.danger_signs:
                high_risk = True

            if "sweating" in facts.danger_signs:
                high_risk = True

            if "radiation" in facts.symptoms:
                high_risk = True

            if high_risk:
                matches.append({
                    "disease": "Possible Cardiac Chest Pain Pattern",
                    "severity": "HIGH",
                    "reason": "Chest pain with radiation, breathlessness, or sweating"
                })
            else:
                matches.append({
                    "disease": "Non-specific Chest Pain Pattern",
                    "severity": "MEDIUM",
                    "reason": "Chest pain without clear high-risk features"
                })

        # ==========================
        # 🟢 FEVER (VIRAL)
        # ==========================
        if facts.fever and not facts.danger_signs:
            if facts.duration_days is not None and facts.duration_days <= 3:
                matches.append({
                    "disease": "Uncomplicated Viral Fever",
                    "severity": "LOW",
                    "reason": "Short-duration fever without danger signs"
                })

        # ==========================
        # 🔴 SYSTEMIC / EMERGENCY
        # ==========================
        if facts.danger_signs:
            if (
                "confusion" in facts.danger_signs
                or "bleeding" in facts.danger_signs
                or "shortness of breath" in facts.danger_signs
            ):
                matches.insert(0, {
                    "disease": "Medical Emergency Pattern",
                    "severity": "EMERGENCY",
                    "reason": "Presence of serious danger signs"
                })

        return matches
