"""
Complete end-to-end test of keyword baseline matcher
"""
import json
from tools.keyword_baseline import KeywordBaseline
from tools.clinical_trials_api import search_clinical_trials_targeted

# Test patient profile (cervical cancer case from your spec)
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

# Initialize baseline matcher
print("Initializing Keyword Baseline Matcher...")
baseline = KeywordBaseline(api_client=search_clinical_trials_targeted)

# Run complete matching pipeline
print("Running matching pipeline...\n")
results = baseline.match_patient(test_patient)

# Display results
print("=" * 70)
print("KEYWORD BASELINE RESULTS")
print("=" * 70)

print(f"\nMethod: {results['method']}")
print(f"\nKeywords used: {', '.join(results['metadata']['keywords_used'][:5])}")
print(f"  (showing first 5 of {len(results['metadata']['keywords_used'])} total)")

print(f"\nTrials searched: {results['metadata']['trials_searched']}")
print(f"Trials after filtering: {results['metadata']['trials_filtered']}")

print("\n" + "-" * 70)
print("TOP 5 MATCHED TRIALS")
print("-" * 70)

for i, trial in enumerate(results['top_trials'], 1):
    print(f"\n{i}. {trial['nct_id']} (Score: {trial['score']})")
    print(f"   {trial['title']}")
    print(f"   {trial['reasoning']}")

# Save results to file
output_file = "output/keyword_baseline_results.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 70)
print(f"Results saved to: {output_file}")
