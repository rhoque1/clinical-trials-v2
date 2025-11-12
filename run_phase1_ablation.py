"""
Phase 1 Knowledge Source Ablation Study

Tests 6 configurations to answer the critical research question:
"Does the 91K-line trial corpus help or hurt? Are authoritative guidelines + FDA labels sufficient?"

Configurations:
1. Control (no RAG)
2. Guidelines only
3. Guidelines + FDA
4. Guidelines + FDA + Biomarkers (no trial corpus)
5. Current system (all sources including trial corpus)
6. Trial corpus only

Runs on all 20 test cases
Expected runtime: ~90-120 minutes
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))


def calculate_metrics(ranked_trials: list, ground_truth_nct_ids: list) -> dict:
    """Calculate evaluation metrics"""
    ranked_nct_ids = [trial.get("nct_id", "") for trial in ranked_trials]

    metrics = {}

    # Precision@K
    for k in [1, 3, 5, 10]:
        top_k = ranked_nct_ids[:k]
        hits = len([nct for nct in ground_truth_nct_ids if nct in top_k])
        precision = hits / min(k, len(ground_truth_nct_ids)) if ground_truth_nct_ids else 0
        metrics[f"precision@{k}"] = precision

    # MRR
    first_hit_rank = None
    for rank, nct_id in enumerate(ranked_nct_ids, start=1):
        if nct_id in ground_truth_nct_ids:
            first_hit_rank = rank
            break

    metrics["mrr"] = 1.0 / first_hit_rank if first_hit_rank else 0.0
    metrics["first_hit_rank"] = first_hit_rank
    metrics["ground_truth_found"] = sum(1 for nct in ground_truth_nct_ids if nct in ranked_nct_ids[:10])

    return metrics


async def test_configuration(config_name: str, use_rag: bool, test_case: dict) -> dict:
    """Test a single configuration on a test case"""
    from agents.workflow_engine import WorkflowEngine
    from agents.orchestrator import WorkflowMode

    case_id = test_case["case_id"]

    print(f"\n[TEST] {config_name} | {case_id}")

    try:
        # Load patient profile
        profile_path = Path(f"evaluation/sample_profiles/{case_id}.json")
        with open(profile_path, 'r') as f:
            patient_profile = json.load(f)

        # Create engine
        engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

        # Run trial discovery
        discovery_result = await engine.run_trial_discovery(patient_profile)

        if not discovery_result.get("success"):
            raise Exception(f"Discovery failed: {discovery_result.get('error')}")

        # Run knowledge enhancement (or skip if control)
        if use_rag:
            enhancement_result = await engine.run_knowledge_enhancement(
                patient_profile,
                discovery_result['ranked_trials']
            )

            if not enhancement_result.get("success"):
                raise Exception(f"Enhancement failed: {enhancement_result.get('error')}")

            final_trials = enhancement_result['ranked_trials']
        else:
            # Control: no RAG
            final_trials = discovery_result['ranked_trials']

        # Calculate metrics
        ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]
        metrics = calculate_metrics(final_trials, ground_truth_nct_ids)

        print(f"   P@3={metrics['precision@3']:.1%} | MRR={metrics['mrr']:.3f}")

        return {
            "config_name": config_name,
            "test_case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "success": True
        }

    except Exception as e:
        print(f"   [ERROR] {str(e)}")
        return {
            "config_name": config_name,
            "test_case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }


async def run_phase1_experiment():
    """Run the complete Phase 1 ablation study"""

    print("="*70)
    print("PHASE 1: KNOWLEDGE SOURCE ABLATION STUDY")
    print("="*70)
    print("\nObjective: Determine which knowledge sources contribute to accuracy")
    print("Hypothesis: Guidelines + FDA sufficient; trial corpus adds noise")
    print("\nConfigurations: 6")
    print("Test cases: 20")
    print("Total evaluations: 120")
    print("Expected runtime: 90-120 minutes")
    print("\n" + "="*70)

    # Load test cases
    with open("evaluation/test_cases.json", 'r') as f:
        data = json.load(f)
        test_cases = data["test_cases"]

    print(f"\nLoaded {len(test_cases)} test cases")

    # Define configurations
    # NOTE: For this initial run, we'll test RAG on/off first
    # Full ablation with different knowledge sources requires rebuilding vectorstore

    configurations = [
        {"name": "Control (No RAG)", "use_rag": False},
        {"name": "RAG-Enhanced (Current System)", "use_rag": True},
    ]

    print(f"\n[INFO] Running 2 configurations for initial validation")
    print(f"[INFO] Control vs. RAG-Enhanced (full 6-config ablation requires vectorstore rebuild)")
    print("\nStarting evaluation...")

    all_results = []

    for config in configurations:
        config_name = config["name"]
        use_rag = config["use_rag"]

        print(f"\n{'='*70}")
        print(f"CONFIGURATION: {config_name}")
        print(f"{'='*70}")

        config_results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] ", end="")
            result = await test_configuration(config_name, use_rag, test_case)
            config_results.append(result)
            all_results.append(result)

            # Brief delay between calls
            await asyncio.sleep(1)

        # Calculate aggregate metrics
        successful = [r for r in config_results if r.get("success")]

        if successful:
            avg_p1 = np.mean([r["metrics"]["precision@1"] for r in successful])
            avg_p3 = np.mean([r["metrics"]["precision@3"] for r in successful])
            avg_p5 = np.mean([r["metrics"]["precision@5"] for r in successful])
            avg_mrr = np.mean([r["metrics"]["mrr"] for r in successful])

            print(f"\n{'='*70}")
            print(f"RESULTS: {config_name}")
            print(f"{'='*70}")
            print(f"  Cases evaluated: {len(successful)}/{len(test_cases)}")
            print(f"  Precision@1: {avg_p1:.1%}")
            print(f"  Precision@3: {avg_p3:.1%}")
            print(f"  Precision@5: {avg_p5:.1%}")
            print(f"  MRR: {avg_mrr:.3f}")

    # Save results
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"phase1_ablation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "experiment": "Phase 1 Knowledge Ablation",
            "timestamp": datetime.now().isoformat(),
            "configurations": len(configurations),
            "test_cases": len(test_cases),
            "results": all_results
        }, f, indent=2)

    print(f"\n{'='*70}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Results saved to: {output_file}")

    # Final comparison
    print_comparison(all_results)

    return all_results


def print_comparison(results: list):
    """Print side-by-side comparison"""

    # Group by configuration
    config_groups = {}
    for r in results:
        config_name = r.get("config_name")
        if config_name not in config_groups:
            config_groups[config_name] = []
        if r.get("success"):
            config_groups[config_name].append(r)

    print(f"\n{'='*70}")
    print(f"FINAL COMPARISON")
    print(f"{'='*70}\n")

    print(f"{'Configuration':<40} {'P@3':<10} {'MRR':<10} {'Cases':<10}")
    print(f"{'-'*70}")

    for config_name, config_results in config_groups.items():
        if config_results:
            avg_p3 = np.mean([r["metrics"]["precision@3"] for r in config_results])
            avg_mrr = np.mean([r["metrics"]["mrr"] for r in config_results])
            cases = len(config_results)

            print(f"{config_name:<40} {avg_p3:<10.1%} {avg_mrr:<10.3f} {cases:<10}")

    # Improvement calculation
    if len(config_groups) == 2:
        control_results = [r for r in results if "Control" in r.get("config_name", "") and r.get("success")]
        rag_results = [r for r in results if "RAG" in r.get("config_name", "") and r.get("success")]

        if control_results and rag_results:
            control_p3 = np.mean([r["metrics"]["precision@3"] for r in control_results])
            rag_p3 = np.mean([r["metrics"]["precision@3"] for r in rag_results])
            improvement = ((rag_p3 - control_p3) / control_p3 * 100) if control_p3 > 0 else 0

            print(f"\n{'='*70}")
            print(f"DECISION")
            print(f"{'='*70}")

            if rag_p3 > control_p3 + 0.10:
                print(f"[STRONG POSITIVE] RAG improves P@3 by {improvement:.1f}%")
                print(f"[ACTION] KEEP RAG - significant improvement detected")
            elif rag_p3 > control_p3 + 0.05:
                print(f"[POSITIVE] RAG improves P@3 by {improvement:.1f}%")
                print(f"[ACTION] KEEP RAG - moderate improvement")
            elif rag_p3 < control_p3 - 0.05:
                print(f"[NEGATIVE] RAG decreases P@3 by {abs(improvement):.1f}%")
                print(f"[ACTION] INVESTIGATE - RAG may be adding noise")
            else:
                print(f"[NEUTRAL] RAG has minimal impact ({improvement:+.1f}%)")
                print(f"[ACTION] Consider cost/complexity tradeoff")


if __name__ == "__main__":
    asyncio.run(run_phase1_experiment())
