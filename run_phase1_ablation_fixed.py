"""
Phase 1 Ablation Experiment - WITH UNICODE FIXES
Tests RAG vs No-RAG performance with proper encoding
"""
import os
import sys

# FIX 1: Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# FIX 2: Set environment variable for subprocess calls
os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from evaluation.rag_evaluator import RAGEvaluator


def run_phase1_experiment():
    """
    Phase 1: Knowledge Ablation Study
    Compare Control (No RAG) vs RAG-Enhanced
    """

    print("="*80)
    print("PHASE 1: KNOWLEDGE ABLATION EXPERIMENT")
    print("Testing: RAG vs No-RAG Performance")
    print("="*80)

    # Load test cases
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        test_data = json.load(f)

    test_cases = test_data["test_cases"]
    print(f"\n[INFO] Loaded {len(test_cases)} test cases")

    # Define experimental configurations
    configs = [
        {
            "name": "Control (No RAG)",
            "use_rag": False,
            "description": "Baseline: Keyword matching + filters only"
        },
        {
            "name": "RAG-Enhanced",
            "use_rag": True,
            "description": "Full system: RAG + knowledge-enhanced ranking"
        }
    ]

    # Run experiments
    all_results = []

    for config_idx, config in enumerate(configs, 1):
        print(f"\n{'='*80}")
        print(f"CONFIGURATION {config_idx}/{len(configs)}: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"{'='*80}")

        # Initialize evaluator for this configuration
        evaluator = RAGEvaluator(use_rag=config["use_rag"])

        config_results = []
        successful = 0
        failed = 0

        # Evaluate each test case
        for i, test_case in enumerate(test_cases, 1):
            case_id = test_case["case_id"]

            print(f"\n[{i}/{len(test_cases)}] Testing: {case_id}")

            try:
                # Run evaluation
                result = evaluator.evaluate_test_case(test_case)

                # Add configuration metadata
                result["config_name"] = config["name"]
                result["test_case_id"] = case_id

                config_results.append(result)

                # Print metrics (sanitize any Unicode)
                metrics = result["metrics"]
                print(f"  Precision@5: {metrics['precision@5']:.1%}")
                print(f"  MRR: {metrics['mrr']:.3f}")
                print(f"  Found: {metrics['ground_truth_found']}/{len(test_case['ground_truth_trials'])}")

                successful += 1

            except Exception as e:
                # Sanitize error message for display
                error_msg = str(e)[:100].encode('ascii', 'replace').decode('ascii')
                print(f"  [ERROR] {error_msg}")

                # Log failed case
                config_results.append({
                    "config_name": config["name"],
                    "test_case_id": case_id,
                    "success": False,
                    "error": str(e)[:200]  # Keep full error in JSON
                })

                failed += 1

        # Summary for this configuration
        print(f"\n{'='*80}")
        print(f"CONFIGURATION SUMMARY: {config['name']}")
        print(f"{'='*80}")
        print(f"Successful: {successful}/{len(test_cases)}")
        print(f"Failed: {failed}/{len(test_cases)}")

        if successful > 0:
            # Calculate aggregate metrics
            valid_results = [r for r in config_results if r.get("success", True)]

            avg_p1 = sum(r["metrics"]["precision@1"] for r in valid_results) / len(valid_results)
            avg_p5 = sum(r["metrics"]["precision@5"] for r in valid_results) / len(valid_results)
            avg_mrr = sum(r["metrics"]["mrr"] for r in valid_results) / len(valid_results)

            print(f"\nAverage Metrics:")
            print(f"  Precision@1: {avg_p1:.1%}")
            print(f"  Precision@5: {avg_p5:.1%}")
            print(f"  MRR: {avg_mrr:.3f}")

        all_results.extend(config_results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evaluation/results/phase1_ablation_{timestamp}.json"

    output = {
        "experiment": "Phase 1 Knowledge Ablation",
        "timestamp": timestamp,
        "configurations": len(configs),
        "test_cases": len(test_cases),
        "results": all_results
    }

    Path("evaluation/results").mkdir(parents=True, exist_ok=True)

    with open(results_file, "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"[COMPLETE] Experiment finished")
    print(f"Results saved to: {results_file}")
    print(f"{'='*80}")

    return results_file


if __name__ == "__main__":
    print("\n[ENCODING] UTF-8 mode enabled for Windows compatibility")
    run_phase1_experiment()
