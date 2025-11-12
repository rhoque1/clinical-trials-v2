"""
Test script for search_trials() method
"""
from tools.keyword_baseline import KeywordBaseline
from tools.clinical_trials_api import search_clinical_trials_targeted

# Test patient profile
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

# Initialize baseline with API client
baseline = KeywordBaseline(api_client=search_clinical_trials_targeted)

# Step 1: Extract keywords
keywords = baseline.extract_keywords(test_patient)
print("Step 1: Extracted Keywords")
print("-" * 50)
print(", ".join(keywords[:5]))  # Show first 5

# Step 2: Search trials
print("\n" + "=" * 50)
print("Step 2: Searching Clinical Trials...")
print("=" * 50)
trials = baseline.search_trials(keywords, max_results=10)

print(f"\nFound {len(trials)} trials\n")

# Display first 3 trials
for i, trial in enumerate(trials[:3], 1):
    print(f"\n{i}. {trial['nct_id']}")
    print(f"   Title: {trial['title'][:80]}...")
    print(f"   Status: {trial['status']}")
    print(f"   Phase: {trial['phase']}")
    print(f"   Conditions: {', '.join(trial['conditions'][:2])}")
    if trial.get('full_text'):
        print(f"   Full text length: {len(trial['full_text'])} chars")
