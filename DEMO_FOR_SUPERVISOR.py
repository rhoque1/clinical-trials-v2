"""
DEMO: RAG-Enhanced Search vs General Search
============================================

This script demonstrates the difference between:
1. GENERAL SEARCH: Keyword matching + basic ranking (Phase 2 only)
2. RAG-ENHANCED: General search + knowledge-based re-ranking (Phase 2 + Phase 3)

Usage:
    python DEMO_FOR_SUPERVISOR.py

The script will run BOTH methods on the same patient and show side-by-side results.
"""
import fix_encoding_global
import asyncio
import json
from pathlib import Path
from datetime import datetime


class RAGDemo:
    """Demo comparing General Search vs RAG-Enhanced Search"""

    def __init__(self):
        self.test_case_id = "lung_egfr_exon19"  # Example: Lung cancer with EGFR mutation

    async def run_general_search(self, patient_profile):
        """
        METHOD 1: GENERAL SEARCH (Baseline)
        - Uses ClinicalTrials.gov API
        - Keyword matching
        - Basic relevance scoring by LLM
        - NO knowledge base enhancement
        """
        print(f"\n{'='*80}")
        print(f"METHOD 1: GENERAL SEARCH (Baseline - No RAG)")
        print(f"{'='*80}")
        print(f"\nHow it works:")
        print(f"  1. Search ClinicalTrials.gov with keywords")
        print(f"  2. Rank trials by relevance (LLM scoring)")
        print(f"  3. Return top matches")
        print(f"\nThis is Phase 2 only (Trial Discovery)\n")

        # Modify workflow to disable RAG
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode

        # Set flag to disable RAG
        import agents.workflow_engine as wf_module
        original_flag = getattr(wf_module, 'DISABLE_RAG_FOR_EXPERIMENT', False)
        wf_module.DISABLE_RAG_FOR_EXPERIMENT = True

        try:
            engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

            # Run trial discovery
            discovery_result = await engine.run_trial_discovery(patient_profile)

            if not discovery_result.get("success"):
                print(f"[ERROR] Trial discovery failed")
                return None

            trials = discovery_result.get("ranked_trials", [])

            print(f"[RESULTS] Found {len(trials)} trials")
            print(f"\nTop 5 Trials (General Search):")
            print(f"{'-'*80}")

            for i, trial in enumerate(trials[:5], 1):
                nct_id = trial.get("nct_id", "N/A")
                title = trial.get("title", "No title")[:60]
                score = trial.get("score", 0)

                print(f"\n{i}. {nct_id}")
                print(f"   Title: {title}...")
                print(f"   Score: {score}")

            return trials

        finally:
            # Restore original flag
            wf_module.DISABLE_RAG_FOR_EXPERIMENT = original_flag

    async def run_rag_enhanced_search(self, patient_profile):
        """
        METHOD 2: RAG-ENHANCED SEARCH (Your System)
        - Starts with general search (same as Method 1)
        - Then applies RAG: retrieves relevant knowledge from:
          * NCCN clinical guidelines
          * FDA drug labels
          * Biomarker databases
        - Re-ranks trials using this clinical knowledge
        - More accurate and clinically informed
        """
        print(f"\n\n{'='*80}")
        print(f"METHOD 2: RAG-ENHANCED SEARCH (Your Full System)")
        print(f"{'='*80}")
        print(f"\nHow it works:")
        print(f"  1. Search ClinicalTrials.gov with keywords (same as Method 1)")
        print(f"  2. Rank trials by relevance (same as Method 1)")
        print(f"  3. Retrieve relevant clinical knowledge from RAG:")
        print(f"     - NCCN treatment guidelines")
        print(f"     - FDA drug labels")
        print(f"     - Biomarker information")
        print(f"  4. Re-rank using clinical knowledge")
        print(f"  5. Return knowledge-enhanced matches")
        print(f"\nThis is Phase 2 + Phase 3 (Trial Discovery + Knowledge Enhancement)\n")

        # Use full workflow with RAG enabled
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode

        # Ensure RAG is enabled
        import agents.workflow_engine as wf_module
        original_flag = getattr(wf_module, 'DISABLE_RAG_FOR_EXPERIMENT', False)
        wf_module.DISABLE_RAG_FOR_EXPERIMENT = False

        try:
            engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

            # Run trial discovery
            discovery_result = await engine.run_trial_discovery(patient_profile)

            if not discovery_result.get("success"):
                print(f"[ERROR] Trial discovery failed")
                return None

            trials = discovery_result.get("ranked_trials", [])

            # Run RAG enhancement
            print(f"\n[RUNNING] Knowledge enhancement with RAG...")

            enhancement_result = await engine.run_knowledge_enhancement(
                patient_profile,
                trials
            )

            if not enhancement_result.get("success"):
                print(f"[ERROR] Knowledge enhancement failed")
                return trials  # Return un-enhanced results

            enhanced_trials = enhancement_result.get("ranked_trials", [])

            print(f"[RESULTS] Enhanced {len(enhanced_trials)} trials with clinical knowledge")
            print(f"\nTop 5 Trials (RAG-Enhanced):")
            print(f"{'-'*80}")

            for i, trial in enumerate(enhanced_trials[:5], 1):
                nct_id = trial.get("nct_id", "N/A")
                title = trial.get("title", "No title")[:60]
                score = trial.get("score", 0)

                print(f"\n{i}. {nct_id}")
                print(f"   Title: {title}...")
                print(f"   Score: {score}")

            return enhanced_trials

        finally:
            # Restore original flag
            wf_module.DISABLE_RAG_FOR_EXPERIMENT = original_flag

    async def compare_results(self, general_trials, rag_trials):
        """Compare the two methods side-by-side"""

        print(f"\n\n{'='*80}")
        print(f"COMPARISON: General Search vs RAG-Enhanced")
        print(f"{'='*80}\n")

        # Get top 10 from each
        general_top10 = [t.get("nct_id") for t in general_trials[:10]]
        rag_top10 = [t.get("nct_id") for t in rag_trials[:10]]

        # Compare rankings
        print(f"{'Rank':<6} {'General Search':<20} {'RAG-Enhanced':<20} {'Change':<10}")
        print(f"{'-'*70}")

        for i in range(10):
            general_nct = general_top10[i] if i < len(general_top10) else "-"
            rag_nct = rag_top10[i] if i < len(rag_top10) else "-"

            # Calculate change
            change = ""
            if general_nct in rag_top10:
                rag_rank = rag_top10.index(general_nct) + 1
                diff = (i + 1) - rag_rank
                if diff > 0:
                    change = f"↓ {diff}"
                elif diff < 0:
                    change = f"↑ {abs(diff)}"
                else:
                    change = "="
            elif general_nct != "-":
                change = "OUT"

            print(f"{i+1:<6} {general_nct:<20} {rag_nct:<20} {change:<10}")

        # Count differences
        different = sum(1 for i in range(min(10, len(general_top10), len(rag_top10)))
                       if general_top10[i] != rag_top10[i])

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"\nTrials in top 10 that changed: {different}/10")
        print(f"\nInterpretation:")
        print(f"  - '↑ N' means RAG moved this trial UP by N positions")
        print(f"  - '↓ N' means RAG moved this trial DOWN by N positions")
        print(f"  - 'OUT' means trial dropped out of top 10")
        print(f"  - '=' means no change in ranking")

    async def run_demo(self):
        """Run complete demo"""

        print("\n" + "="*80)
        print("DEMO: RAG-Enhanced Clinical Trial Matching")
        print("="*80)
        print(f"\nTest Case: {self.test_case_id}")
        print(f"Patient: 62M with metastatic NSCLC, EGFR exon 19 deletion")
        print("\n" + "="*80)

        # Load patient profile
        profile_path = Path(f"evaluation/sample_profiles/{self.test_case_id}.json")

        if not profile_path.exists():
            print(f"\n[ERROR] Patient profile not found: {profile_path}")
            print(f"[INFO] Available profiles:")
            for p in Path("evaluation/sample_profiles").glob("*.json"):
                print(f"  - {p.stem}")
            return

        with open(profile_path, 'r', encoding='utf-8') as f:
            patient_profile = json.load(f)

        # Run both methods
        general_trials = await self.run_general_search(patient_profile)

        if not general_trials:
            print("\n[ERROR] General search failed")
            return

        await asyncio.sleep(2)  # Brief pause

        rag_trials = await self.run_rag_enhanced_search(patient_profile)

        if not rag_trials:
            print("\n[ERROR] RAG-enhanced search failed")
            return

        # Compare
        await self.compare_results(general_trials, rag_trials)

        # Save results
        output_dir = Path("evaluation/demo_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"demo_comparison_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "test_case": self.test_case_id,
                "general_search_top10": [
                    {"rank": i+1, "nct_id": t.get("nct_id"), "score": t.get("score")}
                    for i, t in enumerate(general_trials[:10])
                ],
                "rag_enhanced_top10": [
                    {"rank": i+1, "nct_id": t.get("nct_id"), "score": t.get("score")}
                    for i, t in enumerate(rag_trials[:10])
                ]
            }, f, indent=2, ensure_ascii=False)

        print(f"\n\n{'='*80}")
        print(f"DEMO COMPLETE")
        print(f"{'='*80}")
        print(f"\nResults saved to: {output_file}")
        print(f"\nConclusion:")
        print(f"  RAG-enhanced search uses clinical knowledge to improve ranking.")
        print(f"  The differences you see above show how RAG re-prioritizes trials")
        print(f"  based on NCCN guidelines, FDA labels, and biomarker information.")


async def main():
    """Run the demo"""
    demo = RAGDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("\n[ENCODING] UTF-8 mode enabled")
    print("[INFO] Starting RAG vs General Search demo...\n")

    asyncio.run(main())
