"""Rule-based clinical safety checks for the healthcare agent tools.

Scope: a demonstration interaction table covering well-established, high-signal
drug-drug interaction classes. It is deliberately not a substitute for a
licensed clinical drug database, and callers are told so in every response.
"""

import itertools
import re
from typing import Any, Dict, List, Optional, Set

# Ingredient -> drug class. Names are matched case-insensitively on word
# boundaries, so "Lisinopril 20 MG" and "lisinopril" both resolve.
DRUG_CLASSES: Dict[str, Set[str]] = {
    "ace_inhibitor": {
        "lisinopril", "enalapril", "enalaprilat", "ramipril", "captopril",
        "benazepril", "quinapril", "perindopril", "fosinopril", "trandolapril",
        "moexipril",
    },
    "arb": {
        "losartan", "valsartan", "irbesartan", "candesartan", "olmesartan",
        "telmisartan", "azilsartan", "eprosartan",
    },
    "direct_renin_inhibitor": {"aliskiren"},
    "potassium_sparing_diuretic": {
        "spironolactone", "eplerenone", "amiloride", "triamterene",
    },
    "potassium_supplement": {
        "potassium chloride", "potassium citrate", "potassium gluconate",
    },
    "loop_diuretic": {"furosemide", "bumetanide", "torsemide", "ethacrynic acid"},
    "thiazide_diuretic": {
        "hydrochlorothiazide", "chlorthalidone", "indapamide", "metolazone",
    },
    "anticoagulant": {
        "warfarin", "apixaban", "rivaroxaban", "edoxaban", "dabigatran",
        "enoxaparin", "dalteparin", "heparin", "fondaparinux",
    },
    "antiplatelet": {
        "aspirin", "acetylsalicylic acid", "clopidogrel", "ticagrelor",
        "prasugrel", "dipyridamole", "cilostazol",
    },
    "nsaid": {
        "ibuprofen", "naproxen", "diclofenac", "indomethacin", "ketorolac",
        "meloxicam", "celecoxib", "piroxicam", "etodolac", "nabumetone",
        "sulindac", "ketoprofen",
    },
    "ssri": {
        "sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram",
        "fluvoxamine",
    },
    "snri": {"venlafaxine", "desvenlafaxine", "duloxetine", "levomilnacipran"},
    "tricyclic": {
        "amitriptyline", "nortriptyline", "imipramine", "clomipramine",
        "desipramine", "doxepin",
    },
    "maoi": {
        "phenelzine", "tranylcypromine", "isocarboxazid", "selegiline",
        "rasagiline", "linezolid", "methylene blue",
    },
    "triptan": {
        "sumatriptan", "rizatriptan", "zolmitriptan", "naratriptan",
        "eletriptan", "frovatriptan",
    },
    "serotonergic_opioid": {
        "tramadol", "fentanyl", "meperidine", "methadone", "tapentadol",
    },
    "other_serotonergic": {
        "trazodone", "mirtazapine", "buspirone", "lithium", "dextromethorphan",
        "ondansetron", "st john's wort",
    },
    "statin": {
        "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin",
        "lovastatin", "fluvastatin", "pitavastatin",
    },
    "cyp3a4_inhibitor": {
        "clarithromycin", "erythromycin", "itraconazole", "ketoconazole",
        "fluconazole", "voriconazole", "posaconazole", "ritonavir",
        "cobicistat", "diltiazem", "verapamil",
    },
    "corticosteroid": {
        "prednisone", "prednisolone", "methylprednisolone", "dexamethasone",
        "hydrocortisone", "budesonide",
    },
    "beta_blocker": {
        "metoprolol", "atenolol", "carvedilol", "bisoprolol", "propranolol",
        "nebivolol", "labetalol",
    },
    "sulfonylurea": {"glipizide", "glyburide", "glimepiride"},
    "insulin": {"insulin glargine", "insulin lispro", "insulin aspart", "insulin"},
    "biguanide": {"metformin"},
    "benzodiazepine": {
        "alprazolam", "lorazepam", "diazepam", "clonazepam", "temazepam",
        "midazolam",
    },
    "opioid": {
        "morphine", "oxycodone", "hydrocodone", "hydromorphone", "codeine",
        "tramadol", "fentanyl", "meperidine", "methadone", "tapentadol",
        "buprenorphine",
    },
}

CLASS_LABELS: Dict[str, str] = {
    "ace_inhibitor": "ACE inhibitor",
    "arb": "angiotensin receptor blocker",
    "direct_renin_inhibitor": "direct renin inhibitor",
    "potassium_sparing_diuretic": "potassium-sparing diuretic",
    "potassium_supplement": "potassium supplement",
    "loop_diuretic": "loop diuretic",
    "thiazide_diuretic": "thiazide diuretic",
    "anticoagulant": "anticoagulant",
    "antiplatelet": "antiplatelet",
    "nsaid": "NSAID",
    "ssri": "SSRI",
    "snri": "SNRI",
    "tricyclic": "tricyclic antidepressant",
    "maoi": "MAO inhibitor",
    "triptan": "triptan",
    "serotonergic_opioid": "serotonergic opioid",
    "other_serotonergic": "serotonergic agent",
    "statin": "statin",
    "cyp3a4_inhibitor": "CYP3A4 inhibitor",
    "corticosteroid": "corticosteroid",
    "beta_blocker": "beta blocker",
    "sulfonylurea": "sulfonylurea",
    "insulin": "insulin",
    "biguanide": "biguanide",
    "benzodiazepine": "benzodiazepine",
    "opioid": "opioid",
}

RAAS_BLOCKERS = {"ace_inhibitor", "arb", "direct_renin_inhibitor"}
SEROTONERGIC = {
    "ssri", "snri", "tricyclic", "triptan", "serotonergic_opioid",
    "other_serotonergic",
}

# Each rule fires when distinct medications can be assigned one-per-group, where
# a medication satisfies a group if it belongs to any class in that group.
INTERACTION_RULES: List[Dict[str, Any]] = [
    {
        "id": "dual-raas-blockade",
        "name": "Dual RAAS blockade",
        "severity": "major",
        "groups": [{"ace_inhibitor"}, {"arb"}],
        "effect": "Combined ACE inhibitor and ARB therapy roughly doubles the rate of "
                  "hyperkalemia, hypotension and acute kidney injury without an "
                  "offsetting cardiovascular benefit (ONTARGET, ALTITUDE).",
        "management": "Discontinue one agent; guidelines advise against routine combined "
                      "ACE inhibitor plus ARB therapy.",
        "monitoring": ["Serum potassium", "Serum creatinine / eGFR", "Blood pressure"],
    },
    {
        "id": "raas-potassium-sparing-diuretic",
        "name": "RAAS blocker + potassium-sparing diuretic",
        "severity": "major",
        "groups": [RAAS_BLOCKERS, {"potassium_sparing_diuretic"}],
        "effect": "Additive potassium retention; a leading cause of severe, "
                  "sometimes fatal hyperkalemia, especially with reduced renal "
                  "function or volume depletion.",
        "management": "If the combination is clinically indicated (e.g. HFrEF), use the "
                      "lowest effective doses and confirm baseline potassium and renal "
                      "function before starting.",
        "monitoring": [
            "Serum potassium at baseline, 1 week and 4 weeks after any dose change",
            "Serum creatinine / eGFR",
        ],
    },
    {
        "id": "raas-potassium-supplement",
        "name": "RAAS blocker + potassium supplement",
        "severity": "major",
        "groups": [RAAS_BLOCKERS, {"potassium_supplement"}],
        "effect": "Potassium supplementation on top of RAAS blockade raises the risk of "
                  "hyperkalemia and cardiac arrhythmia.",
        "management": "Reassess whether supplementation is still required; stop it unless "
                      "hypokalemia is documented.",
        "monitoring": ["Serum potassium", "ECG if potassium elevated"],
    },
    {
        "id": "potassium-sparing-plus-supplement",
        "name": "Potassium-sparing diuretic + potassium supplement",
        "severity": "major",
        "groups": [{"potassium_sparing_diuretic"}, {"potassium_supplement"}],
        "effect": "Directly additive hyperkalemia risk.",
        "management": "Avoid the combination unless potassium is actively being repleted "
                      "under monitoring.",
        "monitoring": ["Serum potassium"],
    },
    {
        "id": "triple-whammy-aki",
        "name": "Triple whammy (RAAS blocker + diuretic + NSAID)",
        "severity": "major",
        "groups": [RAAS_BLOCKERS, {"loop_diuretic", "thiazide_diuretic"}, {"nsaid"}],
        "effect": "NSAID-induced afferent arteriolar constriction combined with RAAS "
                  "blockade and diuresis is a well-documented cause of acute kidney injury.",
        "management": "Avoid the NSAID; prefer acetaminophen or topical analgesia.",
        "monitoring": ["Serum creatinine / eGFR", "Urine output", "Volume status"],
    },
    {
        "id": "anticoagulant-nsaid",
        "name": "Anticoagulant + NSAID",
        "severity": "major",
        "groups": [{"anticoagulant"}, {"nsaid"}],
        "effect": "Additive bleeding risk: NSAIDs impair platelet function and cause "
                  "direct GI mucosal injury on top of systemic anticoagulation.",
        "management": "Avoid the NSAID; if unavoidable, use the lowest dose for the "
                      "shortest duration with gastroprotection (PPI).",
        "monitoring": ["Hemoglobin / hematocrit", "Signs of GI bleeding", "INR if on warfarin"],
    },
    {
        "id": "anticoagulant-antiplatelet",
        "name": "Anticoagulant + antiplatelet",
        "severity": "major",
        "groups": [{"anticoagulant"}, {"antiplatelet"}],
        "effect": "Combined anticoagulant and antiplatelet therapy substantially increases "
                  "major and intracranial bleeding risk.",
        "management": "Confirm an active indication for both (e.g. recent stent); "
                      "de-escalate to monotherapy as soon as the indication allows.",
        "monitoring": ["Hemoglobin", "Bleeding assessment", "INR if on warfarin"],
    },
    {
        "id": "anticoagulant-serotonergic",
        "name": "Anticoagulant + serotonergic antidepressant",
        "severity": "moderate",
        "groups": [{"anticoagulant"}, {"ssri", "snri"}],
        "effect": "SSRIs and SNRIs deplete platelet serotonin and impair hemostasis, "
                  "increasing bleeding risk on anticoagulation.",
        "management": "Consider gastroprotection; counsel the patient on bleeding signs.",
        "monitoring": ["Hemoglobin", "Signs of bleeding", "INR if on warfarin"],
    },
    {
        "id": "serotonin-syndrome",
        "name": "Multiple serotonergic agents",
        "severity": "major",
        "groups": [SEROTONERGIC, SEROTONERGIC],
        "effect": "Additive serotonergic activity can precipitate serotonin syndrome "
                  "(agitation, hyperthermia, clonus, autonomic instability). Tramadol "
                  "additionally lowers the seizure threshold when combined with SSRIs.",
        "management": "Avoid or minimise overlapping serotonergic agents; if both are "
                      "required, use the lowest doses and counsel on warning signs.",
        "monitoring": [
            "Neuromuscular exam for clonus/hyperreflexia",
            "Temperature and mental status",
        ],
    },
    {
        "id": "maoi-serotonergic",
        "name": "MAO inhibitor + serotonergic agent",
        "severity": "contraindicated",
        "groups": [{"maoi"}, SEROTONERGIC],
        "effect": "Risk of life-threatening serotonin syndrome and hypertensive crisis.",
        "management": "Do not co-administer. Observe the required washout period between "
                      "an MAOI and any serotonergic agent.",
        "monitoring": ["Do not initiate; escalate to the prescriber immediately"],
    },
    {
        "id": "statin-cyp3a4-inhibitor",
        "name": "Statin + CYP3A4 inhibitor",
        "severity": "major",
        "groups": [{"statin"}, {"cyp3a4_inhibitor"}],
        "effect": "Inhibited statin metabolism raises systemic exposure and the risk of "
                  "myopathy and rhabdomyolysis (greatest for simvastatin and lovastatin).",
        "management": "Hold or dose-cap the statin for the duration of the interacting "
                      "course, or switch to pravastatin/rosuvastatin.",
        "monitoring": ["Creatine kinase if muscle pain", "Renal function"],
    },
    {
        "id": "nsaid-corticosteroid",
        "name": "NSAID + systemic corticosteroid",
        "severity": "moderate",
        "groups": [{"nsaid"}, {"corticosteroid"}],
        "effect": "Roughly fourfold increase in upper GI ulceration and bleeding compared "
                  "with either agent alone.",
        "management": "Add gastroprotection (PPI) and use the shortest possible course.",
        "monitoring": ["Signs of GI bleeding", "Hemoglobin"],
    },
    {
        "id": "nsaid-antihypertensive",
        "name": "NSAID + antihypertensive",
        "severity": "moderate",
        "groups": [{"nsaid"}, RAAS_BLOCKERS | {"beta_blocker", "thiazide_diuretic", "loop_diuretic"}],
        "effect": "NSAIDs cause sodium and water retention that blunts antihypertensive "
                  "efficacy and can destabilise heart failure.",
        "management": "Prefer non-NSAID analgesia; recheck blood pressure if an NSAID is started.",
        "monitoring": ["Blood pressure", "Weight / volume status"],
    },
    {
        "id": "opioid-benzodiazepine",
        "name": "Opioid + benzodiazepine",
        "severity": "major",
        "groups": [{"opioid"}, {"benzodiazepine"}],
        "effect": "Additive CNS and respiratory depression; a leading contributor to "
                  "overdose deaths (FDA boxed warning).",
        "management": "Avoid co-prescribing where possible; if unavoidable, use the lowest "
                      "doses and consider take-home naloxone.",
        "monitoring": ["Sedation level", "Respiratory rate", "Oxygen saturation"],
    },
]

# Classes where two concurrent agents constitute therapeutic duplication rather
# than a distinct pharmacological interaction.
DUPLICATE_THERAPY_CLASSES = {
    "ace_inhibitor", "arb", "nsaid", "ssri", "snri", "statin", "anticoagulant",
    "benzodiazepine", "loop_diuretic", "thiazide_diuretic", "beta_blocker",
    "sulfonylurea",
}

SEVERITY_ORDER = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}

_DRUG_PATTERNS = [
    (name, re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE))
    for name in sorted({drug for drugs in DRUG_CLASSES.values() for drug in drugs})
]


def classes_for(drug: str) -> Set[str]:
    return {cls for cls, drugs in DRUG_CLASSES.items() if drug in drugs}


def identify_medications(text: str) -> List[Dict[str, Any]]:
    """Extract recognised ingredients from free text or JSON the agent supplies."""
    if not text:
        return []
    found = []
    for name, pattern in _DRUG_PATTERNS:
        if pattern.search(text):
            found.append({"ingredient": name, "classes": sorted(classes_for(name))})
    return found


def _label(med: Dict[str, Any]) -> str:
    classes = ", ".join(CLASS_LABELS.get(cls, cls) for cls in med["classes"])
    return f"{med['ingredient'].title()} ({classes})"


def _combination_matches(groups: List[Set[str]], combo) -> bool:
    """True if the medications can be assigned one-per-group."""
    return any(
        all(set(med["classes"]) & group for med, group in zip(perm, groups))
        for perm in itertools.permutations(combo)
    )


def find_interactions(medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluate every rule against the identified medications."""
    interactions = []
    for rule in INTERACTION_RULES:
        groups = rule["groups"]
        if len(medications) < len(groups):
            continue
        for combo in itertools.combinations(medications, len(groups)):
            if not _combination_matches(groups, combo):
                continue
            interactions.append({
                "rule_id": rule["id"],
                "interaction": rule["name"],
                "severity": rule["severity"],
                "medications": [_label(med) for med in combo],
                "effect": rule["effect"],
                "management": rule["management"],
                "monitoring": rule["monitoring"],
            })
    interactions.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["rule_id"]))
    return interactions


def find_duplicate_therapy(medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    duplicates = []
    for cls in sorted(DUPLICATE_THERAPY_CLASSES):
        members = [med["ingredient"].title() for med in medications if cls in med["classes"]]
        if len(members) > 1:
            duplicates.append({
                "drug_class": CLASS_LABELS.get(cls, cls),
                "medications": members,
                "concern": f"Two or more {CLASS_LABELS.get(cls, cls)} agents are active "
                           "concurrently; confirm this is intentional.",
            })
    return duplicates


def check_medications(text: str) -> Dict[str, Any]:
    """Full interaction check over whatever medication text the agent supplies."""
    medications = identify_medications(text)
    interactions = find_interactions(medications)
    duplicates = find_duplicate_therapy(medications)

    buckets: Dict[str, List[str]] = {"critical": [], "moderate": [], "minor": []}
    monitoring: List[str] = []
    for item in interactions:
        line = (f"{' + '.join(item['medications'])} — {item['interaction']}: "
                f"{item['effect']} {item['management']}")
        bucket = "critical" if item["severity"] in ("contraindicated", "major") else item["severity"]
        buckets[bucket].append(line)
        for entry in item["monitoring"]:
            if entry not in monitoring:
                monitoring.append(entry)

    return {
        "medications_evaluated": [med["ingredient"] for med in medications],
        "medication_count": len(medications),
        "interactions": interactions,
        "therapeutic_duplication": duplicates,
        "critical_interactions": buckets["critical"],
        "moderate_interactions": buckets["moderate"],
        "minor_interactions": buckets["minor"],
        "monitoring_requirements": monitoring,
        "highest_severity": interactions[0]["severity"] if interactions else "none",
        "coverage_note": (
            "Rule-based screen over a demonstration interaction table. Only the "
            "ingredients listed in medications_evaluated were recognised; any other "
            "text supplied was not assessed. Not a substitute for a licensed clinical "
            "drug interaction database."
        ),
    }


# --- Condition-driven decision support -------------------------------------

CONDITION_PATTERNS = [
    ("heart_failure", r"heart failure|\bchf\b|hfref|hfpef|cardiomyopathy|reduced ejection"),
    ("chronic_kidney_disease", r"chronic kidney|\bckd\b|renal insufficiency|nephropathy|egfr"),
    ("diabetes", r"diabet|\bt2dm\b|\bt1dm\b|hyperglyc|hba1c"),
    ("hypertension", r"hypertens|\bhtn\b|elevated blood pressure"),
    ("coronary_artery_disease", r"coronary artery|\bcad\b|myocardial infarction|angina|ischemic heart"),
    ("atrial_fibrillation", r"atrial fibrillation|\bafib\b|\ba-fib\b"),
    ("copd_asthma", r"\bcopd\b|asthma|emphysema"),
    ("depression", r"depress|major depressive|\bmdd\b"),
]

CONDITION_GUIDANCE = {
    "heart_failure": {
        "recommendations": [
            "Confirm guideline-directed medical therapy: ARNI/ACEi/ARB, beta blocker, "
            "MRA and SGLT2 inhibitor as tolerated",
            "Review volume status and diuretic requirement",
        ],
        "monitoring": ["Daily weights", "Serum potassium and creatinine", "NYHA class"],
    },
    "chronic_kidney_disease": {
        "recommendations": [
            "Renally dose all medications and avoid nephrotoxins including NSAIDs and "
            "iodinated contrast where possible",
            "Assess albuminuria and confirm RAAS blockade is optimised if proteinuric",
        ],
        "monitoring": ["eGFR and creatinine", "Serum potassium", "Urine albumin/creatinine ratio"],
    },
    "diabetes": {
        "recommendations": [
            "Review glycemic target and current agents against the latest ADA standards",
            "Confirm annual retinopathy, foot and nephropathy screening are current",
        ],
        "monitoring": ["HbA1c every 3-6 months", "Fasting glucose", "Lipid panel"],
    },
    "hypertension": {
        "recommendations": [
            "Confirm blood pressure is at target and review adherence before escalating therapy",
            "Reinforce sodium restriction and weight management",
        ],
        "monitoring": ["Home blood pressure log", "Serum electrolytes and creatinine"],
    },
    "coronary_artery_disease": {
        "recommendations": [
            "Confirm secondary prevention: antiplatelet, high-intensity statin and beta blocker",
            "Reassess anginal burden and functional capacity",
        ],
        "monitoring": ["Lipid panel", "Symptom and exercise tolerance review"],
    },
    "atrial_fibrillation": {
        "recommendations": [
            "Calculate CHA2DS2-VASc and confirm anticoagulation is appropriate",
            "Review rate versus rhythm control strategy",
        ],
        "monitoring": ["Heart rate", "Renal function for DOAC dosing", "Bleeding assessment"],
    },
    "copd_asthma": {
        "recommendations": [
            "Verify inhaler technique and adherence before escalating therapy",
            "Confirm influenza and pneumococcal vaccination status",
        ],
        "monitoring": ["Symptom score and exacerbation frequency", "Spirometry"],
    },
    "depression": {
        "recommendations": [
            "Reassess symptom severity with a structured instrument (e.g. PHQ-9)",
            "Review antidepressant tolerability and suicidality risk",
        ],
        "monitoring": ["PHQ-9 at follow-up", "Medication adherence and side effects"],
    },
}

RED_FLAG_PATTERNS = [
    (r"chest pain|chest pressure|chest tightness", "Chest pain — exclude acute coronary syndrome; obtain ECG and troponin"),
    (r"short(ness)? of breath|dyspnea|dyspnoea|respiratory distress", "Dyspnea — assess oxygenation and volume status urgently"),
    (r"syncope|passed out|loss of consciousness|unresponsive", "Syncope or altered consciousness — requires urgent evaluation"),
    (r"altered mental|confus|disorient", "Altered mental status — screen for hypoxia, sepsis, hypoglycemia and stroke"),
    (r"hypotens|systolic (blood pressure )?(of )?[0-8]\d\b|\bshock\b", "Hypotension or shock physiology — immediate escalation"),
    (r"sepsis|septic|fever and|lactate", "Possible sepsis — apply sepsis bundle and obtain lactate and cultures"),
    (r"bleed|hemorrhag|haemorrhag|melena|hematemesis", "Active bleeding — assess hemodynamics and reverse anticoagulation as indicated"),
    (r"suicid|self-harm", "Suicidality — perform an immediate safety assessment"),
    (r"stroke|facial droop|slurred speech|hemipares|weakness on one side", "Possible stroke — activate stroke pathway and time-of-onset assessment"),
    (r"anaphyla|angioedema|throat swelling", "Anaphylaxis or angioedema — secure airway and give epinephrine"),
]

URGENT_RED_FLAGS = {"Chest pain", "Hypotension", "Possible sepsis", "Active bleeding",
                    "Possible stroke", "Anaphylaxis", "Syncope"}


def detect_conditions(text: str) -> List[str]:
    lowered = (text or "").lower()
    return [name for name, pattern in CONDITION_PATTERNS if re.search(pattern, lowered)]


def detect_red_flags(text: str) -> List[str]:
    lowered = (text or "").lower()
    return [message for pattern, message in RED_FLAG_PATTERNS if re.search(pattern, lowered)]


def assess(patient_summary: str, clinical_question: str = "") -> Dict[str, Any]:
    """Condition- and symptom-driven decision support over the supplied context."""
    combined = f"{patient_summary or ''}\n{clinical_question or ''}"
    conditions = detect_conditions(combined)
    red_flags = detect_red_flags(combined)
    medication_findings = check_medications(combined)

    recommendations: List[str] = []
    monitoring: List[str] = []
    for condition in conditions:
        guidance = CONDITION_GUIDANCE[condition]
        recommendations.extend(guidance["recommendations"])
        for entry in guidance["monitoring"]:
            if entry not in monitoring:
                monitoring.append(entry)

    for interaction in medication_findings["interactions"]:
        if interaction["severity"] in ("contraindicated", "major"):
            recommendations.insert(0, (
                f"Address {interaction['interaction']} "
                f"({' + '.join(interaction['medications'])}): {interaction['management']}"
            ))

    if red_flags:
        urgency = "emergent"
    elif any(i["severity"] in ("contraindicated", "major") for i in medication_findings["interactions"]):
        urgency = "urgent"
    else:
        urgency = "routine"

    if not conditions and not red_flags and not recommendations:
        recommendations.append(
            "No recognised chronic condition, red flag or drug interaction was identified "
            "in the supplied context; clinical judgement is required."
        )

    return {
        "conditions_identified": conditions,
        "red_flags": red_flags,
        "urgency_level": urgency,
        "recommendations": recommendations,
        "medication_safety": {
            "medications_evaluated": medication_findings["medications_evaluated"],
            "critical_interactions": medication_findings["critical_interactions"],
            "moderate_interactions": medication_findings["moderate_interactions"],
        },
        "monitoring": monitoring,
        "basis": (
            "Rule-based decision support derived from the supplied patient context. "
            "Findings reflect only what was present in that text and are not a "
            "certified clinical decision support system."
        ),
    }
