"""
Quick validation test: Check if curated ground truth now gives non-zero accuracy
Tests only the 5 curated cases
"""
import fix_encoding_global
import asyncio
import json
from pathlib import Path


async def test_single_case(case_id: str):
    """Test a single case to see if ground truth is now found"""

    print(f"\n{'='*80}")
    print(f"TESTING: {case_id}")
    print(f"{'='*80}")

    # Load patient profile
    profile_path = Path(f"evaluation/sample_profiles/{case_id}.json")
    with open(profile_path, 'r', encoding='utf-8') as f:
        patient_profile = json.load(f)

    # Load ground truth
    with open("evaluation/test_cases.json", 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        test_case = next((tc for tc in test_data["test_cases"] if tc["case_id"] == case_id), None)

    if not test_case:
        print(f"[ERROR] Test case not found")
        return None

    ground_truth_ncts = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]
    print(f"\n[GROUND TRUTH] {ground_truth_ncts}")

    # Run trial discovery
    from agents.workflow_engine import WorkflowEngine
    from agents.orchestrator import WorkflowMode

    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

    print(f"\n[RUNNING] Trial discovery...")
    discovery_result = await engine.run_trial_discovery(patient_profile)

    if not discovery_result.get("success"):
        print(f"[ERROR] Discovery failed")
        return None

    ranked_trials = discovery_result.get("ranked_trials", [])
    print(f"[FOUND] {len(ranked_trials)} trials")

    # Check if ground truth appears
    ranked_ncts = [t.get("nct_id") for t in ranked_trials]

    found_in_top10 = []
    for gt_nct in ground_truth_ncts:
        if gt_nct in ranked_ncts[:10]:
            rank = ranked_ncts.index(gt_nct) + 1
            found_in_top10.append((gt_nct, rank))

    # Calculate metrics
    precision_at_3 = sum(1 for gt in ground_truth_ncts if gt in ranked_ncts[:3]) / len(ground_truth_ncts)
    precision_at_5 = sum(1 for gt in ground_truth_ncts if gt in ranked_ncts[:5]) / len(ground_truth_ncts)

    print(f"\n[RESULTS]")
    print(f"  Precision@3: {precision_at_3:.1%}")
    print(f"  Precision@5: {precision_at_5:.1%}")
    print(f"  Found in top 10: {len(found_in_top10)}/{len(ground_truth_ncts)}")

    if found_in_top10:
        print(f"\n  Ground truth rankings:")
        for nct, rank in found_in_top10:
            print(f"    {nct} -> Rank #{rank}")
    else:
        print(f"\n  ⚠️ WARNING: Ground truth not found in top 10!")

    print(f"\n  Top 5 trials retrieved:")
    for i, trial in enumerate(ranked_trials[:5], 1):
        nct = trial.get("nct_id")
        is_gt = "✓ GROUND TRUTH" if nct in ground_truth_ncts else ""
        print(f"    {i}. {nct} {is_gt}")

    return {
        "case_id": case_id,
        "precision@3": precision_at_3,
        "precision@5": precision_at_5,
        "found_count": len(found_in_top10)
    }


async def main():
    """Test all 5 curated cases"""

    print("\n" + "="*80)
    print("VALIDATION TEST: Curated Ground Truth")
    print("="*80)
    print("\nTesting 5 cases with newly curated ground truth...")
    print("Expected: Non-zero accuracy (ground truth should now be found)\n")

    test_cases = [
        "cervical_pdl1_standard",
        "lung_egfr_exon19",
        "breast_her2_brca",
        "colorectal_msi_high",
        "melanoma_braf_v600e"
    ]

    results = []

    for case_id in test_cases:
        try:
            result = await test_single_case(case_id)
            if result:
                results.append(result)

            # Delay between cases
            await asyncio.sleep(2)

        except Exception as e:
            print(f"\n[ERROR] Failed to test {case_id}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Summary
    if results:
        avg_p3 = sum(r["precision@3"] for r in results) / len(results)
        avg_p5 = sum(r["precision@5"] for r in results) / len(results)

        print(f"\n\n{'='*80}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"\nCases tested: {len(results)}/{len(test_cases)}")
        print(f"\nAverage Metrics:")
        print(f"  Precision@3: {avg_p3:.1%}")
        print(f"  Precision@5: {avg_p5:.1%}")

        if avg_p3 > 0:
            print(f"\n✓ SUCCESS: Ground truth is now found in search results!")
            print(f"✓ Evaluation framework is working correctly")
            print(f"\n[NEXT STEP] Run full Phase 1 experiment (RAG vs No-RAG)")
        else:
            print(f"\n⚠️ WARNING: Ground truth still not found")
            print(f"⚠️ May need additional curation")


if __name__ == "__main__":
    asyncio.run(main())
