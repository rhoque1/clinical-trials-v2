"""
Simplified RAG Evaluator - Works with existing workflow_engine

Tests the current RAG system against a no-RAG control to measure impact.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np


class SimpleRAGEvaluator:
    """
    Simplified evaluator that works with existing workflow_engine

    Tests two conditions:
    1. Control: No RAG (DISABLE_RAG_FOR_EXPERIMENT = True)
    2. Treatment: Current RAG system (DISABLE_RAG_FOR_EXPERIMENT = False)
    """

    def __init__(self):
        self.test_cases_path = Path("evaluation/test_cases.json")
        self.sample_profiles_dir = Path("evaluation/sample_profiles")
        self.results_dir = Path("evaluation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Load test cases
        with open(self.test_cases_path, 'r') as f:
            data = json.load(f)
            self.test_cases = data["test_cases"]

        print(f"Loaded {len(self.test_cases)} test cases")

    def calculate_metrics(self, ranked_trials: List[Dict], ground_truth_nct_ids: List[str]) -> Dict[str, float]:
        """Calculate evaluation metrics"""

        # Extract NCT IDs
        ranked_nct_ids = [trial.get("nct_id", "") for trial in ranked_trials]

        metrics = {}

        # Precision@K
        for k in [1, 3, 5, 10]:
            top_k = ranked_nct_ids[:k]
            hits = len([nct for nct in ground_truth_nct_ids if nct in top_k])
            precision = hits / min(k, len(ground_truth_nct_ids)) if ground_truth_nct_ids else 0
            metrics[f"precision@{k}"] = precision

        # Mean Reciprocal Rank (MRR)
        first_hit_rank = None
        for rank, nct_id in enumerate(ranked_nct_ids, start=1):
            if nct_id in ground_truth_nct_ids:
                first_hit_rank = rank
                break

        metrics["mrr"] = 1.0 / first_hit_rank if first_hit_rank else 0.0
        metrics["first_hit_rank"] = first_hit_rank

        # Count found
        metrics["ground_truth_found"] = sum(1 for nct in ground_truth_nct_ids if nct in ranked_nct_ids[:10])
        metrics["ground_truth_total"] = len(ground_truth_nct_ids)

        return metrics

    async def test_configuration(self, use_rag: bool, test_case: Dict) -> Dict:
        """
        Test a single configuration on a test case

        Args:
            use_rag: True for RAG enabled, False for control (no RAG)
            test_case: Test case dict
        """

        config_name = "With RAG (Current System)" if use_rag else "No RAG (Control)"
        case_id = test_case["case_id"]

        print(f"\n{'='*70}")
        print(f"Testing: {config_name}")
        print(f"Case: {case_id}")
        print(f"{'='*70}")

        try:
            # Load sample profile
            profile_path = self.sample_profiles_dir / f"{case_id}.json"
            with open(profile_path, 'r') as f:
                patient_profile = json.load(f)

            # Modify workflow_engine to use/disable RAG
            # We'll do this by temporarily modifying the file
            workflow_file = Path("agents/workflow_engine.py")
            with open(workflow_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Modify the DISABLE_RAG_FOR_EXPERIMENT flag
            if use_rag:
                modified_content = original_content.replace(
                    "DISABLE_RAG_FOR_EXPERIMENT = False",
                    "DISABLE_RAG_FOR_EXPERIMENT = False"
                ).replace(
                    "DISABLE_RAG_FOR_EXPERIMENT = True",
                    "DISABLE_RAG_FOR_EXPERIMENT = False"
                )
            else:
                modified_content = original_content.replace(
                    "DISABLE_RAG_FOR_EXPERIMENT = False",
                    "DISABLE_RAG_FOR_EXPERIMENT = True"
                )

            # Write modified version
            with open(workflow_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            try:
                # Import workflow engine (will use modified version)
                from agents.workflow_engine import WorkflowEngine
                from agents.orchestrator import WorkflowMode

                # Reload to get modified version
                import importlib
                import agents.workflow_engine
                importlib.reload(agents.workflow_engine)
                from agents.workflow_engine import WorkflowEngine

                engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

                # Run trial discovery
                print(f"\nRunning trial discovery...")
                discovery_result = await engine.run_trial_discovery(patient_profile)

                if not discovery_result.get("success"):
                    raise Exception(f"Trial discovery failed: {discovery_result.get('error')}")

                # Run knowledge enhancement
                print(f"\nRunning knowledge enhancement (RAG={'enabled' if use_rag else 'disabled'})...")
                enhancement_result = await engine.run_knowledge_enhancement(
                    patient_profile,
                    discovery_result['ranked_trials']
                )

                if not enhancement_result.get("success"):
                    raise Exception(f"Knowledge enhancement failed: {enhancement_result.get('error')}")

                # Get final ranked trials
                final_trials = enhancement_result['ranked_trials']

                # Extract ground truth NCT IDs
                ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]

                # Calculate metrics
                metrics = self.calculate_metrics(final_trials, ground_truth_nct_ids)

                # Show results
                print(f"\n[RESULTS]")
                print(f"  Precision@1: {metrics['precision@1']:.1%}")
                print(f"  Precision@3: {metrics['precision@3']:.1%}")
                print(f"  Precision@5: {metrics['precision@5']:.1%}")
                print(f"  MRR: {metrics['mrr']:.3f}")
                print(f"  First hit rank: {metrics['first_hit_rank']}")
                print(f"  Ground truth found: {metrics['ground_truth_found']}/{metrics['ground_truth_total']}")

                print(f"\n  Top 5 trials:")
                for i, trial in enumerate(final_trials[:5], 1):
                    nct_id = trial.get("nct_id", "N/A")
                    score = trial.get("score", 0)
                    is_gt = "[GROUND TRUTH]" if nct_id in ground_truth_nct_ids else ""
                    print(f"    {i}. {nct_id} (score: {score}) {is_gt}")

                result = {
                    "config_name": config_name,
                    "use_rag": use_rag,
                    "test_case_id": case_id,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics,
                    "top_5_trials": [
                        {
                            "rank": i,
                            "nct_id": trial.get("nct_id"),
                            "score": trial.get("score"),
                            "is_ground_truth": trial.get("nct_id") in ground_truth_nct_ids
                        }
                        for i, trial in enumerate(final_trials[:5], 1)
                    ],
                    "success": True
                }

                return result

            finally:
                # Restore original file
                with open(workflow_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)

                print(f"\n[Restored workflow_engine.py to original state]")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "config_name": config_name,
                "use_rag": use_rag,
                "test_case_id": case_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    async def run_experiment(self):
        """
        Run the complete experiment:
        1. Test all cases WITHOUT RAG (control)
        2. Test all cases WITH RAG (treatment)
        3. Compare results
        """

        print("\n" + "="*70)
        print("RAG EFFECTIVENESS EXPERIMENT")
        print("="*70)
        print(f"\nTest cases: {len(self.test_cases)}")
        print(f"Conditions: 2 (Control vs RAG)")
        print(f"Total evaluations: {len(self.test_cases) * 2}")
        print(f"\n{'='*70}\n")

        all_results = []

        # Test each configuration on each case
        for use_rag in [False, True]:  # Control first, then RAG
            config_name = "With RAG" if use_rag else "Control (No RAG)"

            print(f"\n{'='*70}")
            print(f"TESTING: {config_name}")
            print(f"{'='*70}")

            config_results = []

            for test_case in self.test_cases:
                result = await self.test_configuration(use_rag, test_case)
                config_results.append(result)
                all_results.append(result)

                # Delay between cases
                await asyncio.sleep(2)

            # Calculate aggregate metrics for this config
            successful = [r for r in config_results if r.get("success")]

            if successful:
                avg_p1 = np.mean([r["metrics"]["precision@1"] for r in successful])
                avg_p3 = np.mean([r["metrics"]["precision@3"] for r in successful])
                avg_p5 = np.mean([r["metrics"]["precision@5"] for r in successful])
                avg_mrr = np.mean([r["metrics"]["mrr"] for r in successful])

                print(f"\n{'='*70}")
                print(f"AGGREGATE RESULTS: {config_name}")
                print(f"{'='*70}")
                print(f"  Cases evaluated: {len(successful)}/{len(self.test_cases)}")
                print(f"  Avg Precision@1: {avg_p1:.1%}")
                print(f"  Avg Precision@3: {avg_p3:.1%}")
                print(f"  Avg Precision@5: {avg_p5:.1%}")
                print(f"  Avg MRR: {avg_mrr:.3f}")

        # Save results
        output_file = self.results_dir / f"simple_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "experiment": "RAG Effectiveness Test",
                "timestamp": datetime.now().isoformat(),
                "test_cases": len(self.test_cases),
                "results": all_results
            }, f, indent=2)

        print(f"\n{'='*70}")
        print(f"EXPERIMENT COMPLETE")
        print(f"{'='*70}")
        print(f"Results saved to: {output_file}")

        # Final comparison
        self.print_comparison(all_results)

        return all_results

    def print_comparison(self, results: List[Dict]):
        """Print side-by-side comparison of control vs RAG"""

        control_results = [r for r in results if not r.get("use_rag") and r.get("success")]
        rag_results = [r for r in results if r.get("use_rag") and r.get("success")]

        if not control_results or not rag_results:
            print("\n[WARNING] Not enough successful results to compare")
            return

        # Calculate aggregates
        control_p3 = np.mean([r["metrics"]["precision@3"] for r in control_results])
        rag_p3 = np.mean([r["metrics"]["precision@3"] for r in rag_results])

        control_mrr = np.mean([r["metrics"]["mrr"] for r in control_results])
        rag_mrr = np.mean([r["metrics"]["mrr"] for r in rag_results])

        improvement_p3 = ((rag_p3 - control_p3) / control_p3 * 100) if control_p3 > 0 else 0
        improvement_mrr = ((rag_mrr - control_mrr) / control_mrr * 100) if control_mrr > 0 else 0

        print(f"\n{'='*70}")
        print(f"FINAL COMPARISON")
        print(f"{'='*70}")
        print(f"\n{'Metric':<20} {'Control':<15} {'With RAG':<15} {'Change':<15}")
        print(f"{'-'*70}")
        print(f"{'Precision@3':<20} {control_p3:<15.1%} {rag_p3:<15.1%} {improvement_p3:+.1f}%")
        print(f"{'MRR':<20} {control_mrr:<15.3f} {rag_mrr:<15.3f} {improvement_mrr:+.1f}%")

        print(f"\n{'='*70}")
        print(f"CONCLUSION")
        print(f"{'='*70}")

        if rag_p3 > control_p3 + 0.05:  # 5% threshold
            print(f"[POSITIVE] RAG improves accuracy by {improvement_p3:.1f}%")
            print(f"[RECOMMENDATION] KEEP RAG in production")
        elif rag_p3 < control_p3 - 0.05:
            print(f"[NEGATIVE] RAG decreases accuracy by {abs(improvement_p3):.1f}%")
            print(f"[RECOMMENDATION] DISABLE RAG - use keyword ranking only")
        else:
            print(f"[NEUTRAL] RAG has minimal impact ({improvement_p3:+.1f}%)")
            print(f"[RECOMMENDATION] Consider disabling RAG to reduce complexity")


async def main():
    """Run the simple experiment"""
    evaluator = SimpleRAGEvaluator()
    results = await evaluator.run_experiment()

    print(f"\n[DONE] Check evaluation/results/ for detailed results")


if __name__ == "__main__":
    asyncio.run(main())
