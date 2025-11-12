"""
Statistical Analysis and Visualization of RAG Evaluation Results

Analyzes experiment results to determine:
1. Which RAG configurations perform best
2. Statistical significance of differences
3. Which knowledge sources matter most
4. Recommendations for optimal configuration
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns


class ResultsAnalyzer:
    """Analyze and visualize RAG evaluation results"""

    def __init__(self, results_dir: str = "evaluation/results"):
        self.results_dir = Path(results_dir)
        self.experiments = []
        self.load_experiments()

    def load_experiments(self):
        """Load all experiment result files"""
        experiment_files = list(self.results_dir.glob("experiment_*.json"))

        for file in experiment_files:
            with open(file, 'r') as f:
                experiment = json.load(f)
                experiment['file_path'] = str(file)
                self.experiments.append(experiment)

        print(f"Loaded {len(self.experiments)} experiments")

    def create_comparison_table(self, experiment_name: str = None) -> pd.DataFrame:
        """
        Create comparison table of all configurations

        Returns DataFrame with configs as rows, metrics as columns
        """
        if experiment_name:
            experiments = [e for e in self.experiments if e["experiment_name"] == experiment_name]
        else:
            experiments = self.experiments

        if not experiments:
            print(f"No experiments found for: {experiment_name}")
            return pd.DataFrame()

        # Use most recent experiment
        experiment = max(experiments, key=lambda x: x["timestamp"])

        rows = []
        for result in experiment["results"]:
            if not result.get("success"):
                continue

            row = {
                "Config": result["config_name"],
                "Config ID": result["config_id"],
                "P@1": result["aggregate_metrics"].get("precision@1", 0),
                "P@3": result["aggregate_metrics"].get("precision@3", 0),
                "P@5": result["aggregate_metrics"].get("precision@5", 0),
                "MRR": result["aggregate_metrics"].get("mrr", 0),
                "NDCG@5": result["aggregate_metrics"].get("ndcg@5", 0),
                "Cases": result["test_cases_evaluated"]
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df = df.sort_values("P@3", ascending=False)

        return df

    def statistical_significance_test(self, config1_id: str, config2_id: str) -> Dict[str, Any]:
        """
        Test if difference between two configs is statistically significant

        Uses paired t-test on per-case metrics
        """
        # Find results for both configs
        config1_results = None
        config2_results = None

        for experiment in self.experiments:
            for result in experiment["results"]:
                if result.get("config_id") == config1_id:
                    config1_results = result
                if result.get("config_id") == config2_id:
                    config2_results = result

        if not config1_results or not config2_results:
            return {"error": "One or both configs not found"}

        # Extract per-case P@3 scores
        config1_scores = [
            case["metrics"]["precision@3"]
            for case in config1_results["per_case_results"]
            if case.get("success")
        ]

        config2_scores = [
            case["metrics"]["precision@3"]
            for case in config2_results["per_case_results"]
            if case.get("success")
        ]

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(config1_scores, config2_scores)

        # Effect size (Cohen's d)
        mean_diff = np.mean(config1_scores) - np.mean(config2_scores)
        pooled_std = np.sqrt((np.std(config1_scores)**2 + np.std(config2_scores)**2) / 2)
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

        result = {
            "config1": config1_id,
            "config2": config2_id,
            "config1_mean": np.mean(config1_scores),
            "config2_mean": np.mean(config2_scores),
            "mean_difference": mean_diff,
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant_at_0.05": p_value < 0.05,
            "significant_at_0.01": p_value < 0.01,
            "cohens_d": cohens_d,
            "effect_size": self._interpret_cohens_d(cohens_d)
        }

        return result

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        d = abs(d)
        if d < 0.2:
            return "negligible"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"

    def knowledge_ablation_analysis(self) -> Dict[str, Any]:
        """
        Analyze knowledge ablation experiment to determine:
        1. Does RAG help at all? (control vs any RAG)
        2. Which sources are most valuable?
        3. Does trial corpus help or hurt?
        """
        # Find knowledge ablation experiment
        ablation_exp = None
        for exp in self.experiments:
            if "ablation" in exp["experiment_name"].lower():
                ablation_exp = exp
                break

        if not ablation_exp:
            return {"error": "Knowledge ablation experiment not found"}

        # Extract key comparisons
        results_map = {
            r["config_id"]: r
            for r in ablation_exp["results"]
            if r.get("success")
        }

        analysis = {
            "experiment": ablation_exp["experiment_name"],
            "timestamp": ablation_exp["timestamp"]
        }

        # 1. RAG vs No RAG
        if "control" in results_map and "guidelines_only" in results_map:
            control_p3 = results_map["control"]["aggregate_metrics"]["precision@3"]
            rag_p3 = results_map["guidelines_only"]["aggregate_metrics"]["precision@3"]

            analysis["rag_helps"] = rag_p3 > control_p3
            analysis["rag_improvement"] = (rag_p3 - control_p3) / control_p3 if control_p3 > 0 else 0

            sig_test = self.statistical_significance_test("control", "guidelines_only")
            analysis["rag_vs_control_significant"] = sig_test.get("significant_at_0.05", False)

        # 2. Guidelines only vs Guidelines + FDA
        if "guidelines_only" in results_map and "guidelines_fda" in results_map:
            guidelines_p3 = results_map["guidelines_only"]["aggregate_metrics"]["precision@3"]
            guidelines_fda_p3 = results_map["guidelines_fda"]["aggregate_metrics"]["precision@3"]

            analysis["fda_labels_help"] = guidelines_fda_p3 > guidelines_p3
            analysis["fda_improvement"] = (guidelines_fda_p3 - guidelines_p3) / guidelines_p3 if guidelines_p3 > 0 else 0

        # 3. With vs Without Trial Corpus
        if "no_trial_corpus" in results_map and "current_system" in results_map:
            no_corpus_p3 = results_map["no_trial_corpus"]["aggregate_metrics"]["precision@3"]
            with_corpus_p3 = results_map["current_system"]["aggregate_metrics"]["precision@3"]

            analysis["trial_corpus_helps"] = with_corpus_p3 > no_corpus_p3
            analysis["corpus_impact"] = (with_corpus_p3 - no_corpus_p3) / no_corpus_p3 if no_corpus_p3 > 0 else 0

            sig_test = self.statistical_significance_test("no_trial_corpus", "current_system")
            analysis["corpus_impact_significant"] = sig_test.get("significant_at_0.05", False)

        # 4. Best configuration
        best_config = max(
            results_map.values(),
            key=lambda x: x["aggregate_metrics"]["precision@3"]
        )
        analysis["best_config"] = best_config["config_id"]
        analysis["best_config_p3"] = best_config["aggregate_metrics"]["precision@3"]

        return analysis

    def generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on analysis
        """
        recommendations = []

        # Analyze knowledge ablation
        ablation = self.knowledge_ablation_analysis()

        if ablation.get("error"):
            return ["Run knowledge ablation experiment first"]

        # Recommendation 1: RAG value
        if ablation.get("rag_helps"):
            improvement = ablation["rag_improvement"] * 100
            recommendations.append(
                f"[OK] KEEP RAG: Improves accuracy by {improvement:.1f}% over baseline (P@3)"
            )
        else:
            recommendations.append(
                f"[X] REMOVE RAG: Decreases accuracy. Use keyword ranking only."
            )

        # Recommendation 2: FDA labels
        if ablation.get("fda_labels_help"):
            improvement = ablation["fda_improvement"] * 100
            recommendations.append(
                f"[OK] INCLUDE FDA LABELS: Adds {improvement:.1f}% improvement over guidelines only"
            )
        else:
            recommendations.append(
                f"[!] FDA LABELS NOT HELPFUL: Consider removing to reduce noise"
            )

        # Recommendation 3: Trial corpus
        if ablation.get("corpus_impact_significant"):
            if ablation.get("trial_corpus_helps"):
                recommendations.append(
                    f"[OK] KEEP TRIAL CORPUS: Significantly improves accuracy"
                )
            else:
                recommendations.append(
                    f"[X] REMOVE TRIAL CORPUS: Significantly DECREASES accuracy (adds noise)"
                )
        else:
            recommendations.append(
                f"[!] TRIAL CORPUS: No significant impact. Consider removing to reduce vectorstore size."
            )

        # Recommendation 4: Best configuration
        best = ablation.get("best_config")
        best_p3 = ablation.get("best_config_p3", 0)
        recommendations.append(
            f"🏆 OPTIMAL CONFIG: Use '{best}' (P@3 = {best_p3:.2%})"
        )

        return recommendations

    def print_report(self, experiment_name: str = "knowledge_ablation"):
        """Print comprehensive analysis report"""
        print("\n" + "="*80)
        print("RAG EVALUATION ANALYSIS REPORT")
        print("="*80)

        # 1. Configuration comparison table
        print("\n[CHART] CONFIGURATION COMPARISON")
        print("-" * 80)
        df = self.create_comparison_table(experiment_name)
        print(df.to_string(index=False))

        # 2. Knowledge ablation analysis
        print("\n\n🔬 KNOWLEDGE ABLATION ANALYSIS")
        print("-" * 80)
        ablation = self.knowledge_ablation_analysis()

        if not ablation.get("error"):
            print(f"\nRAG Effectiveness:")
            print(f"  RAG helps: {ablation.get('rag_helps', 'N/A')}")
            print(f"  Improvement: {ablation.get('rag_improvement', 0)*100:+.1f}%")
            print(f"  Statistically significant: {ablation.get('rag_vs_control_significant', 'N/A')}")

            print(f"\nFDA Labels Impact:")
            print(f"  FDA labels help: {ablation.get('fda_labels_help', 'N/A')}")
            print(f"  Improvement: {ablation.get('fda_improvement', 0)*100:+.1f}%")

            print(f"\nTrial Corpus Impact:")
            print(f"  Trial corpus helps: {ablation.get('trial_corpus_helps', 'N/A')}")
            print(f"  Impact: {ablation.get('corpus_impact', 0)*100:+.1f}%")
            print(f"  Statistically significant: {ablation.get('corpus_impact_significant', 'N/A')}")

        # 3. Recommendations
        print("\n\n💡 RECOMMENDATIONS")
        print("-" * 80)
        recommendations = self.generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        # 4. Statistical tests
        print("\n\n📈 STATISTICAL SIGNIFICANCE TESTS")
        print("-" * 80)

        # Test key comparisons
        tests = [
            ("control", "guidelines_only", "No RAG vs Guidelines Only"),
            ("guidelines_only", "guidelines_fda", "Guidelines Only vs Guidelines+FDA"),
            ("no_trial_corpus", "current_system", "Without Corpus vs With Corpus")
        ]

        for config1, config2, description in tests:
            result = self.statistical_significance_test(config1, config2)
            if not result.get("error"):
                print(f"\n{description}:")
                print(f"  {config1}: {result['config1_mean']:.2%}")
                print(f"  {config2}: {result['config2_mean']:.2%}")
                print(f"  Difference: {result['mean_difference']:.2%}")
                print(f"  p-value: {result['p_value']:.4f}")
                print(f"  Significant: {result['significant_at_0.05']}")
                print(f"  Effect size: {result['effect_size']} (Cohen's d = {result['cohens_d']:.2f})")

        print("\n" + "="*80)
        print("END OF REPORT")
        print("="*80 + "\n")


def main():
    """Analyze existing results"""
    analyzer = ResultsAnalyzer()

    if not analyzer.experiments:
        print("No experiments found. Run evaluator first.")
        print("Usage: python evaluation/rag_evaluator.py")
        return

    # Print comprehensive report
    analyzer.print_report("knowledge_ablation")

    # Save report to file
    report_file = Path("evaluation/results/analysis_report.txt")
    # TODO: Redirect print to file


if __name__ == "__main__":
    main()
