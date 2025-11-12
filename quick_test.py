"""
Quick Sanity Test - Verify evaluation framework works
Tests 2 cases only for rapid validation
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode


async def quick_test():
    """Test system with 2 test cases to verify it works"""

    print("="*70)
    print("QUICK SANITY TEST")
    print("="*70)
    print("\nTesting evaluation framework with 2 test cases...")
    print("This should take ~2-3 minutes\n")

    # Load test cases
    with open("evaluation/test_cases.json", 'r') as f:
        data = json.load(f)
        test_cases = data["test_cases"][:2]  # Only first 2

    print(f"Test cases: {[tc['case_id'] for tc in test_cases]}\n")

    results = []

    for test_case in test_cases:
        case_id = test_case["case_id"]
        print(f"\n{'='*70}")
        print(f"Testing: {case_id}")
        print(f"{'='*70}")

        try:
            # Load patient profile
            profile_path = Path(f"evaluation/sample_profiles/{case_id}.json")
            with open(profile_path, 'r') as f:
                patient_profile = json.load(f)

            # Create engine
            engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

            # Run trial discovery
            print(f"\n[1/2] Running trial discovery...")
            discovery_result = await engine.run_trial_discovery(patient_profile)

            if not discovery_result.get("success"):
                raise Exception(f"Discovery failed: {discovery_result.get('error')}")

            print(f"[+] Found {len(discovery_result.get('ranked_trials', []))} trials")

            # Run knowledge enhancement (with RAG)
            print(f"[2/2] Running knowledge enhancement with RAG...")
            enhancement_result = await engine.run_knowledge_enhancement(
                patient_profile,
                discovery_result['ranked_trials']
            )

            if not enhancement_result.get("success"):
                raise Exception(f"Enhancement failed: {enhancement_result.get('error')}")

            final_trials = enhancement_result['ranked_trials']
            print(f"[+] Re-ranked {len(final_trials)} trials")

            # Check if ground truth in top 5
            ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]
            top_5_nct_ids = [t.get("nct_id") for t in final_trials[:5]]

            hits = [nct for nct in ground_truth_nct_ids if nct in top_5_nct_ids]

            print(f"\n[RESULTS]")
            print(f"  Ground truth trials: {ground_truth_nct_ids}")
            print(f"  Top 5: {top_5_nct_ids}")
            print(f"  Hits in top 5: {len(hits)}/{len(ground_truth_nct_ids)}")

            if hits:
                print(f"  [+] SUCCESS - Found ground truth in top 5")
            else:
                print(f"  [!] Ground truth NOT in top 5")

            results.append({
                "case_id": case_id,
                "success": True,
                "hits": len(hits),
                "ground_truth_count": len(ground_truth_nct_ids)
            })

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "case_id": case_id,
                "success": False,
                "error": str(e)
            })

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")

    successful = [r for r in results if r.get("success")]
    print(f"\nCases tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")

    if successful:
        total_hits = sum(r.get("hits", 0) for r in successful)
        total_gt = sum(r.get("ground_truth_count", 0) for r in successful)
        print(f"\nGround truth found: {total_hits}/{total_gt}")
        print(f"\n[OK] SANITY TEST PASSED - System is functional!")
        print(f"\nReady to run full experiments.")
        return True
    else:
        print(f"\n[FAIL] SANITY TEST FAILED - Fix issues before running full experiment")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
