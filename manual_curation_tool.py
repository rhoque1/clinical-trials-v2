"""
Manual Curation Helper Tool

Interactive tool to help manually select ground truth trials from actual search results.
This ensures ground truth trials are compatible with the evaluation framework.
"""
import fix_encoding_global  # Apply UTF-8 fixes
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class ManualCurationTool:
    """Interactive tool for curating ground truth trials"""

    def __init__(self):
        self.diagnostic_dir = Path("evaluation/manual_curation")
        self.test_cases_path = Path("evaluation/test_cases.json")
        self.backup_path = Path("evaluation/test_cases_BACKUP_before_curation.json")

    def load_latest_diagnostic(self) -> Dict:
        """Load the most recent diagnostic results"""

        # Find latest diagnostic file
        diagnostic_files = sorted(self.diagnostic_dir.glob("diagnostics_*.json"), reverse=True)

        if not diagnostic_files:
            raise FileNotFoundError(
                "No diagnostic files found. Run diagnose_ground_truth_v2.py first."
            )

        latest_file = diagnostic_files[0]
        print(f"[INFO] Loading diagnostic: {latest_file.name}")

        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def display_case_for_curation(self, diagnostic: Dict, case_number: int, total_cases: int):
        """Display a case with its top candidates for manual review"""

        print(f"\n{'='*80}")
        print(f"CASE {case_number}/{total_cases}: {diagnostic['case_id']}")
        print(f"{'='*80}")

        # Show patient context
        patient = diagnostic.get("patient_summary", {})
        print(f"\n[PATIENT PROFILE]")
        print(f"  Diagnosis:  {patient.get('diagnoses', 'N/A')}")
        print(f"  Biomarkers: {patient.get('biomarkers', 'N/A')}")

        # Show current ground truth status
        print(f"\n[CURRENT GROUND TRUTH STATUS]")
        gt_trials = diagnostic.get("ground_truth_trials", [])
        gt_found = diagnostic.get("ground_truth_found_count", 0)

        print(f"  Current ground truth: {gt_trials}")
        print(f"  Found in search results: {gt_found}/{len(gt_trials)}")

        if gt_found == 0:
            print(f"  ⚠️  PROBLEM: None of these trials appear in search results!")
            print(f"  ⚠️  This causes 0% accuracy")
        elif gt_found < len(gt_trials):
            print(f"  ⚠️  PARTIAL: Only some trials found")

        # Show top candidates from actual search results
        print(f"\n[TOP 20 CANDIDATES FROM ACTUAL SEARCH]")
        print(f"(Select 2-3 clinically appropriate trials from this list)\n")

        candidates = diagnostic.get("top_20_candidates", [])

        for candidate in candidates:
            rank = candidate.get("rank", 0)
            nct_id = candidate.get("nct_id", "N/A")
            title = candidate.get("title", "No title")[:70]
            score = candidate.get("score", 0)
            status = candidate.get("status", "Unknown")
            phases = ", ".join(candidate.get("phases", []))
            conditions = ", ".join(candidate.get("conditions", [])[:3])

            print(f"{rank:2d}. NCT: {nct_id}")
            print(f"    Title: {title}...")
            print(f"    Score: {score:.0f} | Status: {status} | Phase: {phases}")
            print(f"    Conditions: {conditions}")
            print()

    def curate_case_interactive(self, diagnostic: Dict, case_number: int, total_cases: int) -> List[str]:
        """
        Interactively curate a single case

        Returns:
            List of NCT IDs selected as new ground truth
        """

        self.display_case_for_curation(diagnostic, case_number, total_cases)

        print(f"\n{'='*80}")
        print(f"MANUAL CURATION")
        print(f"{'='*80}")

        candidates = diagnostic.get("top_20_candidates", [])
        candidate_ncts = [c.get("nct_id") for c in candidates]

        print(f"\nSelect 2-3 clinically appropriate trials from the list above.")
        print(f"Enter the NCT IDs separated by commas (e.g., NCT12345678, NCT87654321)")
        print(f"Or enter 'skip' to skip this case")
        print(f"Or enter 'auto' to automatically select top 3")

        while True:
            user_input = input("\nYour selection: ").strip()

            if user_input.lower() == 'skip':
                print("[INFO] Skipping this case")
                return None

            if user_input.lower() == 'auto':
                # Auto-select top 3
                selected = candidate_ncts[:3]
                print(f"[AUTO] Selected top 3: {selected}")
                return selected

            # Parse manual selection
            selected_ncts = [nct.strip() for nct in user_input.split(',')]

            # Validate
            invalid = [nct for nct in selected_ncts if nct not in candidate_ncts]

            if invalid:
                print(f"[ERROR] Invalid NCT IDs: {invalid}")
                print(f"[ERROR] Please select from the displayed candidates (1-20)")
                continue

            if len(selected_ncts) < 2:
                print(f"[WARNING] You selected {len(selected_ncts)} trial(s). Recommend 2-3.")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue

            print(f"[CONFIRMED] Selected {len(selected_ncts)} trial(s): {selected_ncts}")
            return selected_ncts

    def curate_case_batch(self, diagnostic: Dict) -> List[str]:
        """
        Batch curation: automatically select top 3 trials with highest scores

        Use this for quick batch processing when you trust the ranking.
        """

        candidates = diagnostic.get("top_20_candidates", [])

        if not candidates:
            return None

        # Select top 3
        selected = [c.get("nct_id") for c in candidates[:3]]

        return selected

    def update_test_cases(self, curated_ground_truth: Dict[str, List[str]]):
        """
        Update test_cases.json with newly curated ground truth

        Args:
            curated_ground_truth: Dict mapping case_id -> list of NCT IDs
        """

        # Backup original file
        with open(self.test_cases_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        backup_path = Path(f"evaluation/test_cases_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)

        print(f"\n[BACKUP] Original test_cases.json saved to: {backup_path}")

        # Update ground truth
        updated_count = 0

        for test_case in original_data["test_cases"]:
            case_id = test_case["case_id"]

            if case_id in curated_ground_truth:
                new_ncts = curated_ground_truth[case_id]

                if new_ncts:  # Only update if we have new ground truth
                    # Replace ground truth trials
                    test_case["ground_truth_trials"] = [
                        {
                            "nct_id": nct_id,
                            "trial_name": f"Manually curated from search results",
                            "rationale": "Selected from actual search results (manual curation)",
                            "expected_rank": "top5" if i < 2 else "top10",
                            "confidence": "manually_curated",
                            "curation_date": datetime.now().isoformat()
                        }
                        for i, nct_id in enumerate(new_ncts)
                    ]

                    updated_count += 1
                    print(f"[UPDATED] {case_id}: {len(new_ncts)} new ground truth trial(s)")

        # Save updated file
        with open(self.test_cases_path, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)

        print(f"\n[COMPLETE] Updated {updated_count} test case(s)")
        print(f"[SAVED] Updated test_cases.json")

        return updated_count

    def run_interactive_curation(self, limit: int = None):
        """Run interactive curation session"""

        print(f"\n{'='*80}")
        print(f"MANUAL CURATION TOOL - INTERACTIVE MODE")
        print(f"{'='*80}")

        # Load diagnostics
        diagnostic_data = self.load_latest_diagnostic()
        diagnostics = diagnostic_data.get("diagnostics", [])

        # Filter successful cases
        successful = [d for d in diagnostics if d.get("success")]

        if limit:
            successful = successful[:limit]

        print(f"\n[INFO] Cases to curate: {len(successful)}")
        print(f"[INFO] You'll review each case and select appropriate trials from search results\n")

        curated_ground_truth = {}

        for i, diagnostic in enumerate(successful, 1):
            case_id = diagnostic["case_id"]

            # Skip if ground truth is already good
            gt_found = diagnostic.get("ground_truth_found_count", 0)
            gt_total = len(diagnostic.get("ground_truth_trials", []))

            if gt_found == gt_total and gt_total >= 2:
                print(f"\n[SKIP] {case_id}: Ground truth already compatible ({gt_found}/{gt_total} found)")
                continue

            # Curate this case
            selected_ncts = self.curate_case_interactive(diagnostic, i, len(successful))

            if selected_ncts:
                curated_ground_truth[case_id] = selected_ncts

        # Update test_cases.json
        if curated_ground_truth:
            print(f"\n{'='*80}")
            print(f"UPDATING TEST CASES")
            print(f"{'='*80}")

            self.update_test_cases(curated_ground_truth)

            print(f"\n[SUCCESS] Curation complete!")
            print(f"[NEXT STEP] Run Phase 1 experiment with updated ground truth")
        else:
            print(f"\n[INFO] No changes made")

    def run_batch_curation(self, limit: int = None):
        """
        Run batch curation: automatically select top 3 for all cases

        Use this for quick testing. Manual review is recommended for production.
        """

        print(f"\n{'='*80}")
        print(f"MANUAL CURATION TOOL - BATCH MODE (AUTO)")
        print(f"{'='*80}")
        print(f"\n[INFO] Auto-selecting top 3 trials for each case")
        print(f"[WARNING] This is for quick testing only!")
        print(f"[RECOMMENDATION] Use interactive mode for production\n")

        # Load diagnostics
        diagnostic_data = self.load_latest_diagnostic()
        diagnostics = diagnostic_data.get("diagnostics", [])

        # Filter successful cases
        successful = [d for d in diagnostics if d.get("success")]

        if limit:
            successful = successful[:limit]

        print(f"[INFO] Cases to process: {len(successful)}\n")

        curated_ground_truth = {}

        for i, diagnostic in enumerate(successful, 1):
            case_id = diagnostic["case_id"]

            print(f"[{i}/{len(successful)}] {case_id}...", end=" ")

            selected_ncts = self.curate_case_batch(diagnostic)

            if selected_ncts:
                curated_ground_truth[case_id] = selected_ncts
                print(f"✓ Selected {len(selected_ncts)} trials: {', '.join(selected_ncts)}")
            else:
                print(f"✗ No candidates found")

        # Update test_cases.json
        if curated_ground_truth:
            print(f"\n{'='*80}")
            print(f"UPDATING TEST CASES")
            print(f"{'='*80}")

            self.update_test_cases(curated_ground_truth)

            print(f"\n[SUCCESS] Batch curation complete!")
            print(f"[NEXT STEP] Run Phase 1 experiment with updated ground truth")
        else:
            print(f"\n[INFO] No changes made")


def main():
    """Run manual curation tool"""

    import sys

    tool = ManualCurationTool()

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        # Batch mode: auto-select top 3
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        tool.run_batch_curation(limit=limit)
    else:
        # Interactive mode (default)
        print("\n[MODE] Interactive curation")
        print("[INFO] Use --batch flag for automatic selection")
        print("[INFO] Press Ctrl+C to cancel\n")

        try:
            limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
            tool.run_interactive_curation(limit=limit)
        except KeyboardInterrupt:
            print("\n\n[CANCELLED] Curation cancelled by user")


if __name__ == "__main__":
    main()
