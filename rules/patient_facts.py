from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PatientFacts:
    # =====================================================
    # CORE SYMPTOMS
    # =====================================================
    symptoms: List[str] = field(default_factory=list)

    # =====================================================
    # TIME & VITALS
    # =====================================================
    duration_days: Optional[int] = None
    onset_type: Optional[str] = None        # sudden / gradual
    temperature_c: Optional[float] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    oxygen_saturation: Optional[int] = None

    # =====================================================
    # PAIN CHARACTERISTICS
    # =====================================================
    pain_severity: Optional[int] = None      # 1–10
    pain_location: Optional[str] = None
    pain_radiation: Optional[str] = None
    pain_character: Optional[str] = None     # dull, sharp, burning
    pain_triggered_by_exertion: bool = False

    # =====================================================
    # DEMOGRAPHICS
    # =====================================================
    age: Optional[int] = None
    gender: Optional[str] = None             # male / female / other
    pregnancy: bool = False

    # =====================================================
    # SYSTEM-WISE FLAGS (VERY IMPORTANT)
    # =====================================================
    respiratory: bool = False
    cardiac: bool = False
    gi: bool = False
    neuro: bool = False
    musculoskeletal: bool = False
    dermatological: bool = False
    urinary: bool = False
    endocrine: bool = False
    hematological: bool = False

    # =====================================================
    # RESPIRATORY DETAILS
    # =====================================================
    cough_type: Optional[str] = None          # dry / productive
    sputum_color: Optional[str] = None
    wheezing: bool = False
    chest_tightness: bool = False
    shortness_of_breath: bool = False

    # =====================================================
    # CARDIAC DETAILS
    # =====================================================
    chest_pain_type: Optional[str] = None     # pressure, tightness
    palpitations: bool = False
    leg_swelling: bool = False
    syncope: bool = False

    # =====================================================
    # GI DETAILS
    # =====================================================
    vomiting: bool = False
    diarrhea: bool = False
    blood_in_stool: bool = False
    abdominal_distension: bool = False
    jaundice: bool = False

    # =====================================================
    # NEUROLOGICAL DETAILS
    # =====================================================
    headache_severity: Optional[int] = None
    photophobia: bool = False
    neck_stiffness: bool = False
    seizures: bool = False
    focal_weakness: bool = False
    speech_difficulty: bool = False
    altered_sensorium: bool = False

    # =====================================================
    # URINARY DETAILS
    # =====================================================
    burning_urination: bool = False
    frequent_urination: bool = False
    blood_in_urine: bool = False
    flank_pain: bool = False

    # =====================================================
    # SKIN / ALLERGY
    # =====================================================
    rash: bool = False
    itching: bool = False
    swelling: bool = False
    hives: bool = False

    # =====================================================
    # DANGER SIGNS (GLOBAL RED FLAGS)
    # =====================================================
    danger_signs: List[str] = field(default_factory=list)

    # =====================================================
    # COMORBIDITIES & RISK FACTORS
    # =====================================================
    diabetes: bool = False
    hypertension: bool = False
    heart_disease: bool = False
    lung_disease: bool = False
    kidney_disease: bool = False
    liver_disease: bool = False
    immunocompromised: bool = False

    # =====================================================
    # SOCIAL & EXPOSURE HISTORY
    # =====================================================
    smoking: bool = False
    alcohol: bool = False
    recent_travel: bool = False
    contact_with_sick_person: bool = False
    insect_bite: bool = False
    animal_bite: bool = False


    food_trigger: bool = False
    stress: bool = False
