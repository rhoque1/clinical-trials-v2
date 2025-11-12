"""
Diagnostic script to check why ground truth trials aren't being found
"""

import sys
import json
import requests
from pathlib import Path

def check_ground_truth():
    """Check if ground truth NCT IDs exist and are active"""

    # Load test cases
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        data = json.load(f)

    print("="*80)
    print("GROUND TRUTH VALIDATION")
    print("="*80)

    total_trials = 0
    found_trials = 0
    active_trials = 0

    for case in data["test_cases"][:5]:  # Check first 5 cases
        case_id = case["case_id"]
        print(f"\n{'='*80}")
        print(f"Case: {case_id}")
        print(f"{'='*80}")

        for gt in case["ground_truth_trials"]:
            nct_id = gt["nct_id"]
            trial_name = gt["trial_name"]
            total_trials += 1

            print(f"\n  Checking: {nct_id} ({trial_name})")

            # Try to fetch the trial directly from ClinicalTrials.gov API
            try:
                url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    trial_data = response.json()
                    found_trials += 1

                    # Extract status
                    try:
                        status = trial_data["protocolSection"]["statusModule"]["overallStatus"]
                    except KeyError:
                        status = "UNKNOWN"

                    print(f"    [+] FOUND in API")
                    print(f"    Status: {status}")

                    if status in ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"]:
                        active_trials += 1
                        print(f"    [+] ACTIVE - Should be discoverable")
                    else:
                        print(f"    [!] NOT ACTIVE - Won't appear in search results")
                        print(f"        Reason: Status '{status}' excluded from API queries")
                else:
                    print(f"    [X] NOT FOUND in API (HTTP {response.status_code})")
                    print(f"        Possible reasons:")
                    print(f"        - Trial completed/terminated")
                    print(f"        - NCT ID invalid")
                    print(f"        - API access issue")

            except Exception as e:
                print(f"    [X] ERROR: {str(e)}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total ground truth trials checked: {total_trials}")
    print(f"Found in API: {found_trials}/{total_trials} ({100*found_trials/total_trials:.1f}%)")
    print(f"Active/Recruiting: {active_trials}/{total_trials} ({100*active_trials/total_trials:.1f}%)")

    if active_trials == 0:
        print(f"\n[CRITICAL] NO active ground truth trials found!")
        print("This explains 0% accuracy - ground truth trials are not in search results.")
        print("\nOptions:")
        print("1. Update ground truth with currently active trials")
        print("2. Change API queries to include completed trials (not recommended)")
        print("3. Use synthetic test cases with guaranteed active trials")
    elif active_trials < total_trials * 0.5:
        print(f"\n[WARNING] Only {100*active_trials/total_trials:.1f}% of ground truth trials are active")
        print("Test set needs updating with current trials.")
    else:
        print(f"\n[OK] Most ground truth trials are active")
        print("Issue may be with ranking/retrieval logic, not ground truth validity")

if __name__ == "__main__":
    check_ground_truth()
