# rules/disease_engine.py

from rules.disease_patterns import DISEASE_PATTERNS
from rules.severity_utils import sort_by_severity
from rules.patient_facts import PatientFacts


class DiseasePatternEngine:

    def evaluate(self, facts: PatientFacts) -> list[dict]:
        matches = []

        for pattern in DISEASE_PATTERNS:
            matched, score = self._match_pattern_with_confidence(pattern, facts)
            if matched:
                matches.append({
                    "disease": pattern["name"],
                    "severity": pattern["severity"],
                    "reason": pattern["reason"],
                    "confidence": round(score, 2)
                })

        return sort_by_severity(matches)

    # =====================================================
    # MATCH + CONFIDENCE CALCULATION
    # =====================================================
    def _match_pattern_with_confidence(
        self, pattern: dict, facts: PatientFacts
    ) -> tuple[bool, float]:

        total_checks = 0
        matched_checks = 0

        # ----------------------------
        # REQUIRED SYMPTOMS
        # ----------------------------
        for s in pattern.get("required_symptoms", []):
            total_checks += 1
            if s in facts.symptoms:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # REQUIRED SYSTEM FLAGS
        # ----------------------------
        for flag in pattern.get("required_flags", []):
            total_checks += 1
            if getattr(facts, flag, False):
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # REQUIRED DANGER SIGNS
        # ----------------------------
        for sign in pattern.get("required_danger_signs", []):
            total_checks += 1
            if sign in facts.danger_signs:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # EXCLUDE IF DANGER SIGNS PRESENT
        # ----------------------------
        if pattern.get("exclude_danger_signs"):
            total_checks += 1
            if not facts.danger_signs:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # AGE CONSTRAINT
        # ----------------------------
        if "min_age" in pattern:
            total_checks += 1
            if facts.age is not None and facts.age >= pattern["min_age"]:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # DURATION CONSTRAINT
        # ----------------------------
        if facts.duration_days is not None:
            if "min_duration_days" in pattern:
                total_checks += 1
                if facts.duration_days >= pattern["min_duration_days"]:
                    matched_checks += 1
                else:
                    return False, 0.0

            if "max_duration_days" in pattern:
                total_checks += 1
                if facts.duration_days <= pattern["max_duration_days"]:
                    matched_checks += 1
                else:
                    return False, 0.0

        # ----------------------------
        # TEMPERATURE CONSTRAINT
        # ----------------------------
        if "min_temperature_c" in pattern:
            total_checks += 1
            if facts.temperature_c is not None and facts.temperature_c >= pattern["min_temperature_c"]:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # TEMPERATURE CONSTRAINT
        # ----------------------------
        if "min_temperature_c" in pattern:
            total_checks += 1
            if facts.temperature_c is not None and facts.temperature_c >= pattern["min_temperature_c"]:
                matched_checks += 1
            else:
                return False, 0.0

        # ----------------------------
        # FINAL CONFIDENCE
        # ----------------------------
        if total_checks == 0:
            confidence = 0.5
        else:
            confidence = matched_checks / total_checks

        return True, confidence
