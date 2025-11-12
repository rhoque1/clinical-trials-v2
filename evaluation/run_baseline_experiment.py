"""
Comprehensive Baseline Experiment Runner
Tests all 4 methods on all 20 test cases

Outputs:
- Per-case results (Precision@K, MRR for each method)
- Aggregate metrics (mean, std dev, confidence intervals)
- Statistical significance tests (t-tests comparing methods)
- Visualization data (for creating charts)
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
from collections import defaultdict
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.baselines import get_baseline


class BaselineExperiment:
    """Run comprehensive baseline comparison experiment"""

    def __init__(self):
        self.test_cases_path = Path(__file__).parent / "test_cases.json"
        self.profiles_dir = Path(__file__).parent / "sample_profiles"
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True, parents=True)

        # Load test cases
        with open(self.test_cases_path) as f:
            data = json.load(f)
            self.test_cases = data["test_cases"]

        print(f"Loaded {len(self.test_cases)} test cases")

    def calculate_metrics(self, ranked_trials: List[Dict], ground_truth_nct_ids: List[str]) -> Dict[str, float]:
        """Calculate evaluation metrics for a single case"""

        # Extract NCT IDs from ranked list
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
        metrics["first_hit_rank"] = first_hit_rank if first_hit_rank else 999

        # Hit Rate (did we find at least one?)
        metrics["hit_rate"] = 1.0 if first_hit_rank else 0.0

        # Recall@10
        hits_at_10 = len([nct for nct in ground_truth_nct_ids if nct in ranked_nct_ids[:10]])
        metrics["recall@10"] = hits_at_10 / len(ground_truth_nct_ids) if ground_truth_nct_ids else 0

        return metrics

    async def test_method_on_case(self, method_name: str, test_case: Dict) -> Dict:
        """Test a single method on a single test case"""

        case_id = test_case["case_id"]
        print(f"\n  Testing {method_name} on {case_id}...")

        try:
            # Load patient profile
            profile_path = self.profiles_dir / f"{case_id}.json"
            with open(profile_path) as f:
                patient_profile = json.load(f)

            # Get baseline method
            baseline = get_baseline(method_name)

            # Rank trials
            ranked_trials = await baseline.rank_trials(patient_profile)

            # Extract ground truth NCT IDs
            ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]

            # Calculate metrics
            metrics = self.calculate_metrics(ranked_trials, ground_truth_nct_ids)

            # Build result
            result = {
                "method": method_name,
                "case_id": case_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "top_5_trials": [
                    {
                        "rank": i,
                        "nct_id": trial.get("nct_id"),
                        "score": trial.get("score", 0),
                        "is_ground_truth": trial.get("nct_id") in ground_truth_nct_ids
                    }
                    for i, trial in enumerate(ranked_trials[:5], 1)
                ],
                "ground_truth_nct_ids": ground_truth_nct_ids,
                "success": True
            }

            # Print brief summary
            print(f"    P@3: {metrics['precision@3']:.1%}, MRR: {metrics['mrr']:.3f}")

            return result

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()

            return {
                "method": method_name,
                "case_id": case_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    async def run_experiment(self, methods: List[str] = None):
        """
        Run experiment: test all methods on all cases

        Args:
            methods: List of method names to test. Default: all 4 methods
        """

        if methods is None:
            methods = ['keyword_search', 'tfidf', 'zero_shot_gpt4', 'rag_enhanced']

        print("\n" + "="*70)
        print("BASELINE COMPARISON EXPERIMENT")
        print("="*70)
        print(f"\nMethods: {', '.join(methods)}")
        print(f"Test cases: {len(self.test_cases)}")
        print(f"Total evaluations: {len(methods) * len(self.test_cases)}")
        print(f"\n{'='*70}\n")

        all_results = []

        # Test each method on each case
        for method_name in methods:
            print(f"\n{'='*70}")
            print(f"TESTING METHOD: {method_name.upper()}")
            print(f"{'='*70}")

            method_results = []

            for test_case in self.test_cases:
                result = await self.test_method_on_case(method_name, test_case)
                method_results.append(result)
                all_results.append(result)

                # Small delay to avoid rate limits
                await asyncio.sleep(1)

            # Compute aggregate metrics for this method
            self.print_aggregate_metrics(method_name, method_results)

        # Save results
        output_file = self.results_dir / f"baseline_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "experiment": "Baseline Comparison",
                "timestamp": datetime.now().isoformat(),
                "methods": methods,
                "test_cases": len(self.test_cases),
                "results": all_results
            }, f, indent=2)

        print(f"\n{'='*70}")
        print(f"EXPERIMENT COMPLETE")
        print(f"{'='*70}")
        print(f"Results saved to: {output_file}")

        # Final comparison
        self.print_final_comparison(all_results, methods)
        self.compute_statistical_significance(all_results, methods)

        return all_results, output_file

    def print_aggregate_metrics(self, method_name: str, results: List[Dict]):
        """Print aggregate metrics for a single method"""

        successful = [r for r in results if r.get("success")]

        if not successful:
            print(f"\n[WARNING] No successful results for {method_name}")
            return

        # Compute means
        metrics_dict = defaultdict(list)
        for r in successful:
            for metric_name, value in r["metrics"].items():
                metrics_dict[metric_name].append(value)

        print(f"\n{'='*70}")
        print(f"AGGREGATE RESULTS: {method_name.upper()}")
        print(f"{'='*70}")
        print(f"Cases evaluated: {len(successful)}/{len(results)}")
        print(f"\nMetric                 Mean      Std Dev   Min       Max")
        print(f"{'-'*70}")

        for metric_name in ["precision@1", "precision@3", "precision@5", "mrr", "hit_rate"]:
            values = metrics_dict[metric_name]
            mean = np.mean(values)
            std = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)

            print(f"{metric_name:<20} {mean:>7.1%}   {std:>7.3f}   {min_val:>7.1%}   {max_val:>7.1%}")

    def print_final_comparison(self, all_results: List[Dict], methods: List[str]):
        """Print side-by-side comparison of all methods"""

        print(f"\n{'='*70}")
        print(f"FINAL COMPARISON (ALL METHODS)")
        print(f"{'='*70}")

        # Group results by method
        by_method = defaultdict(list)
        for r in all_results:
            if r.get("success"):
                by_method[r["method"]].append(r)

        # Print comparison table
        print(f"\n{'Method':<20} {'P@1':<10} {'P@3':<10} {'P@5':<10} {'MRR':<10} {'Hit Rate':<10}")
        print(f"{'-'*70}")

        for method in methods:
            if method not in by_method:
                continue

            results = by_method[method]

            p1 = np.mean([r["metrics"]["precision@1"] for r in results])
            p3 = np.mean([r["metrics"]["precision@3"] for r in results])
            p5 = np.mean([r["metrics"]["precision@5"] for r in results])
            mrr = np.mean([r["metrics"]["mrr"] for r in results])
            hit_rate = np.mean([r["metrics"]["hit_rate"] for r in results])

            print(f"{method:<20} {p1:<10.1%} {p3:<10.1%} {p5:<10.1%} {mrr:<10.3f} {hit_rate:<10.1%}")

    def compute_statistical_significance(self, all_results: List[Dict], methods: List[str]):
        """Compute statistical significance using paired t-tests"""

        from scipy import stats

        print(f"\n{'='*70}")
        print(f"STATISTICAL SIGNIFICANCE (Paired t-tests)")
        print(f"{'='*70}")

        # Group results by method and case_id
        by_method_and_case = defaultdict(lambda: defaultdict(dict))
        for r in all_results:
            if r.get("success"):
                by_method_and_case[r["method"]][r["case_id"]] = r["metrics"]

        # Compare RAG-enhanced against each baseline
        if 'rag_enhanced' in methods:
            baseline_methods = [m for m in methods if m != 'rag_enhanced']

            for baseline in baseline_methods:
                # Get paired P@3 scores
                rag_scores = []
                baseline_scores = []

                for case_id in by_method_and_case['rag_enhanced'].keys():
                    if case_id in by_method_and_case[baseline]:
                        rag_scores.append(by_method_and_case['rag_enhanced'][case_id]['precision@3'])
                        baseline_scores.append(by_method_and_case[baseline][case_id]['precision@3'])

                if len(rag_scores) >= 3:  # Need at least 3 pairs for t-test
                    t_stat, p_value = stats.ttest_rel(rag_scores, baseline_scores)

                    mean_diff = np.mean(rag_scores) - np.mean(baseline_scores)
                    relative_improvement = (mean_diff / np.mean(baseline_scores) * 100) if np.mean(baseline_scores) > 0 else 0

                    print(f"\nRAG-enhanced vs. {baseline}:")
                    print(f"  Mean P@3 difference: {mean_diff:+.1%} ({relative_improvement:+.1f}% relative)")
                    print(f"  t-statistic: {t_stat:.3f}")
                    print(f"  p-value: {p_value:.4f}")

                    if p_value < 0.05:
                        print(f"  [SIGNIFICANT] p < 0.05 - RAG-enhanced is {'better' if mean_diff > 0 else 'worse'}")
                    else:
                        print(f"  [NOT SIGNIFICANT] p >= 0.05 - No significant difference")

        print(f"\n{'='*70}")


async def main():
    """Run the baseline experiment"""

    import sys

    # Parse arguments
    if len(sys.argv) > 1:
        # Allow specifying which methods to test
        methods = sys.argv[1].split(',')
    else:
        # Default: test all methods
        methods = ['keyword_search', 'tfidf', 'zero_shot_gpt4', 'rag_enhanced']

    print(f"\nRunning experiment with methods: {', '.join(methods)}")

    experiment = BaselineExperiment()
    results, output_file = await experiment.run_experiment(methods)

    print(f"\n[DONE] Results saved to: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Review results in {output_file}")
    print(f"2. Analyze failure modes")
    print(f"3. Create visualizations (precision@K curves, bar charts)")


if __name__ == "__main__":
    asyncio.run(main())
