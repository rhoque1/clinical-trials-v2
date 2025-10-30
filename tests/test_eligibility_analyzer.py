"""
Test script for Eligibility Analyzer (Phase 3)
Tests the 5-state eligibility assessment pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from state_machines.eligibility_analyzer import EligibilityAnalyzer
from agents.state_machine_agent import StateMachineAgent


async def run_eligibility_analyzer():
    """Execute the complete Eligibility Analyzer state machine"""
    
    print("="*80)
    print("PHASE 3: ELIGIBILITY ANALYZER TEST")
    print("="*80)
    
    # Initialize state machine
    sm = EligibilityAnalyzer()
    
    # Mock patient profile (from Phase 1 - simplified for testing)
    mock_patient_profile = {
        "demographics": {
            "age": 40,
            "sex": "Female"
        },
        "diagnoses": [
            {
                "condition": "Cervical Squamous Cell Carcinoma",
                "stage": "IIIB",
                "histology": "Squamous Cell Carcinoma"
            }
        ],
        "biomarkers": [
            {"name": "PIK3CA", "variant": "E545K", "status": "positive"},
            {"name": "TP53", "variant": "R273H", "status": "positive"},
            {"name": "PD-L1", "value": 15, "unit": "%", "status": "positive"},
            {"name": "HPV", "subtype": "HPV-16", "status": "positive"}
        ],
        "treatment_history": [
            {
                "regimen": "Cisplatin-based chemoradiation",
                "start_date": "2024-03",
                "status": "completed"
            }
        ]
    }
    
    # Mock top 10 trials (from Phase 2 - simplified summaries)
    mock_ranked_trials = [
        {
            "nct_id": "NCT05501171",
            "title": "Pembrolizumab and Chemoradiation for Locally Advanced Cervical Cancer",
            "phase": "Phase 3",
            "status": "Recruiting",
            "rank_score": 85,
            "brief_summary": "Study of pembrolizumab with chemoradiation in stage IB3-IVA cervical cancer",
            "criteria_snippet": "Inclusion: Age >=18, Stage IB3-IVA cervical cancer, ECOG 0-1. Exclusion: Prior immunotherapy, active brain metastases"
        },
        {
            "nct_id": "NCT04230954",
            "title": "Durvalumab With Chemoradiotherapy in Cervical Cancer",
            "phase": "Phase 3",
            "status": "Recruiting",
            "rank_score": 82,
            "brief_summary": "Study of durvalumab with standard chemoradiation in locally advanced cervical cancer",
            "criteria_snippet": "Inclusion: Age >=18, Stage IB2-IVA, ECOG 0-1, adequate organ function. Exclusion: Prior pelvic radiation"
        },
        {
            "nct_id": "NCT03830866",
            "title": "Atezolizumab and Bevacizumab in Recurrent Cervical Cancer",
            "phase": "Phase 2",
            "status": "Recruiting",
            "rank_score": 78,
            "brief_summary": "Combination immunotherapy for recurrent/metastatic cervical cancer",
            "criteria_snippet": "Inclusion: Recurrent/metastatic cervical cancer, prior platinum therapy. Exclusion: Active CNS metastases"
        },
        {
            "nct_id": "NCT04221945",
            "title": "PD-L1 Positive Advanced Cervical Cancer Study",
            "phase": "Phase 2",
            "status": "Recruiting",
            "rank_score": 80,
            "brief_summary": "Study for PD-L1 positive advanced cervical cancer patients",
            "criteria_snippet": "Inclusion: PD-L1 positive (>=1%), Stage IIIB-IVB, squamous histology. Exclusion: Prior checkpoint inhibitor"
        },
        {
            "nct_id": "NCT03556202",
            "title": "HPV-Targeted Immunotherapy in Cervical Cancer",
            "phase": "Phase 1/2",
            "status": "Recruiting",
            "rank_score": 76,
            "brief_summary": "HPV-targeted vaccine combined with pembrolizumab",
            "criteria_snippet": "Inclusion: HPV-16 or HPV-18 positive, any stage. Exclusion: Autoimmune disease"
        },
        {
            "nct_id": "NCT04300647",
            "title": "Carboplatin and Paclitaxel With Immunotherapy",
            "phase": "Phase 3",
            "status": "Recruiting",
            "rank_score": 75,
            "brief_summary": "Standard chemotherapy plus immunotherapy for advanced cervical cancer",
            "criteria_snippet": "Inclusion: Stage IVB or recurrent, measurable disease. Exclusion: >2 prior systemic regimens"
        },
        {
            "nct_id": "NCT03257267",
            "title": "PIK3CA Mutation Targeted Therapy Study",
            "phase": "Phase 2",
            "status": "Recruiting",
            "rank_score": 77,
            "brief_summary": "Targeted therapy for PIK3CA mutant solid tumors including cervical cancer",
            "criteria_snippet": "Inclusion: PIK3CA mutation confirmed, advanced solid tumor. Exclusion: Uncontrolled diabetes"
        },
        {
            "nct_id": "NCT04576156",
            "title": "Radiotherapy Plus Immunotherapy Cervical Cancer",
            "phase": "Phase 2",
            "status": "Recruiting",
            "rank_score": 74,
            "brief_summary": "Combination radiation and immune checkpoint inhibitor",
            "criteria_snippet": "Inclusion: Locally advanced cervical cancer, no prior radiation. Exclusion: Inflammatory bowel disease"
        },
        {
            "nct_id": "NCT03668639",
            "title": "Neoadjuvant Immunotherapy Before Surgery",
            "phase": "Phase 2",
            "status": "Recruiting",
            "rank_score": 72,
            "brief_summary": "Immunotherapy before surgical resection in early-stage cervical cancer",
            "criteria_snippet": "Inclusion: Stage IB2-IIB, surgical candidate. Exclusion: Prior systemic therapy"
        },
        {
            "nct_id": "NCT05123456",
            "title": "TP53 Mutation Basket Trial",
            "phase": "Phase 1",
            "status": "Recruiting",
            "rank_score": 70,
            "brief_summary": "Novel agent targeting TP53 mutations across tumor types",
            "criteria_snippet": "Inclusion: TP53 mutation, any solid tumor, prior standard therapy. Exclusion: Active infection"
        }
    ]
    
    # Store in global memory
    sm.global_memory["patient_profile"] = mock_patient_profile
    sm.global_memory["ranked_trials"] = mock_ranked_trials
    
    print(f"\n✓ Loaded patient profile: {mock_patient_profile['demographics']['age']}F, Stage {mock_patient_profile['diagnoses'][0]['stage']}")
    print(f"✓ Loaded {len(mock_ranked_trials)} ranked trials for eligibility analysis")
    
    # Execute state machine
    # Execute state machine
    state_count = 0
    current_state = sm.get_current_state()
    
    while current_state is not None:
        state_count += 1
        
        print(f"\n{'='*80}")
        print(f"STATE {state_count}: {current_state.name.upper()}")
        print(f"Description: {current_state.description}")
        print(f"{'='*80}")
        
        # Create agent for this state
        agent = StateMachineAgent(sm)
        
        # Get instruction with context
        instruction = current_state.get_instruction(sm.global_memory)
        
        # Build task based on state
        if current_state.name == "extract_criteria":
            # State 1: Pass trial summaries for criteria extraction
            task = f"""Extract structured eligibility criteria from these {len(mock_ranked_trials)} trials:

{chr(10).join([f"{i+1}. {t['nct_id']}: {t['criteria_snippet']}" for i, t in enumerate(mock_ranked_trials)])}

Parse into structured JSON format as specified."""
        
        elif current_state.name == "match_demographics":
            # State 2: Pass patient demographics and structured criteria
            patient_age = mock_patient_profile['demographics']['age']
            patient_sex = mock_patient_profile['demographics']['sex']
            criteria = sm.global_memory.get("structured_criteria", {})
            
            task = f"""Match patient demographics against trial criteria:

PATIENT:
- Age: {patient_age}
- Sex: {patient_sex}

TRIAL CRITERIA:
{chr(10).join([f"{nct}: Age requirement in inclusion criteria" for nct in criteria.keys()])}

Perform deterministic matching and return results in specified JSON format."""
        
        elif current_state.name == "match_clinical_features":
            # State 3: Pass clinical features and criteria
            diagnosis = mock_patient_profile['diagnoses'][0]
            biomarkers = mock_patient_profile['biomarkers']
            
            task = f"""Match patient clinical features against trial requirements:

PATIENT CLINICAL PROFILE:
- Diagnosis: {diagnosis['condition']}
- Stage: {diagnosis['stage']}
- Histology: {diagnosis['histology']}
- Biomarkers:
{chr(10).join([f"  * {b['name']}: {b.get('variant', '')} {b.get('value', '')} {b.get('unit', '')} ({b['status']})" for b in biomarkers])}

Trials that passed demographics: {list(sm.global_memory.get('demographic_matches', {}).keys())}

Perform hybrid exact/fuzzy matching and return results with clinical scores."""
        
        elif current_state.name == "assess_eligibility":
            # State 4: Pass high-scoring trials for complex assessment
            clinical_matches = sm.global_memory.get("clinical_matches", {})
            high_scoring = {nct: data for nct, data in clinical_matches.items() 
                          if data.get("clinical_score", 0) >= 0.7}
            
            task = f"""Assess complex eligibility criteria for {len(high_scoring)} high-scoring trials:

PATIENT CONTEXT:
- Recent treatment: {mock_patient_profile['treatment_history'][0]['regimen']} (completed {mock_patient_profile['treatment_history'][0]['start_date']})
- Available data: Demographics, stage, biomarkers, treatment history
- Missing data: Recent labs, ECOG status, imaging reports

HIGH-SCORING TRIALS: {list(high_scoring.keys())}

Use chain-of-thought reasoning to assess complex criteria like:
- Adequate organ function
- Prior treatment requirements
- Washout periods
- Performance status

Return detailed assessments with confidence scores."""
        
        elif current_state.name == "generate_recommendations":
            # State 5: Synthesize all previous assessments
            task = f"""Generate final eligibility report synthesizing all assessments:

AVAILABLE DATA:
- Structured criteria: {len(sm.global_memory.get('structured_criteria', {}))} trials
- Demographic matches: {sm.global_memory.get('demographic_matches', {})}
- Clinical matches: {sm.global_memory.get('clinical_matches', {})}
- Eligibility assessments: {sm.global_memory.get('eligibility_assessments', {})}

Create actionable recommendations for top 3-5 trials with:
- Match scores
- Strengths and concerns
- Required actions
- Next steps

Return comprehensive report in specified JSON format."""
        
        else:
            task = "Process this state according to the instruction."
        
        # Execute state
        # Execute state
        # Execute state (agent handles LLM call, process_input, and transition internally)
        print(f"\n→ Executing LLM agent...")
        agent_result = await agent.execute_state(task)
        
        # Extract the processed result
        state_result = agent_result.get('state_result', {})
        llm_response = agent_result.get('llm_response', '')
        
        # Print result summary
        print(f"\n✓ State completed:")
        print(f"  Status: {state_result.get('status', 'unknown')}")
        
        if current_state.name == "extract_criteria":
            print(f"  Trials processed: {state_result.get('trials_processed', 0)}")
        elif current_state.name == "match_demographics":
            print(f"  Passing trials: {state_result.get('passing_trials', 0)}")
        elif current_state.name == "match_clinical_features":
            print(f"  High-scoring trials (>=0.7): {state_result.get('high_scoring_trials', 0)}")
        elif current_state.name == "assess_eligibility":
            print(f"  Highly likely matches: {state_result.get('highly_likely_matches', 0)}")
        elif current_state.name == "generate_recommendations":
            print(f"  Top matches: {state_result.get('top_matches_count', 0)}")
        
        # Check if state was successful
        if state_result.get('status') != 'success':
            print(f"\n⚠️ Warning: State returned status '{state_result.get('status')}'")
            if 'error' in state_result:
                print(f"   Error: {state_result['error']}")
            # Continue anyway for debugging
        
        # Note: agent.execute_state() already transitioned to next state
        # Just update our reference
        current_state = sm.get_current_state()
    
    print(f"\n{'='*80}")
    print("ELIGIBILITY ANALYZER COMPLETE")
    print(f"{'='*80}")
    
    # Print final summary
    final_recs = sm.global_memory.get("final_recommendations", {})
    if final_recs:
        print(f"\n📊 FINAL RESULTS:")
        print(f"\nTop Matches: {len(final_recs.get('top_matches', []))}")
        for match in final_recs.get('top_matches', [])[:3]:
            print(f"\n  {match.get('rank')}. {match.get('nct_id')} (Score: {match.get('match_score')})")
            print(f"     Status: {match.get('eligibility_status')}")
            print(f"     Strengths: {len(match.get('strengths', []))} identified")
            print(f"     Required actions: {len(match.get('required_actions', []))}")
        
        print(f"\n💡 Summary: {final_recs.get('summary', 'N/A')}")
    
    return sm


if __name__ == "__main__":
    asyncio.run(run_eligibility_analyzer())