# rules/disease_patterns.py

DISEASE_PATTERNS = [

# =====================================================
# FEVER & INFECTIOUS DISEASES
# =====================================================
{
    "name": "Uncomplicated Viral Fever",
    "required_symptoms": ["fever"],
    "max_duration_days": 5,
    "exclude_danger_signs": True,
    "severity": "LOW",
    "reason": "Short-duration fever without danger signs"
},
{
    "name": "Bacterial Infection (Possible)",
    "required_symptoms": ["fever"],
    "min_duration_days": 4,
    "severity": "MODERATE",
    "reason": "Fever persisting beyond viral duration"
},
{
    "name": "High Grade Fever",
    "required_symptoms": ["fever"],
    "min_temperature_c": 39,
    "severity": "HIGH",
    "reason": "High-grade fever increases complication risk"
},
{
    "name": "Sepsis (Possible)",
    "required_symptoms": ["fever"],
    "required_danger_signs": ["confusion", "low blood pressure"],
    "severity": "EMERGENCY",
    "reason": "Systemic infection with organ dysfunction"
},

# =====================================================
# RESPIRATORY SYSTEM
# =====================================================
{
    "name": "Upper Respiratory Tract Infection",
    "system": "respiratory",
    "required_symptoms": ["cough"],
    "exclude_danger_signs": True,
    "severity": "LOW",
    "reason": "Mild respiratory symptoms"
},
{
    "name": "Acute Bronchitis",
    "system": "respiratory",
    "required_symptoms": ["cough"],
    "optional_symptoms": ["fever"],
    "severity": "MODERATE",
    "reason": "Inflammation of bronchi"
},
{
    "name": "Pneumonia (Possible)",
    "system": "respiratory",
    "required_symptoms": ["fever", "cough"],
    "required_flags": ["shortness_of_breath"],
    "severity": "HIGH",
    "reason": "Lower respiratory tract involvement"
},
{
    "name": "Acute Asthma Exacerbation",
    "system": "respiratory",
    "required_flags": ["wheezing", "shortness_of_breath"],
    "severity": "HIGH",
    "reason": "Airway obstruction causing respiratory distress"
},

# =====================================================
# CARDIAC SYSTEM
# =====================================================
{
    "name": "Stable Angina",
    "system": "cardiac",
    "required_symptoms": ["chest pain"],
    "required_flags": ["pain_triggered_by_exertion"],
    "severity": "MODERATE",
    "reason": "Exertional chest pain with cardiac origin"
},
{
    "name": "Acute Coronary Syndrome",
    "system": "cardiac",
    "required_symptoms": ["chest pain"],
    "required_danger_signs": ["sweating", "shortness of breath"],
    "severity": "EMERGENCY",
    "reason": "Possible myocardial infarction"
},
{
    "name": "Heart Failure Exacerbation",
    "system": "cardiac",
    "required_flags": ["shortness_of_breath", "leg_swelling"],
    "severity": "HIGH",
    "reason": "Fluid overload and reduced cardiac output"
},

# =====================================================
# GASTROINTESTINAL SYSTEM
# =====================================================
{
    "name": "Acute Gastritis",
    "system": "gi",
    "required_symptoms": ["abdominal pain"],
    "exclude_danger_signs": True,
    "severity": "LOW",
    "reason": "Upper abdominal inflammation"
},
{
    "name": "Gastroenteritis",
    "system": "gi",
    "required_flags": ["diarrhea"],
    "severity": "LOW",
    "reason": "Acute bowel infection"
},
{
    "name": "Acute Appendicitis (Possible)",
    "system": "gi",
    "required_symptoms": ["abdominal pain"],
    "required_flags": ["vomiting"],
    "severity": "HIGH",
    "reason": "Progressive inflammatory abdominal pathology"
},
{
    "name": "Acute Hepatitis (Possible)",
    "system": "gi",
    "required_flags": ["jaundice"],
    "severity": "HIGH",
    "reason": "Liver inflammation"
},

# =====================================================
# NEUROLOGICAL SYSTEM
# =====================================================
{
    "name": "Migraine",
    "system": "neuro",
    "required_symptoms": ["headache"],
    "exclude_danger_signs": True,
    "severity": "MODERATE",
    "reason": "Recurrent neurovascular headache"
},
{
    "name": "Meningitis (Possible)",
    "system": "neuro",
    "required_symptoms": ["fever", "headache"],
    "required_flags": ["neck_stiffness", "altered_sensorium"],
    "severity": "EMERGENCY",
    "reason": "Central nervous system infection"
},
{
    "name": "Stroke (Possible)",
    "system": "neuro",
    "required_flags": ["focal_weakness", "speech_difficulty"],
    "severity": "EMERGENCY",
    "reason": "Acute focal neurological deficit"
},

# =====================================================
# URINARY SYSTEM
# =====================================================
{
    "name": "Urinary Tract Infection",
    "system": "urinary",
    "required_flags": ["burning_urination"],
    "severity": "MODERATE",
    "reason": "Lower urinary tract infection"
},
{
    "name": "Acute Pyelonephritis",
    "system": "urinary",
    "required_flags": ["burning_urination", "flank_pain"],
    "required_symptoms": ["fever"],
    "severity": "HIGH",
    "reason": "Upper urinary tract infection"
},

# =====================================================
# MUSCULOSKELETAL SYSTEM
# =====================================================
{
    "name": "Soft Tissue Injury with Swelling",
    "system": "musculoskeletal",
    "required_symptoms": ["lump"],
    "required_flags": ["swelling"],
    "optional_flags": ["pain_severity"],
    "severity": "MODERATE",
    "reason": "Trauma-induced soft tissue swelling with associated pain"
},

# =====================================================
# METABOLIC & SYSTEMIC
# =====================================================
{
    "name": "Hypoglycemia",
    "required_symptoms": ["dizziness"],
    "required_flags": ["altered_sensorium"],
    "severity": "HIGH",
    "reason": "Low blood glucose affecting brain function"
},
{
    "name": "Dehydration",
    "required_symptoms": ["dizziness"],
    "severity": "MODERATE",
    "reason": "Reduced circulating volume"
},

# =====================================================
# SPECIAL POPULATIONS
# =====================================================
{
    "name": "Elderly High-Risk Infection",
    "required_symptoms": ["fever"],
    "min_age": 60,
    "severity": "HIGH",
    "reason": "Elderly patients deteriorate rapidly"
},
{
    "name": "Immunocompromised Infection Risk",
    "required_symptoms": ["fever"],
    "required_flags": ["immunocompromised"],
    "severity": "HIGH",
    "reason": "Reduced immune defense"
}

]
