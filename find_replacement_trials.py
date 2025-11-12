"""
Find active replacement trials for completed ground truth trials
"""

import json
import requests
import time
from typing import List, Dict

def get_trial_status(nct_id: str) -> str:
    """Get the status of a trial"""
    try:
        url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            trial_data = response.json()
            return trial_data["protocolSection"]["statusModule"]["overallStatus"]
        return "NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"

def search_active_trials(cancer_type: str, keywords: List[str], max_results: int = 20) -> List[Dict]:
    """Search for active trials matching cancer type and keywords"""

    # Build search query
    query_parts = [cancer_type] + keywords
    query = " ".join(query_parts)

    try:
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": query,
            "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,NOT_YET_RECRUITING",
            "pageSize": max_results,
            "format": "json"
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            trials = []

            for study in data.get("studies", []):
                try:
                    protocol = study["protocolSection"]
                    id_module = protocol["identificationModule"]
                    status_module = protocol["statusModule"]
                    design_module = protocol.get("designModule", {})

                    trial_info = {
                        "nct_id": id_module["nctId"],
                        "title": id_module.get("briefTitle", ""),
                        "status": status_module["overallStatus"],
                        "phase": design_module.get("phases", ["N/A"]),
                        "conditions": protocol.get("conditionsModule", {}).get("conditions", [])
                    }
                    trials.append(trial_info)
                except KeyError:
                    continue

            return trials
        return []
    except Exception as e:
        print(f"    [ERROR] Search failed: {str(e)}")
        return []

def find_replacements():
    """Find replacement trials for all completed ground truth trials"""

    # Load test cases
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        data = json.load(f)

    print("="*80)
    print("FINDING ACTIVE REPLACEMENT TRIALS")
    print("="*80)

    all_replacements = []

    for case in data["test_cases"]:
        case_id = case["case_id"]
        patient_summary = case["patient_summary"]

        print(f"\n{'='*80}")
        print(f"Case: {case_id}")
        print(f"Patient: {patient_summary[:100]}...")
        print(f"{'='*80}")

        needs_replacement = []

        # Check each ground truth trial
        for gt in case["ground_truth_trials"]:
            nct_id = gt["nct_id"]
            trial_name = gt["trial_name"]
            status = get_trial_status(nct_id)

            if status not in ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING"]:
                print(f"\n  [!] {nct_id} ({trial_name}) - Status: {status}")
                print(f"      Needs replacement")
                needs_replacement.append(gt)
            else:
                print(f"\n  [+] {nct_id} ({trial_name}) - Status: {status}")
                print(f"      Still active, no replacement needed")

        # Find replacements if needed
        if needs_replacement:
            print(f"\n  [SEARCH] Looking for {len(needs_replacement)} replacement(s)...")

            # Extract search terms from patient summary
            keywords = []
            summary_lower = patient_summary.lower()

            # Extract cancer type
            cancer_types = {
                "cervical": "cervical cancer",
                "lung": "lung cancer",
                "breast": "breast cancer",
                "colorectal": "colorectal cancer",
                "melanoma": "melanoma",
                "pancreatic": "pancreatic cancer",
                "ovarian": "ovarian cancer",
                "prostate": "prostate cancer",
                "gastric": "gastric cancer",
                "bladder": "bladder cancer",
                "glioblastoma": "glioblastoma",
                "cholangiocarcinoma": "cholangiocarcinoma",
                "endometrial": "endometrial cancer",
                "renal": "renal cell carcinoma"
            }

            cancer_type = None
            for key, value in cancer_types.items():
                if key in summary_lower:
                    cancer_type = value
                    break

            if not cancer_type:
                cancer_type = "cancer"

            # Extract key biomarkers/features
            biomarker_terms = []
            if "pd-l1" in summary_lower or "pdl1" in summary_lower:
                biomarker_terms.append("PD-L1")
            if "egfr" in summary_lower:
                biomarker_terms.append("EGFR")
            if "her2" in summary_lower:
                biomarker_terms.append("HER2")
            if "braf" in summary_lower:
                biomarker_terms.append("BRAF")
            if "msi" in summary_lower or "microsatellite" in summary_lower:
                biomarker_terms.append("MSI")
            if "alk" in summary_lower:
                biomarker_terms.append("ALK")
            if "ros1" in summary_lower:
                biomarker_terms.append("ROS1")
            if "kras" in summary_lower:
                biomarker_terms.append("KRAS")
            if "brca" in summary_lower:
                biomarker_terms.append("BRCA")

            # Search for active trials
            active_trials = search_active_trials(cancer_type, biomarker_terms, max_results=20)

            print(f"\n  [RESULTS] Found {len(active_trials)} active trials")

            if active_trials:
                print(f"\n  Top 5 candidate replacements:")
                for i, trial in enumerate(active_trials[:5], 1):
                    # Sanitize title for Windows console
                    title = trial['title'][:80].encode('ascii', 'replace').decode('ascii')
                    print(f"\n    {i}. {trial['nct_id']}")
                    print(f"       Title: {title}...")
                    print(f"       Status: {trial['status']}")
                    print(f"       Phase: {', '.join(trial['phase'])}")

                # Store recommendations
                all_replacements.append({
                    "case_id": case_id,
                    "completed_trials": needs_replacement,
                    "candidates": active_trials[:5]
                })
            else:
                print(f"  [WARNING] No active trials found with these criteria")

        time.sleep(1)  # Rate limiting

    # Save recommendations
    output_file = "evaluation/replacement_trials_recommendations.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(all_replacements, f, indent=2)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Cases needing replacements: {len(all_replacements)}")
    print(f"Recommendations saved to: {output_file}")
    print(f"\nNext step: Review recommendations and update evaluation/test_cases.json")

if __name__ == "__main__":
    find_replacements()
