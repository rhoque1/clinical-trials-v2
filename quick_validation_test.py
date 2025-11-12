"""
Quick validation test with updated ground truth
Tests 3 cases to verify:
1. Updated ground truth trials are found
2. Unicode encoding is fixed
3. Both Control and RAG phases work
"""
import os
import sys

# Fix UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
from evaluation.rag_evaluator import RAGEvaluator


def run_validation():
    """Run quick validation on 3 test cases"""

    print("="*80)
    print("VALIDATION TEST: Updated Ground Truth + Unicode Fix")
    print("="*80)

    # Load test cases
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        test_data = json.load(f)

    # Select 3 diverse cases
    test_cases = [
        test_data["test_cases"][0],   # cervical_pdl1_standard (was 0% before)
        test_data["test_cases"][3],   # melanoma_braf_v600e (was 0% before)
        test_data["test_cases"][7]    # prostate_brca2_crpc (was 0% before)
    ]

    print(f"\n[INFO] Testing {len(test_cases)} cases:")
    for tc in test_cases:
        print(f"  - {tc['case_id']}")

    configs = [
        {"name": "Control", "use_rag": False},
        {"name": "RAG-Enhanced", "use_rag": True}
    ]

    for config in configs:
        print(f"\n{'='*80}")
        print(f"TESTING: {config['name']}")
        print(f"{'='*80}")

        evaluator = RAGEvaluator(use_rag=config["use_rag"])

        for test_case in test_cases:
            case_id = test_case["case_id"]
            print(f"\n[TEST] {case_id}")

            try:
                result = evaluator.evaluate_test_case(test_case)
                metrics = result["metrics"]

                print(f"  [OK] Completed successfully")
                print(f"  Precision@1: {metrics['precision@1']:.1%}")
                print(f"  Precision@5: {metrics['precision@5']:.1%}")
                print(f"  MRR: {metrics['mrr']:.3f}")
                print(f"  Ground truth found: {metrics['ground_truth_found']}/{len(test_case['ground_truth_trials'])}")

                if metrics['ground_truth_found'] > 0:
                    print(f"  [+] SUCCESS: Found at least one ground truth trial!")
                else:
                    print(f"  [!]  WARNING: No ground truth trials found")

            except Exception as e:
                error_msg = str(e)[:150].encode('ascii', 'replace').decode('ascii')
                print(f"  [ERROR] {error_msg}")
                print(f"  [X] FAILED - Unicode or other error")

    print(f"\n{'='*80}")
    print("VALIDATION COMPLETE")
    print("If all tests passed, ready to run full Phase 1 experiment")
    print("="*80)


if __name__ == "__main__":
    run_validation()
