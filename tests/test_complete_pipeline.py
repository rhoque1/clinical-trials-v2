"""
Test script for Complete Pipeline (Phase 4)
Tests end-to-end: PDF → Patient Profile → Trial Discovery → Eligibility Analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode


async def run_complete_pipeline():
    """Execute the complete clinical trial matching pipeline"""
    
    print("="*80)
    print("COMPLETE PIPELINE TEST - END-TO-END")
    print("="*80)
    
    # Initialize workflow engine
    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)
    
    # Path to test PDF (adjust if needed)
    pdf_path = "tccr.pdf"
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"\n❌ ERROR: PDF not found at {pdf_path}")
        print("Please ensure tap.pdf is in the project root directory")
        return
    
    print(f"\n✓ Found PDF: {pdf_path}")
    print(f"✓ Mode: AUTO (complete automation)")
    print("\nStarting pipeline execution...\n")
    
    # Run the complete workflow
    results = await engine.run_complete_workflow(pdf_path=pdf_path)
    
    # Check if successful
    if not results.get("success"):
        print(f"\n❌ Pipeline failed: {results.get('error', 'Unknown error')}")
        return
    
    # Display detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS BREAKDOWN")
    print("="*80)
    
    # Phase 1 Results
    patient_profile = results.get('patient_profile', {})
    demographics = patient_profile.get('demographics', {})
    diagnoses = patient_profile.get('diagnoses', {})
    biomarkers = patient_profile.get('biomarkers', {})
    
    print("\n📋 PHASE 1 - PATIENT PROFILE:")
    print(f"  Age: {demographics.get('age')} years")
    print(f"  Sex: {demographics.get('sex')}")
    # Handle diagnoses (string format from extraction)
    if isinstance(diagnoses, str):
        print(f"  Diagnosis: {diagnoses[:100]}...")
        stage = 'IIIB' if 'IIIB' in diagnoses else 'Unknown'
        print(f"  Stage: {stage}")
    else:
        print(f"  Diagnosis: {diagnoses.get('condition', 'Unknown')}")
        print(f"  Stage: {diagnoses.get('stage', 'Unknown')}")
        print(f"  Histology: {diagnoses.get('histology', 'Unknown')}")
    
    if biomarkers:
        print(f"  Biomarkers ({len(biomarkers)} identified):")
        # Handle both dict and list formats
        if isinstance(biomarkers, dict):
            for name, details in list(biomarkers.items())[:5]:
                print(f"    - {name}: {details}")
        elif isinstance(biomarkers, list):
            for marker in biomarkers[:5]:
                if isinstance(marker, dict):
                    print(f"    - {marker.get('name', 'Unknown')}: {marker.get('status', 'Unknown')}")
    
    search_terms = patient_profile.get('search_terms', [])
    print(f"  Search terms: {len(search_terms)} generated")
    if search_terms:
        print(f"    Examples: {search_terms[:3]}")
    
    # Phase 2 Results
    # Phase 2 Results
    trial_discovery = results.get('trial_discovery', {})
    ranked_trials = trial_discovery.get('ranked_trials', [])
    
    print(f"\n🔍 PHASE 2 - TRIAL DISCOVERY:")
    print(f"  Total trials found: {trial_discovery.get('total_found', 0)}")
    print(f"  Trials ranked: {len(ranked_trials)}")
    print(f"  Top match score: {trial_discovery.get('top_score', 0)}")
    
    if ranked_trials:
        print(f"\n  Top 5 Trials (before RAG):")
        for i, trial in enumerate(ranked_trials[:5], 1):
            print(f"    {i}. {trial.get('nct_id', 'Unknown')} (Score: {trial.get('rank_score', 0)})")
            print(f"       {trial.get('title', 'No title')[:70]}...")
            print(f"       Phase: {trial.get('phase', 'Unknown')}")
    
    # Phase 2.5 Results (RAG Enhancement)
    knowledge_enhancement = results.get('knowledge_enhancement', {})
    enhanced_trials = knowledge_enhancement.get('ranked_trials', [])
    
    print(f"\n🧠 PHASE 2.5 - KNOWLEDGE-ENHANCED RANKING (RAG):")
    print(f"  Knowledge enhancement: {'✓ Applied' if knowledge_enhancement.get('knowledge_enhanced') else '✗ Not applied'}")
    print(f"  Trials enhanced: {knowledge_enhancement.get('enhancement_count', 0)}")
    
    if enhanced_trials:
        print(f"\n  Top 5 Trials (after RAG):")
        for i, trial in enumerate(enhanced_trials[:5], 1):
            orig_score = trial.get('original_score', trial.get('rank_score', 'N/A'))
            new_score = trial.get('score', trial.get('rank_score', 'N/A'))
            guideline_score = trial.get('guideline_score', 'N/A')
            
            score_change = ""
            if orig_score != 'N/A' and new_score != 'N/A' and orig_score != new_score:
                diff = new_score - orig_score
                score_change = f" (Δ{diff:+.0f})"
            
            print(f"    {i}. {trial.get('nct_id', 'Unknown')} (Score: {new_score}{score_change})")
            print(f"       Original: {orig_score} | Guideline: {guideline_score}")
            
            rationale = trial.get('guideline_rationale', '')
            if rationale:
                print(f"       Rationale: {rationale[:100]}...")
    
    # Phase 3 Results
    
    # Phase 3 Results
    eligibility_analysis = results.get('eligibility_analysis', {})
    top_matches = eligibility_analysis.get('top_matches', [])
    summary = eligibility_analysis.get('summary', '')
    
    print(f"\n⚖️ PHASE 3 - ELIGIBILITY ANALYSIS:")
    print(f"  Top recommendations: {len(top_matches)}")
    
    if top_matches:
        print(f"\n  Detailed Recommendations:")
        for i, match in enumerate(top_matches, 1):
            print(f"\n    {'='*70}")
            print(f"    RECOMMENDATION #{i}")
            print(f"    {'='*70}")
            print(f"    Trial: {match.get('nct_id', 'Unknown')}")
            print(f"    Title: {match.get('trial_title', 'Unknown')}")
            print(f"    Match Score: {match.get('match_score', 0)}/100")
            print(f"    Eligibility Status: {match.get('eligibility_status', 'Unknown')}")
            
            strengths = match.get('strengths', [])
            if strengths:
                print(f"\n    ✓ Strengths ({len(strengths)}):")
                for strength in strengths:
                    print(f"      • {strength}")
            
            concerns = match.get('concerns', [])
            if concerns:
                print(f"\n    ⚠️ Concerns ({len(concerns)}):")
                for concern in concerns:
                    print(f"      • {concern}")
            
            required_actions = match.get('required_actions', [])
            if required_actions:
                print(f"\n    📋 Required Actions ({len(required_actions)}):")
                for action in required_actions:
                    print(f"      • {action}")
            
            next_steps = match.get('next_steps', '')
            if next_steps:
                print(f"\n    ➡️ Next Steps:")
                print(f"      {next_steps}")
    
    if summary:
        print(f"\n  💡 Overall Summary:")
        print(f"    {summary}")
    
    # Execution metrics
    execution_time = results.get('execution_time_seconds', 0)
    print(f"\n⏱️ EXECUTION METRICS:")
    print(f"  Total time: {execution_time:.1f} seconds ({execution_time/60:.2f} minutes)")
    print(f"  Timestamp: {results.get('timestamp', 'Unknown')}")
    
    # Success message
    print("\n" + "="*80)
    print("✅ COMPLETE PIPELINE TEST PASSED")
    print("="*80)
    print("\nAll three phases executed successfully:")
    print("  ✓ Phase 1: Patient Profile Extracted")
    print("  ✓ Phase 2: Trials Discovered and Ranked")
    print("  ✓ Phase 3: Eligibility Analyzed and Recommendations Generated")
    print(f"\nResults saved to JSON file in output/ directory")


async def run_quick_test():
    """Quick sanity check - just run Phase 1"""
    print("\n" + "="*80)
    print("QUICK TEST - PHASE 1 ONLY")
    print("="*80)
    
    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)
    pdf_path = "tccr.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"\n❌ ERROR: PDF not found at {pdf_path}")
        return
    
    print("\nRunning Phase 1 only (Patient Profiling)...\n")
    result = await engine.run_patient_profiling(pdf_path)
    
    if result.get("success"):
        print("\n✅ Phase 1 test passed!")
        
        # Handle diagnoses (could be string or dict)
        diagnoses = result.get('diagnoses', '')
        if isinstance(diagnoses, str):
            print(f"   Diagnoses: {diagnoses[:100]}...")  # First 100 chars
        else:
            print(f"   Diagnoses: {diagnoses.get('condition', 'Unknown')}")
        
        # Handle biomarkers (could be string or dict)
        biomarkers = result.get('biomarkers', {})
        if isinstance(biomarkers, str):
            print(f"   Biomarkers: Extracted (text format)")
        else:
            print(f"   Biomarkers: {len(biomarkers)} found")
        
        print(f"   Search terms: {len(result.get('search_terms', []))} generated")
    else:
        print(f"\n❌ Phase 1 test failed: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Clinical Trial Matching Pipeline")
    parser.add_argument('--quick', action='store_true', help='Run quick test (Phase 1 only)')
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(run_quick_test())
    else:
        asyncio.run(run_complete_pipeline())