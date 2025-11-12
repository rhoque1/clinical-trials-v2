"""
Simple RAG test runner - directly uses workflow_engine
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode


async def test_single_case(case_id: str, use_rag: bool):
    """Test one case with or without RAG"""

    # Load patient profile
    profile_path = Path(f"evaluation/sample_profiles/{case_id}.json")
    with open(profile_path, 'r') as f:
        patient_profile = json.load(f)

    # Load ground truth
    with open("evaluation/test_cases.json", 'r') as f:
        test_cases = json.load(f)["test_cases"]

    test_case = next((tc for tc in test_cases if tc["case_id"] == case_id), None)
    ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]

    print(f"\n{'='*70}")
    print(f"Case: {case_id}")
    print(f"RAG: {'ENABLED' if use_rag else 'DISABLED'}")
    print(f"{'='*70}")

    # Create engine
    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

    # Temporarily modify the RAG flag
    from state_machines import knowledge_enhanced_ranking
    original_init = knowledge_enhanced_ranking.KnowledgeEnhancedRankingMachine.__init__

    def patched_init(self):
        original_init(self, disable_rag_for_experiment=(not use_rag))

    knowledge_enhanced_ranking.KnowledgeEnhancedRankingMachine.__init__ = patched_init

    try:
        # Run discovery
        print("Running trial discovery...")
        discovery_result = await engine.run_trial_discovery(patient_profile)

        # Run enhancement
        print("Running knowledge enhancement...")
        enhancement_result = await engine.run_knowledge_enhancement(
            patient_profile,
            discovery_result['ranked_trials']
        )

        # Get results
        final_trials = enhancement_result['ranked_trials']
        ranked_nct_ids = [t.get("nct_id") for t in final_trials]

        # Calculate metrics
        top_3 = ranked_nct_ids[:3]
        top_5 = ranked_nct_ids[:5]

        hits_3 = sum(1 for nct in ground_truth_nct_ids if nct in top_3)
        hits_5 = sum(1 for nct in ground_truth_nct_ids if nct in top_5)

        p3 = hits_3 / len(ground_truth_nct_ids) if ground_truth_nct_ids else 0
        p5 = hits_5 / len(ground_truth_nct_ids) if ground_truth_nct_ids else 0

        # Find first hit
        first_hit_rank = None
        for rank, nct_id in enumerate(ranked_nct_ids, 1):
            if nct_id in ground_truth_nct_ids:
                first_hit_rank = rank
                break

        mrr = 1.0 / first_hit_rank if first_hit_rank else 0.0

        print(f"\n[RESULTS]")
        print(f"  Precision@3: {p3:.1%}")
        print(f"  Precision@5: {p5:.1%}")
        print(f"  MRR: {mrr:.3f}")
        print(f"  First hit rank: {first_hit_rank}")

        print(f"\n  Top 5 trials:")
        for i, trial in enumerate(final_trials[:5], 1):
            nct_id = trial.get("nct_id", "N/A")
            score = trial.get("score", 0)
            is_gt = "[GROUND TRUTH]" if nct_id in ground_truth_nct_ids else ""
            print(f"    {i}. {nct_id} (score: {score:.1f}) {is_gt}")

        return {
            "case_id": case_id,
            "use_rag": use_rag,
            "metrics": {
                "precision@3": p3,
                "precision@5": p5,
                "mrr": mrr,
                "first_hit_rank": first_hit_rank
            },
            "top_5": [(t.get("nct_id"), t.get("score")) for t in final_trials[:5]],
            "success": True
        }

    finally:
        # Restore original
        knowledge_enhanced_ranking.KnowledgeEnhancedRankingMachine.__init__ = original_init


async def main():
    """Run all tests"""

    test_case_ids = [
        "cervical_pdl1_standard",
        "lung_egfr_exon19",
        "breast_her2_brca",
        "colorectal_msi_high",
        "melanoma_braf_v600e"
    ]

    print("\n" + "="*70)
    print("RAG EFFECTIVENESS EXPERIMENT")
    print("="*70)
    print(f"Test cases: {len(test_case_ids)}")
    print(f"Conditions: Control (no RAG) vs Treatment (with RAG)")
    print("="*70)

    all_results = []

    # Test without RAG first
    print("\n\n" + "="*70)
    print("PHASE 1: CONTROL (NO RAG)")
    print("="*70)

    control_results = []
    for case_id in test_case_ids:
        result = await test_single_case(case_id, use_rag=False)
        control_results.append(result)
        all_results.append(result)
        await asyncio.sleep(2)

    # Test with RAG
    print("\n\n" + "="*70)
    print("PHASE 2: TREATMENT (WITH RAG)")
    print("="*70)

    rag_results = []
    for case_id in test_case_ids:
        result = await test_single_case(case_id, use_rag=True)
        rag_results.append(result)
        all_results.append(result)
        await asyncio.sleep(2)

    # Calculate aggregates
    import numpy as np

    control_p3 = np.mean([r["metrics"]["precision@3"] for r in control_results])
    rag_p3 = np.mean([r["metrics"]["precision@3"] for r in rag_results])

    control_mrr = np.mean([r["metrics"]["mrr"] for r in control_results])
    rag_mrr = np.mean([r["metrics"]["mrr"] for r in rag_results])

    improvement_p3 = ((rag_p3 - control_p3) / control_p3 * 100) if control_p3 > 0 else 0
    improvement_mrr = ((rag_mrr - control_mrr) / control_mrr * 100) if control_mrr > 0 else 0

    # Print comparison
    print("\n\n" + "="*70)
    print("FINAL COMPARISON")
    print("="*70)
    print(f"\n{'Metric':<20} {'Control':<15} {'With RAG':<15} {'Change':<15}")
    print("-"*70)
    print(f"{'Precision@3':<20} {control_p3:<15.1%} {rag_p3:<15.1%} {improvement_p3:+.1f}%")
    print(f"{'MRR':<20} {control_mrr:<15.3f} {rag_mrr:<15.3f} {improvement_mrr:+.1f}%")

    print(f"\n{'='*70}")
    print("CONCLUSION")
    print("="*70)

    if rag_p3 > control_p3 + 0.05:
        print(f"[POSITIVE] RAG improves accuracy by {improvement_p3:.1f}%")
        print(f"[RECOMMENDATION] KEEP RAG in production")
    elif rag_p3 < control_p3 - 0.05:
        print(f"[NEGATIVE] RAG decreases accuracy by {abs(improvement_p3):.1f}%")
        print(f"[RECOMMENDATION] DISABLE RAG - use keyword ranking only")
    else:
        print(f"[NEUTRAL] RAG has minimal impact ({improvement_p3:+.1f}%)")
        print(f"[RECOMMENDATION] Consider disabling RAG to reduce complexity")

    # Save results
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "experiment": "RAG Effectiveness Test",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "control_p3": control_p3,
                "rag_p3": rag_p3,
                "improvement_p3": improvement_p3,
                "control_mrr": control_mrr,
                "rag_mrr": rag_mrr
            },
            "results": all_results
        }, f, indent=2)

    print(f"\n[SAVED] Results: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
