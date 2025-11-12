"""
Automatically update test_cases.json with active replacement trials
Selection criteria:
1. Prefer Phase 2/3 over Phase 1
2. Prefer RECRUITING > NOT_YET_RECRUITING > ACTIVE_NOT_RECRUITING
3. Avoid N/A phase (observational studies) unless no other option
4. Match conditions to patient case
"""

import json
from typing import List, Dict, Tuple

def score_candidate(candidate: Dict, case_cancer_type: str) -> Tuple[int, Dict]:
    """
    Score a candidate trial based on quality criteria
    Returns (score, candidate) where higher score is better
    """
    score = 0

    # Phase scoring (higher phase = more established)
    phases = candidate.get("phase", [])
    if "PHASE3" in phases:
        score += 100
    elif "PHASE2" in phases or any("PHASE2" in p for p in phases):
        score += 80
    elif "PHASE1" in phases:
        score += 40
    else:  # N/A or missing
        score += 10  # Lowest priority for observational

    # Status scoring (recruiting is best for enrollment)
    status = candidate.get("status", "")
    if status == "RECRUITING":
        score += 30
    elif status == "NOT_YET_RECRUITING":
        score += 20
    elif status == "ACTIVE_NOT_RECRUITING":
        score += 10

    # Condition matching (prefer trials for same cancer type)
    conditions_str = " ".join(candidate.get("conditions", [])).lower()
    if case_cancer_type.lower() in conditions_str:
        score += 50

    return (score, candidate)

def extract_cancer_type(case_id: str) -> str:
    """Extract main cancer type from case ID"""
    cancer_types = {
        "cervical": "cervical",
        "lung": "lung",
        "breast": "breast",
        "colorectal": "colorectal",
        "melanoma": "melanoma",
        "prostate": "prostate",
        "ovarian": "ovarian",
        "gastric": "gastric",
        "hnscc": "head and neck",
        "rcc": "renal",
        "hcc": "hepatocellular",
        "bladder": "bladder",
        "pancreatic": "pancreatic",
        "endometrial": "endometrial",
        "cholangiocarcinoma": "cholangiocarcinoma",
        "glioblastoma": "glioblastoma"
    }

    for key, value in cancer_types.items():
        if key in case_id.lower():
            return value
    return "cancer"

def select_best_replacement(candidates: List[Dict], case_id: str) -> Dict:
    """Select the best replacement trial from candidates"""
    cancer_type = extract_cancer_type(case_id)

    # Score all candidates
    scored = [score_candidate(c, cancer_type) for c in candidates]

    # Sort by score (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return best candidate
    return scored[0][1] if scored else candidates[0]

def create_new_ground_truth_entry(candidate: Dict, original: Dict) -> Dict:
    """Create a new ground truth entry from a candidate trial"""
    # Extract phase for rationale
    phases = candidate.get("phase", ["Unknown"])
    phase_str = ", ".join([p.replace("PHASE", "Phase ") for p in phases if p != "NA"])
    if not phase_str:
        phase_str = "Active trial"

    # Shorten title if too long
    title = candidate.get("title", "")
    if len(title) > 100:
        title = title[:97] + "..."

    return {
        "nct_id": candidate["nct_id"],
        "trial_name": title,
        "rationale": f"{phase_str}, {candidate['status'].replace('_', ' ').lower()}",
        "expected_rank": original.get("expected_rank", "top5"),
        "confidence": "medium"  # Lower confidence for replacements
    }

def update_test_cases():
    """Main function to update test_cases.json with active trials"""

    # Load files
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        test_data = json.load(f)

    with open("evaluation/replacement_trials_recommendations.json", "r", encoding='utf-8') as f:
        recommendations = json.load(f)

    # Create lookup dict for recommendations
    rec_dict = {rec["case_id"]: rec for rec in recommendations}

    print("="*80)
    print("UPDATING TEST CASES WITH ACTIVE TRIALS")
    print("="*80)

    total_replacements = 0
    cases_updated = 0

    # Process each test case
    for case in test_data["test_cases"]:
        case_id = case["case_id"]

        # Check if this case has recommendations
        if case_id not in rec_dict:
            print(f"\n[SKIP] {case_id} - No replacements needed")
            continue

        rec = rec_dict[case_id]
        completed_ncts = {trial["nct_id"] for trial in rec["completed_trials"]}

        if not completed_ncts:
            print(f"\n[SKIP] {case_id} - No completed trials")
            continue

        print(f"\n{'='*80}")
        print(f"Case: {case_id}")
        print(f"{'='*80}")

        # Process ground truth trials
        new_ground_truth = []
        replacements_made = 0

        for gt_trial in case["ground_truth_trials"]:
            nct_id = gt_trial["nct_id"]

            if nct_id in completed_ncts:
                # This trial needs replacement
                print(f"\n  [REPLACE] {nct_id} ({gt_trial['trial_name']})")
                print(f"            Status: COMPLETED")

                # Select best candidate
                best_candidate = select_best_replacement(rec["candidates"], case_id)

                # Create new ground truth entry
                new_trial = create_new_ground_truth_entry(best_candidate, gt_trial)
                new_ground_truth.append(new_trial)

                print(f"  [NEW]     {new_trial['nct_id']}")
                # Sanitize for Windows console
                title_safe = new_trial['trial_name'][:80].encode('ascii', 'replace').decode('ascii')
                rationale_safe = new_trial['rationale'].encode('ascii', 'replace').decode('ascii')
                print(f"            Title: {title_safe}")
                print(f"            Rationale: {rationale_safe}")

                replacements_made += 1
                total_replacements += 1
            else:
                # Keep original trial (still active)
                print(f"\n  [KEEP]    {nct_id} ({gt_trial['trial_name']})")
                new_ground_truth.append(gt_trial)

        # Update case with new ground truth
        case["ground_truth_trials"] = new_ground_truth

        if replacements_made > 0:
            cases_updated += 1
            print(f"\n  [OK] Made {replacements_made} replacement(s)")

    # Save updated test cases
    output_file = "evaluation/test_cases.json"
    backup_file = "evaluation/test_cases_BACKUP_original.json"

    # Create backup of original
    with open(backup_file, "w", encoding='utf-8') as f:
        with open(output_file, "r", encoding='utf-8') as orig:
            f.write(orig.read())

    print(f"\n{'='*80}")
    print(f"[BACKUP] Original saved to: {backup_file}")

    # Write updated test cases
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"[UPDATED] New test cases saved to: {output_file}")
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Cases updated: {cases_updated}/20")
    print(f"Total replacements: {total_replacements}")
    print(f"\nGround truth now uses active trials only.")
    print(f"Next step: Re-run Phase 1 experiment to validate improvements")
    print(f"{'='*80}")

if __name__ == "__main__":
    update_test_cases()
