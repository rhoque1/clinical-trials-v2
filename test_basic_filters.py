"""
Test script for apply_basic_filters() method
"""
from tools.keyword_baseline import KeywordBaseline
from tools.clinical_trials_api import search_clinical_trials_targeted

# Test patient profile - 40 year old female
test_patient = {
    "demographics": {
        "age": 40,
        "sex": "Female",
        "ecog": 1
    },
    "clinical_features": {
        "diagnosis": "Cervical Squamous Cell Carcinoma",
        "stage": "IIIB",
        "histology": "Squamous Cell Carcinoma"
    },
    "biomarkers": {
        "PIK3CA": "E545K mutation",
        "TP53": "R273H mutation",
        "PD-L1": "15% CPS",
        "HPV": "Type 16 positive",
        "MSI": "MSS"
    },
    "treatment_history": {
        "prior_treatments": ["Cisplatin-based chemoradiation"],
        "current_status": "Post-treatment surveillance"
    },
    "search_terms": ["cervical cancer", "squamous cell", "PD-L1 positive"]
}

# Initialize baseline
baseline = KeywordBaseline(api_client=search_clinical_trials_targeted)

# Step 1: Extract keywords
keywords = baseline.extract_keywords(test_patient)

# Step 2: Search trials
print("Searching for trials...")
trials = baseline.search_trials(keywords, max_results=15)
print(f"Found {len(trials)} trials before filtering\n")

# Step 3: Apply basic filters
print("=" * 50)
print("Applying basic filters (age=40, sex=Female)")
print("=" * 50)
filtered_trials = baseline.apply_basic_filters(test_patient, trials)

print(f"\n{len(filtered_trials)} trials passed basic filters")
print(f"{len(trials) - len(filtered_trials)} trials filtered out\n")

# Show first 5 filtered trials
for i, trial in enumerate(filtered_trials[:5], 1):
    eligibility = trial.get("eligibility", {})
    print(f"{i}. {trial['nct_id']}")
    print(f"   Title: {trial['title'][:70]}...")
    print(f"   Age: {eligibility.get('min_age')} - {eligibility.get('max_age')}")
    print(f"   Sex: {eligibility.get('gender')}")
    print()
