"""
Inspect detailed results from eligibility analyzer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from tests.test_eligibility_analyzer import run_eligibility_analyzer


async def inspect_results():
    """Run the analyzer and inspect detailed results"""
    
    sm = await run_eligibility_analyzer()
    
    print("\n" + "="*80)
    print("DETAILED RESULTS INSPECTION")
    print("="*80)
    
    # Inspect State 1 output: Structured criteria
    print("\n📋 STATE 1 - STRUCTURED CRITERIA (Sample):")
    structured_criteria = sm.global_memory.get("structured_criteria", {})
    sample_trial = list(structured_criteria.keys())[0] if structured_criteria else None
    if sample_trial:
        print(f"\n{sample_trial}:")
        print(json.dumps(structured_criteria[sample_trial], indent=2))
    
    # Inspect State 2 output: Demographic matches
    print("\n👤 STATE 2 - DEMOGRAPHIC MATCHES (Sample):")
    demo_matches = sm.global_memory.get("demographic_matches", {})
    if demo_matches:
        sample = list(demo_matches.items())[0]
        print(f"\n{sample[0]}:")
        print(json.dumps(sample[1], indent=2))
    
    # Inspect State 3 output: Clinical matches
    print("\n🔬 STATE 3 - CLINICAL MATCHES (Top scorer):")
    clinical_matches = sm.global_memory.get("clinical_matches", {})
    if clinical_matches:
        top_scorer = max(clinical_matches.items(), key=lambda x: x[1].get('clinical_score', 0))
        print(f"\n{top_scorer[0]} (Score: {top_scorer[1].get('clinical_score')}):")
        print(json.dumps(top_scorer[1], indent=2))
    
    # Inspect State 4 output: Eligibility assessments
    print("\n⚖️ STATE 4 - ELIGIBILITY ASSESSMENT (Top match):")
    eligibility = sm.global_memory.get("eligibility_assessments", {})
    if eligibility:
        top_match = list(eligibility.items())[0]
        print(f"\n{top_match[0]}:")
        print(json.dumps(top_match[1], indent=2))
    
    # Inspect State 5 output: Already shown in main test
    print("\n💡 STATE 5 - FINAL RECOMMENDATIONS:")
    print("(See main test output above)")
    
    print("\n" + "="*80)
    print("Inspection complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(inspect_results())