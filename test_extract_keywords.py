"""
Test script for extract_keywords() method
"""
from tools.keyword_baseline import KeywordBaseline
from tools.clinical_trials_api import search_clinical_trials_targeted

# Mock patient profile (based on your spec)
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

# Test keyword extraction
baseline = KeywordBaseline(api_client=None)  # We don't need API for this test
keywords = baseline.extract_keywords(test_patient)

print("Extracted Keywords:")
print("-" * 50)
for i, keyword in enumerate(keywords, 1):
    print(f"{i}. {keyword}")

print("\n" + "=" * 50)
print(f"Total keywords extracted: {len(keywords)}")
