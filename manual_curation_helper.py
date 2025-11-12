"""
Manual Ground Truth Curation Helper

Runs actual system searches for test cases and displays what trials
are REALLY being retrieved, allowing manual selection of appropriate
ground truth from actual results.

This solves the evaluation framework mismatch where automatically
selected ground truth trials don't appear in system searches.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict

# Fix UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode


async def run_actual_search(test_case: Dict) -> Dict:
    """
    Run the ACTUAL system search for a test case

    Returns what the system REALLY retrieves
    """
    print(f"\n{'='*80}")
    print(f"Running ACTUAL system search for: {test_case['case_id']}")
    print(f"{'='*80}")
    print(f"Patient: {test_case['patient_summary']}")
    print(f"Biomarkers: {', '.join(test_case['key_biomarkers'])}")

    # Create workflow engine
    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

    # Create patient profile from test case
    patient_profile = {
        "success": True,
        "demographics": {"age": 40, "sex": "Female"},
        "diagnoses": test_case["patient_summary"],
        "biomarkers": ", ".join(test_case["key_biomarkers"]),
        "treatment_history": {"prior_therapies": []},
        "search_terms": test_case["key_biomarkers"]
    }

    # Run trial discovery (baseline search)
    print("\n[1] Running baseline trial discovery...")
    discovery_result = await engine.run_trial_discovery(patient_profile)
    baseline_trials = discovery_result['ranked_trials']

    print(f"[OK] Found {len(baseline_trials)} trials via baseline search")

    # Run knowledge enhancement (RAG-based ranking)
    print("\n[2] Running knowledge enhancement (RAG)...")
    enhancement_result = await engine.run_knowledge_enhancement(
        patient_profile,
        baseline_trials
    )
    rag_trials = enhancement_result['ranked_trials']

    print(f"[OK] Re-ranked {len(rag_trials)} trials with RAG")

    return {
        "test_case_id": test_case["case_id"],
        "baseline_trials": baseline_trials,
        "rag_trials": rag_trials,
        "current_ground_truth": test_case["ground_truth_trials"]
    }


def display_trials(trials: List[Dict], title: str, max_display: int = 20):
    """Display trial results in readable format"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"Showing top {min(max_display, len(trials))} of {len(trials)} trials\n")

    for i, trial in enumerate(trials[:max_display], 1):
        nct_id = trial.get('nct_id', 'N/A')
        title_text = trial.get('title', 'No title')[:70]
        phase = trial.get('phase', 'N/A')
        status = trial.get('status', 'N/A')
        score = trial.get('score', 0)

        # Sanitize for Windows console
        title_safe = title_text.encode('ascii', 'replace').decode('ascii')

        print(f"{i:2d}. {nct_id}")
        print(f"    Title: {title_safe}...")
        print(f"    Phase: {phase} | Status: {status} | Score: {score:.3f}")

        # Show conditions/interventions if available
        conditions = trial.get('conditions', [])
        interventions = trial.get('interventions', [])

        if conditions:
            cond_str = ', '.join(conditions[:3]).encode('ascii', 'replace').decode('ascii')
            print(f"    Conditions: {cond_str}")

        if interventions:
            interv_str = ', '.join(interventions[:3]).encode('ascii', 'replace').decode('ascii')
            print(f"    Interventions: {interv_str}")

        print()


def check_ground_truth_coverage(search_results: Dict):
    """Check if current ground truth trials appear in search results"""
    baseline_nct_ids = [t.get('nct_id') for t in search_results['baseline_trials']]
    rag_nct_ids = [t.get('nct_id') for t in search_results['rag_trials']]
    ground_truth_nct_ids = [gt['nct_id'] for gt in search_results['current_ground_truth']]

    print(f"\n{'='*80}")
    print("GROUND TRUTH COVERAGE CHECK")
    print(f"{'='*80}")

    print(f"\nCurrent ground truth trials:")
    for gt in search_results['current_ground_truth']:
        nct_id = gt['nct_id']
        name = gt['trial_name'][:60].encode('ascii', 'replace').decode('ascii')

        in_baseline = nct_id in baseline_nct_ids
        in_rag = nct_id in rag_nct_ids

        baseline_rank = baseline_nct_ids.index(nct_id) + 1 if in_baseline else "NOT FOUND"
        rag_rank = rag_nct_ids.index(nct_id) + 1 if in_rag else "NOT FOUND"

        status = "✓ FOUND" if in_baseline else "✗ MISSING"

        print(f"\n  {status} {nct_id}")
        print(f"  Name: {name}")
        print(f"  Baseline rank: {baseline_rank}")
        print(f"  RAG rank: {rag_rank}")

    found_count = sum(1 for nct in ground_truth_nct_ids if nct in baseline_nct_ids)

    print(f"\n{'='*80}")
    print(f"COVERAGE: {found_count}/{len(ground_truth_nct_ids)} ground truth trials found in search results")
    print(f"{'='*80}")

    if found_count == 0:
        print("\n⚠️  WARNING: ZERO ground truth trials found in search results!")
        print("   This explains the 0% evaluation accuracy.")
        print("   Ground truth must be selected from ACTUAL search results.")


def save_curation_report(search_results: Dict, output_dir: Path):
    """Save detailed report for manual curation"""
    output_dir.mkdir(parents=True, exist_ok=True)

    case_id = search_results['test_case_id']
    filename = output_dir / f"curation_report_{case_id}.json"

    # Prepare report data (top 30 trials for manual review)
    report = {
        "test_case_id": case_id,
        "current_ground_truth": search_results['current_ground_truth'],
        "baseline_top_30": [
            {
                "rank": i,
                "nct_id": t.get('nct_id'),
                "title": t.get('title', ''),
                "phase": t.get('phase', ''),
                "status": t.get('status', ''),
                "score": t.get('score'),
                "conditions": t.get('conditions', []),
                "interventions": t.get('interventions', [])
            }
            for i, t in enumerate(search_results['baseline_trials'][:30], 1)
        ],
        "rag_top_30": [
            {
                "rank": i,
                "nct_id": t.get('nct_id'),
                "title": t.get('title', ''),
                "phase": t.get('phase', ''),
                "status": t.get('status', ''),
                "score": t.get('score'),
                "guideline_score": t.get('guideline_score'),
                "conditions": t.get('conditions', []),
                "interventions": t.get('interventions', [])
            }
            for i, t in enumerate(search_results['rag_trials'][:30], 1)
        ],
        "instructions": "Manually select 2-3 clinically appropriate trials from the above lists as new ground truth"
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[SAVED] Curation report: {filename}")
    print("        Review this file to manually select appropriate ground truth trials")


async def curate_test_cases(case_ids: List[str]):
    """
    Run curation process for specified test cases

    Args:
        case_ids: List of case IDs to curate (e.g., ['cervical_pdl1_standard', 'lung_egfr_exon19'])
    """
    # Load test cases
    with open("evaluation/test_cases.json", "r", encoding='utf-8') as f:
        test_data = json.load(f)

    all_cases = test_data["test_cases"]

    # Filter to specified cases
    selected_cases = [tc for tc in all_cases if tc['case_id'] in case_ids]

    if not selected_cases:
        print(f"[ERROR] No test cases found matching: {case_ids}")
        return

    print(f"\n{'='*80}")
    print("MANUAL GROUND TRUTH CURATION")
    print(f"{'='*80}")
    print(f"Curating {len(selected_cases)} test cases:")
    for tc in selected_cases:
        print(f"  - {tc['case_id']}")
    print(f"{'='*80}")

    output_dir = Path("evaluation/manual_curation")

    for test_case in selected_cases:
        try:
            # Run actual system search
            search_results = await run_actual_search(test_case)

            # Display results
            display_trials(
                search_results['baseline_trials'],
                f"BASELINE SEARCH RESULTS: {test_case['case_id']}",
                max_display=20
            )

            display_trials(
                search_results['rag_trials'],
                f"RAG-ENHANCED RESULTS: {test_case['case_id']}",
                max_display=20
            )

            # Check if current ground truth is in results
            check_ground_truth_coverage(search_results)

            # Save detailed report for manual review
            save_curation_report(search_results, output_dir)

            print(f"\n{'='*80}")
            print(f"[OK] Curation data prepared for: {test_case['case_id']}")
            print(f"{'='*80}")

            # Small delay between cases
            await asyncio.sleep(2)

        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"\n[ERROR] Failed to curate {test_case['case_id']}: {error_msg}")

    print(f"\n{'='*80}")
    print("CURATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"1. Review curation reports in: {output_dir}/")
    print(f"2. For each case, manually select 2-3 clinically appropriate trials from ACTUAL results")
    print(f"3. Update evaluation/test_cases.json with new ground truth")
    print(f"4. Re-run Phase 1 experiment - should now show >0% accuracy")


async def main():
    """
    Main curation workflow

    Start with 3 representative cases as recommended in GROUND_TRUTH_ANALYSIS.md
    """
    # Select 3 diverse cases for initial curation
    initial_cases = [
        "cervical_pdl1_standard",    # Cervical cancer with PD-L1
        "lung_egfr_exon19",          # Lung cancer with EGFR mutation
        "melanoma_braf_v600e"        # Melanoma with BRAF V600E
    ]

    print("\n" + "="*80)
    print("MANUAL GROUND TRUTH CURATION HELPER")
    print("="*80)
    print("\nPurpose: Select ground truth from ACTUAL search results")
    print("Problem: Current ground truth trials don't appear in system searches")
    print("Solution: Run real searches and manually curate from actual results")
    print("="*80)

    await curate_test_cases(initial_cases)


if __name__ == "__main__":
    asyncio.run(main())
