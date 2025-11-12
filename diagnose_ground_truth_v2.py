"""
Ground Truth Diagnostic Tool v2

Analyzes why ground truth trials aren't appearing in search results
and provides actionable recommendations for manual curation.
"""
import fix_encoding_global  # Apply UTF-8 fixes
import json
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class GroundTruthDiagnostic:
    """Diagnose ground truth mismatch issues"""

    def __init__(self):
        self.test_cases_path = Path("evaluation/test_cases.json")
        self.sample_profiles_dir = Path("evaluation/sample_profiles")
        self.output_dir = Path("evaluation/manual_curation")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def diagnose_single_case(self, test_case: Dict) -> Dict:
        """
        Run diagnostic on a single test case

        Returns:
            - What trials the system actually finds
            - Whether ground truth appears in results
            - Top 20 candidates for manual curation
        """
        case_id = test_case["case_id"]
        print(f"\n{'='*80}")
        print(f"DIAGNOSING: {case_id}")
        print(f"{'='*80}")

        # Load patient profile
        profile_path = self.sample_profiles_dir / f"{case_id}.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            patient_profile = json.load(f)

        # Import workflow engine
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode

        engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

        # Run trial discovery (Phase 2)
        print(f"\n[1] Running trial discovery...")
        discovery_result = await engine.run_trial_discovery(patient_profile)

        if not discovery_result.get("success"):
            return {
                "case_id": case_id,
                "error": f"Discovery failed: {discovery_result.get('error')}",
                "success": False
            }

        # Get trials found
        trials_found = discovery_result.get("ranked_trials", [])
        print(f"    -> Found {len(trials_found)} trials")

        # Extract ground truth NCT IDs
        ground_truth_nct_ids = [gt["nct_id"] for gt in test_case["ground_truth_trials"]]
        print(f"\n[2] Ground truth trials: {ground_truth_nct_ids}")

        # Check if ground truth appears in results
        found_nct_ids = {trial.get("nct_id") for trial in trials_found}
        ground_truth_in_results = [nct for nct in ground_truth_nct_ids if nct in found_nct_ids]

        print(f"\n[3] Ground truth found in results: {len(ground_truth_in_results)}/{len(ground_truth_nct_ids)}")
        if ground_truth_in_results:
            print(f"    -> Found: {ground_truth_in_results}")
            for nct in ground_truth_in_results:
                # Find rank
                for rank, trial in enumerate(trials_found, 1):
                    if trial.get("nct_id") == nct:
                        print(f"       {nct} at rank #{rank}")
                        break
        else:
            print(f"    -> NONE of the ground truth trials appear in search results!")
            print(f"    -> This explains 0% accuracy")

        # Get top 20 for manual review
        top_20 = trials_found[:20]

        print(f"\n[4] Top 20 trials for manual curation:")
        print(f"    (These are what the system actually found)")
        for i, trial in enumerate(top_20, 1):
            nct_id = trial.get("nct_id", "N/A")
            title = trial.get("title", "No title")[:60]
            score = trial.get("score", 0)
            print(f"    {i:2d}. {nct_id} (score: {score:.0f}) - {title}...")

        # Extract patient summary for context
        diagnoses = patient_profile.get("diagnoses", [])
        biomarkers = patient_profile.get("biomarkers", [])

        # Handle both string and list formats
        if isinstance(diagnoses, str):
            diagnosis_str = diagnoses
        elif isinstance(diagnoses, list):
            diagnosis_str = ", ".join([
                d.get("cancer_type", "") if isinstance(d, dict) else str(d)
                for d in diagnoses
            ])
        else:
            diagnosis_str = ""

        if isinstance(biomarkers, str):
            biomarker_str = biomarkers
        elif isinstance(biomarkers, list):
            biomarker_str = ", ".join([
                f"{b.get('gene', '')} {b.get('variant', '')}" if isinstance(b, dict) else str(b)
                for b in biomarkers
            ])
        else:
            biomarker_str = ""

        print(f"\n[5] Patient context:")
        print(f"    Diagnosis: {diagnosis_str}")
        print(f"    Biomarkers: {biomarker_str}")

        # Return structured diagnostic data
        return {
            "case_id": case_id,
            "success": True,
            "patient_summary": {
                "diagnoses": diagnosis_str,
                "biomarkers": biomarker_str,
            },
            "ground_truth_trials": ground_truth_nct_ids,
            "ground_truth_found_count": len(ground_truth_in_results),
            "ground_truth_found": ground_truth_in_results,
            "total_trials_retrieved": len(trials_found),
            "top_20_candidates": [
                {
                    "rank": i,
                    "nct_id": trial.get("nct_id"),
                    "title": trial.get("title", ""),
                    "score": trial.get("score", 0),
                    "brief_summary": trial.get("brief_summary", "")[:200],
                    "conditions": trial.get("conditions", []),
                    "phases": trial.get("phases", []),
                    "status": trial.get("overall_status", "")
                }
                for i, trial in enumerate(top_20, 1)
            ]
        }

    async def diagnose_all_cases(self, limit: int = None):
        """Run diagnostics on all test cases"""

        print(f"\n{'='*80}")
        print(f"GROUND TRUTH DIAGNOSTIC ANALYSIS")
        print(f"{'='*80}")

        # Load test cases
        with open(self.test_cases_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data["test_cases"]

        if limit:
            test_cases = test_cases[:limit]
            print(f"\nAnalyzing first {limit} test cases (limit applied)")

        print(f"\nTotal cases to diagnose: {len(test_cases)}")

        all_diagnostics = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n\n{'#'*80}")
            print(f"# CASE {i}/{len(test_cases)}")
            print(f"{'#'*80}")

            try:
                diagnostic = await self.diagnose_single_case(test_case)
                all_diagnostics.append(diagnostic)

                # Delay between cases
                await asyncio.sleep(2)

            except Exception as e:
                print(f"\n[ERROR] Failed to diagnose {test_case['case_id']}: {str(e)}")
                import traceback
                traceback.print_exc()

                all_diagnostics.append({
                    "case_id": test_case["case_id"],
                    "success": False,
                    "error": str(e)
                })

        # Generate summary report
        self.generate_summary_report(all_diagnostics)

        # Save full diagnostics
        output_file = self.output_dir / f"diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "cases_analyzed": len(test_cases),
                "diagnostics": all_diagnostics
            }, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*80}")
        print(f"[COMPLETE] Diagnostic analysis finished")
        print(f"{'='*80}")
        print(f"\nFull diagnostics saved to: {output_file}")
        print(f"\nNext step: Use manual curation tool to select new ground truth")

        return all_diagnostics

    def generate_summary_report(self, diagnostics: List[Dict]):
        """Generate summary statistics"""

        successful = [d for d in diagnostics if d.get("success")]

        print(f"\n\n{'='*80}")
        print(f"SUMMARY REPORT")
        print(f"{'='*80}")

        print(f"\nCases analyzed: {len(diagnostics)}")
        print(f"Successful: {len(successful)}")

        if not successful:
            print("\n[WARNING] No successful diagnostics to analyze")
            return

        # Count how many cases have ANY ground truth in results
        cases_with_gt = sum(1 for d in successful if d.get("ground_truth_found_count", 0) > 0)
        cases_without_gt = len(successful) - cases_with_gt

        print(f"\n{'='*80}")
        print(f"GROUND TRUTH COVERAGE")
        print(f"{'='*80}")
        print(f"Cases with ground truth in search results: {cases_with_gt}/{len(successful)} ({cases_with_gt/len(successful)*100:.1f}%)")
        print(f"Cases with NO ground truth in results: {cases_without_gt}/{len(successful)} ({cases_without_gt/len(successful)*100:.1f}%)")

        if cases_without_gt > 0:
            print(f"\n[CRITICAL] {cases_without_gt} cases have ground truth trials that don't appear in search results!")
            print(f"[ACTION REQUIRED] Manual curation needed for these cases:")

            for d in successful:
                if d.get("ground_truth_found_count", 0) == 0:
                    print(f"  - {d['case_id']}")

        print(f"\n{'='*80}")
        print(f"RECOMMENDATION")
        print(f"{'='*80}")

        if cases_without_gt >= len(successful) * 0.5:  # More than 50% need curation
            print(f"\n[CRITICAL] Most test cases have incompatible ground truth.")
            print(f"")
            print(f"You have two options:")
            print(f"")
            print(f"Option 1: Manual Curation (RECOMMENDED)")
            print(f"  - Review the top_20_candidates for each case")
            print(f"  - Select 2-3 clinically appropriate trials from ACTUAL results")
            print(f"  - Update test_cases.json with new ground truth")
            print(f"")
            print(f"Option 2: Pivot Evaluation Strategy")
            print(f"  - Change metrics from 'Precision@K' to 'Coverage@K'")
            print(f"  - Measure whether system finds trials at all (less strict)")
            print(f"")
            print(f"Estimated time for Option 1: {len(successful) * 10} minutes ({len(successful)} cases × 10 min/case)")
        else:
            print(f"\n[GOOD] Most test cases have compatible ground truth!")
            print(f"[ACTION] Fix the {cases_without_gt} cases that need curation")


async def main():
    """Run diagnostic analysis"""

    print("\n[ENCODING] UTF-8 mode enabled")
    print("[INFO] This will analyze why ground truth trials aren't appearing in search results\n")

    diagnostic = GroundTruthDiagnostic()

    # For initial testing, analyze first 5 cases
    # Change to None to analyze all cases
    LIMIT = 5

    results = await diagnostic.diagnose_all_cases(limit=LIMIT)

    print(f"\n[DONE] Check evaluation/manual_curation/ for detailed analysis")


if __name__ == "__main__":
    asyncio.run(main())
