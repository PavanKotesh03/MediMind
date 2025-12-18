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

        total_required = 0
        matched_required = 0
        
        # Track optional matches for better scoring
        matched_optional = 0
        total_optional = 0

        # ----------------------------
        # REQUIRED SYMPTOMS
        # ----------------------------
        for s in pattern.get("required_symptoms", []):
            total_required += 1
            if s in facts.symptoms:
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # REQUIRED SYSTEM FLAGS
        # ----------------------------
        for flag in pattern.get("required_flags", []):
            total_required += 1
            if getattr(facts, flag, False):
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # REQUIRED DANGER SIGNS
        # ----------------------------
        for sign in pattern.get("required_danger_signs", []):
            total_required += 1
            if sign in facts.danger_signs:
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # EXCLUDE IF DANGER SIGNS PRESENT
        # ----------------------------
        if pattern.get("exclude_danger_signs"):
            total_required += 1
            if not facts.danger_signs:
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # AGE CONSTRAINT
        # ----------------------------
        if "min_age" in pattern:
            total_required += 1
            if facts.age is not None and facts.age >= pattern["min_age"]:
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # DURATION CONSTRAINT
        # ----------------------------
        if facts.duration_days is not None:
            if "min_duration_days" in pattern:
                total_required += 1
                if facts.duration_days >= pattern["min_duration_days"]:
                    matched_required += 1
                else:
                    return False, 0.0

            if "max_duration_days" in pattern:
                total_required += 1
                if facts.duration_days <= pattern["max_duration_days"]:
                    matched_required += 1
                else:
                    return False, 0.0

        # ----------------------------
        # TEMPERATURE CONSTRAINT
        # ----------------------------
        if "min_temperature_c" in pattern:
            total_required += 1
            if facts.temperature_c is not None and facts.temperature_c >= pattern["min_temperature_c"]:
                matched_required += 1
            else:
                return False, 0.0

        # ----------------------------
        # OPTIONAL SYMPTOMS (improves confidence score)
        # ----------------------------
        for s in pattern.get("optional_symptoms", []):
            total_optional += 1
            if s in facts.symptoms:
                matched_optional += 1

        # ----------------------------
        # OPTIONAL FLAGS (improves confidence score)
        # ----------------------------
        for flag in pattern.get("optional_flags", []):
            total_optional += 1
            if getattr(facts, flag, False):
                matched_optional += 1

        # ----------------------------
        # FINAL CONFIDENCE
        # ----------------------------
        # Calculate confidence based on how well the pattern fits the overall symptom picture
        # We want to favor patterns that explain more of the patient's actual symptoms
        total_criteria = total_required + total_optional
        
        if total_criteria == 0:
            confidence = 0.5
        else:
            # Calculate base confidence as percentage of criteria met
            base_confidence = (matched_required + matched_optional) / total_criteria
            
            # Apply boosts for specific matches
            confidence = base_confidence
            
            # Boost for matching specific patient facts
            if hasattr(facts, 'headache_severity') and facts.headache_severity and 'headache_severity' in pattern.get("optional_flags", []):
                confidence *= 1.2  # Boost for matching headache severity (unilateral)
                
            if hasattr(facts, 'stress') and facts.stress and 'stress' in pattern.get("required_flags", []):
                confidence *= 1.3  # Boost for matching stress trigger
                
            # Additional boost for patterns that require more specific criteria
            # This favors more specific diagnoses over general ones
            if total_criteria > 2:
                confidence *= 1.1  # Small boost for more specific patterns
                
        # Only cap at the end for the final result, but preserve relative differences
        # We'll scale all confidences to be between 0 and 1 while preserving relative differences
        confidence = min(2.0, confidence)  # Allow up to 2x boost
        final_confidence = min(1.0, confidence / 2.0)  # Scale back to 0-1 range

        # Ensure minimum confidence for matching patterns
        if final_confidence == 0 and total_required == 0:
            final_confidence = 0.5
        elif final_confidence == 0:
            final_confidence = 0.1  # Very low confidence for patterns that don't explain symptoms

        return True, final_confidence