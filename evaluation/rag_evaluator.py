"""
RAG Evaluation Framework

Measures accuracy of different RAG configurations against ground truth test cases.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import numpy as np
from collections import defaultdict

from evaluation.rag_configurations import RAGConfiguration, get_all_configs
from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode


class RAGEvaluator:
    """Evaluates RAG configurations against ground truth test cases"""

    def __init__(self, test_cases_path: str = "evaluation/test_cases.json"):
        self.test_cases_path = Path(test_cases_path)
        self.results_dir = Path("evaluation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Load test cases
        with open(self.test_cases_path, 'r') as f:
            data = json.load(f)
            self.test_cases = data["test_cases"]

        print(f"Loaded {len(self.test_cases)} test cases")

    def calculate_metrics(self,
                         ranked_trials: List[Dict],
                         ground_truth: List[Dict]) -> Dict[str, float]:
        """
        Calculate evaluation metrics

        Metrics:
        - Precision@K: % of ground truth trials in top K
        - Mean Reciprocal Rank (MRR): Average 1/rank of first correct trial
        - NDCG@K: Normalized Discounted Cumulative Gain
        """
        metrics = {}

        # Extract NCT IDs from ranked trials
        ranked_nct_ids = [trial.get("nct_id") for trial in ranked_trials]
        ground_truth_nct_ids = [gt["nct_id"] for gt in ground_truth]

        # Precision@K
        for k in [1, 3, 5, 10]:
            top_k = ranked_nct_ids[:k]
            hits = len([nct for nct in ground_truth_nct_ids if nct in top_k])
            precision = hits / min(k, len(ground_truth_nct_ids))
            metrics[f"precision@{k}"] = precision

        # Mean Reciprocal Rank (MRR)
        first_hit_rank = None
        for rank, nct_id in enumerate(ranked_nct_ids, start=1):
            if nct_id in ground_truth_nct_ids:
                first_hit_rank = rank
                break

        metrics["mrr"] = 1.0 / first_hit_rank if first_hit_rank else 0.0
        metrics["first_hit_rank"] = first_hit_rank if first_hit_rank else None

        # NDCG@5
        # Relevance scores: very_high=3, high=2, medium=1
        relevance_map = {gt["nct_id"]: 3 if gt.get("confidence") == "very_high" else 2
                        for gt in ground_truth}

        dcg = 0.0
        for rank, nct_id in enumerate(ranked_nct_ids[:5], start=1):
            if nct_id in relevance_map:
                relevance = relevance_map[nct_id]
                dcg += relevance / np.log2(rank + 1)

        # Ideal DCG (perfect ranking)
        ideal_relevances = sorted([3 if gt.get("confidence") == "very_high" else 2
                                  for gt in ground_truth], reverse=True)
        idcg = sum(rel / np.log2(rank + 1) for rank, rel in enumerate(ideal_relevances[:5], start=1))

        metrics["ndcg@5"] = dcg / idcg if idcg > 0 else 0.0

        # Ground truth trials found (absolute count)
        metrics["ground_truth_found"] = sum(1 for nct in ground_truth_nct_ids if nct in ranked_nct_ids[:10])
        metrics["ground_truth_total"] = len(ground_truth_nct_ids)

        return metrics

    async def evaluate_config_on_case(self,
                                      config: RAGConfiguration,
                                      test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single RAG configuration on a single test case

        Returns results with metrics
        """
        print(f"\n{'='*70}")
        print(f"Evaluating: {config.name}")
        print(f"Test Case: {test_case['case_id']}")
        print(f"{'='*70}")

        # Create workflow engine with this RAG config
        # NOTE: We'll need to modify workflow_engine to accept RAG config
        # For now, use the existing system
        engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

        # Determine if RAG should be disabled
        disable_rag = (config.config_id == "control")

        # Modify the workflow engine's RAG setting
        # This is a hack - we'll need to refactor workflow_engine to accept config
        from agents.workflow_engine import WorkflowEngine as WE
        original_disable_flag = False

        # Run the workflow (using existing PDF if available, or create mock)
        # For now, we'll use the patient summary to create a simple profile
        try:
            # Mock patient profile from test case
            patient_profile = {
                "success": True,
                "demographics": {"age": 40, "sex": "Female"},
                "diagnoses": test_case["patient_summary"],
                "biomarkers": ", ".join(test_case["key_biomarkers"]),
                "treatment_history": {"prior_therapies": []},
                "search_terms": test_case["key_biomarkers"]
            }

            # Run trial discovery
            discovery_result = await engine.run_trial_discovery(patient_profile)

            # Run knowledge enhancement with this config
            # TODO: This needs refactoring to accept config parameter
            if not disable_rag:
                enhancement_result = await engine.run_knowledge_enhancement(
                    patient_profile,
                    discovery_result['ranked_trials']
                )
                final_trials = enhancement_result['ranked_trials']
            else:
                final_trials = discovery_result['ranked_trials']

            # Calculate metrics
            metrics = self.calculate_metrics(
                final_trials,
                test_case["ground_truth_trials"]
            )

            # Return results
            result = {
                "config_id": config.config_id,
                "config_name": config.name,
                "test_case_id": test_case["case_id"],
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "top_5_trials": [
                    {
                        "nct_id": trial.get("nct_id"),
                        "title": trial.get("title", "")[:80],
                        "score": trial.get("score"),
                        "original_score": trial.get("original_score"),
                        "guideline_score": trial.get("guideline_score"),
                        "is_ground_truth": trial.get("nct_id") in [gt["nct_id"] for gt in test_case["ground_truth_trials"]]
                    }
                    for trial in final_trials[:5]
                ],
                "ground_truth_trials": test_case["ground_truth_trials"],
                "success": True
            }

            print(f"\n[CHART] Results:")
            print(f"  Precision@3: {metrics['precision@3']:.2%}")
            print(f"  Precision@5: {metrics['precision@5']:.2%}")
            print(f"  MRR: {metrics['mrr']:.3f}")
            print(f"  NDCG@5: {metrics['ndcg@5']:.3f}")
            print(f"  Ground truth found: {metrics['ground_truth_found']}/{metrics['ground_truth_total']}")

            return result

        except Exception as e:
            print(f"[X] Error evaluating config: {str(e)}")
            return {
                "config_id": config.config_id,
                "config_name": config.name,
                "test_case_id": test_case["case_id"],
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    async def evaluate_config(self, config: RAGConfiguration) -> Dict[str, Any]:
        """
        Evaluate a configuration across all test cases

        Returns aggregate metrics
        """
        print(f"\n{'='*70}")
        print(f"EVALUATING CONFIGURATION: {config.name}")
        print(f"{'='*70}")

        results = []
        for test_case in self.test_cases:
            result = await self.evaluate_config_on_case(config, test_case)
            results.append(result)

            # Small delay between cases
            await asyncio.sleep(2)

        # Aggregate metrics
        successful_results = [r for r in results if r.get("success")]

        if not successful_results:
            return {
                "config_id": config.config_id,
                "config_name": config.name,
                "success": False,
                "error": "All test cases failed"
            }

        # Average metrics across test cases
        aggregate_metrics = defaultdict(list)
        for result in successful_results:
            for metric_name, value in result["metrics"].items():
                if value is not None and metric_name != "first_hit_rank":
                    aggregate_metrics[metric_name].append(value)

        avg_metrics = {
            metric: np.mean(values)
            for metric, values in aggregate_metrics.items()
        }

        # Overall assessment
        config_result = {
            "config_id": config.config_id,
            "config_name": config.name,
            "description": config.description,
            "timestamp": datetime.now().isoformat(),
            "test_cases_evaluated": len(successful_results),
            "test_cases_failed": len(results) - len(successful_results),
            "aggregate_metrics": avg_metrics,
            "per_case_results": results,
            "success": True
        }

        # Save results
        output_file = self.results_dir / f"{config.config_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(config_result, f, indent=2)

        print(f"\n{'='*70}")
        print(f"CONFIGURATION RESULTS: {config.name}")
        print(f"{'='*70}")
        print(f"Test cases evaluated: {len(successful_results)}/{len(results)}")
        print(f"\nAggregate Metrics:")
        print(f"  Precision@3: {avg_metrics.get('precision@3', 0):.2%}")
        print(f"  Precision@5: {avg_metrics.get('precision@5', 0):.2%}")
        print(f"  MRR: {avg_metrics.get('mrr', 0):.3f}")
        print(f"  NDCG@5: {avg_metrics.get('ndcg@5', 0):.3f}")
        print(f"\nResults saved to: {output_file}")

        return config_result

    async def run_experiment(self, experiment_name: str):
        """
        Run a full experiment with multiple configurations

        Args:
            experiment_name: 'knowledge_ablation', 'retrieval_params', or 'query_construction'
        """
        from evaluation.rag_configurations import get_experiment_configs

        configs = get_experiment_configs(experiment_name)

        print(f"\n{'='*70}")
        print(f"RUNNING EXPERIMENT: {experiment_name}")
        print(f"Configurations to test: {len(configs)}")
        print(f"{'='*70}")

        experiment_results = []
        for config in configs:
            result = await self.evaluate_config(config)
            experiment_results.append(result)

            # Delay between configs
            await asyncio.sleep(5)

        # Save experiment summary
        experiment_summary = {
            "experiment_name": experiment_name,
            "timestamp": datetime.now().isoformat(),
            "configs_tested": len(configs),
            "results": experiment_results
        }

        summary_file = self.results_dir / f"experiment_{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(experiment_summary, f, indent=2)

        # Print comparison
        print(f"\n{'='*70}")
        print(f"EXPERIMENT SUMMARY: {experiment_name}")
        print(f"{'='*70}")
        print(f"\nConfiguration Comparison (sorted by Precision@3):\n")

        successful_results = [r for r in experiment_results if r.get("success")]
        sorted_results = sorted(
            successful_results,
            key=lambda x: x["aggregate_metrics"].get("precision@3", 0),
            reverse=True
        )

        print(f"{'Rank':<6} {'Configuration':<30} {'P@3':<8} {'P@5':<8} {'MRR':<8} {'NDCG@5':<8}")
        print("-" * 70)

        for rank, result in enumerate(sorted_results, 1):
            metrics = result["aggregate_metrics"]
            print(f"{rank:<6} {result['config_name'][:29]:<30} "
                  f"{metrics.get('precision@3', 0):.2%}   "
                  f"{metrics.get('precision@5', 0):.2%}   "
                  f"{metrics.get('mrr', 0):.3f}    "
                  f"{metrics.get('ndcg@5', 0):.3f}")

        print(f"\nFull results saved to: {summary_file}")

        return experiment_summary

    async def quick_test(self, config: RAGConfiguration, test_case_id: str = None):
        """Quick test of a single config on one case"""
        if test_case_id:
            test_case = next((tc for tc in self.test_cases if tc["case_id"] == test_case_id), None)
            if not test_case:
                print(f"Test case {test_case_id} not found")
                return
        else:
            test_case = self.test_cases[0]  # Use first case

        result = await self.evaluate_config_on_case(config, test_case)
        return result


async def main():
    """Run experiments"""
    evaluator = RAGEvaluator()

    # Run the knowledge ablation experiment
    print("\n" + "="*70)
    print("STARTING KNOWLEDGE ABLATION EXPERIMENT")
    print("Testing which knowledge sources contribute to accuracy")
    print("="*70)

    await evaluator.run_experiment("knowledge_ablation")

    print("\n[OK] Experiment complete! Check evaluation/results/ for detailed results.")


if __name__ == "__main__":
    asyncio.run(main())
