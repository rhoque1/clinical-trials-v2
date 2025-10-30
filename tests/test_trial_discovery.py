import sys
sys.path.append('..')

from state_machines.trial_discovery import TrialDiscoveryStateMachine
from agents.state_machine_agent import StateMachineAgent
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv('../.env')

def test_trial_discovery():
    """Test the complete Trial Discovery state machine"""
    
    print("=" * 80)
    print("TRIAL DISCOVERY STATE MACHINE TEST")
    print("=" * 80)
    
    # Initialize state machine
    sm = TrialDiscoveryStateMachine()
    
    # Simulate patient profile data from Patient Profiler output
    # Using the real output from your tccr.pdf test
    sm.global_memory = {
        "demographics": {
            "age": 40,
            "sex": "Female"
        },
        "diagnoses": ["Stage IIIB Cervical Squamous Cell Carcinoma"],
        "biomarkers": {
            "PIK3CA": "E545K mutation",
            "TP53": "R273H mutation", 
            "PD-L1": "15%",
            "HPV": "Type 16 positive"
        },
        "search_terms": [
            "cervical squamous cell carcinoma PIK3CA",
            "stage IIIB cervical cancer",
            "HPV-16 positive cervical carcinoma",
            "cervical cancer PD-L1 positive",
            "locally advanced cervical cancer",
            "cervical cancer immunotherapy"
        ]
    }
    
    print("\n📋 Starting with patient profile:")
    print(f"   Diagnosis: {sm.global_memory['diagnoses'][0]}")
    print(f"   Search terms: {len(sm.global_memory['search_terms'])} terms")
    print(f"   Key biomarkers: PIK3CA, PD-L1, HPV-16")
    
    print("\n" + "=" * 80)
    print("EXECUTING STATE MACHINE...")
    print("=" * 80 + "\n")
    
    async def run_state_machine():
        """Execute state machine with async agent"""
        step = 0
        max_steps = 10
        
        while not sm.is_complete() and step < max_steps:
            step += 1
            current_state_name = sm.current_state
            current_state = sm.get_current_state()
            
            print(f"\n{'='*60}")
            print(f"STEP {step}: {current_state_name}")
            print(f"{'='*60}")
            
            # Create agent for this state
            agent = StateMachineAgent(sm)
            
            # Get instruction with context
            instruction = current_state.get_instruction(sm.global_memory)
            print(f"Instruction: {instruction[:150]}...")
            
            # Prepare task input based on state
            if current_state_name == "generate_queries":
                task = f"Generate search queries from these patient search terms: {sm.global_memory.get('search_terms', [])}"
            
            elif current_state_name == "rank_trials":
                # For ranking, we need to provide trial summaries to the LLM
                filtered_trials = sm.global_memory.get("filtered_trials", [])[:20]  # Limit to 20 for token limits
                
                trial_summaries = []
                for trial in filtered_trials:
                    phase = trial.get("phase", ["Unknown"])[0] if isinstance(trial.get("phase"), list) else trial.get("phase", "Unknown")
                    conditions = trial.get("conditions", [])
                    conditions_str = ", ".join(conditions[:3]) if isinstance(conditions, list) else str(conditions)
                    
                    trial_summaries.append(
                        f"NCT: {trial.get('nct_id')}\n"
                        f"Title: {trial.get('title', '')[:100]}\n"
                        f"Conditions: {conditions_str}\n"
                        f"Phase: {phase}\n"
                        f"Status: {trial.get('status')}"
                    )
                
                trials_text = "\n\n---\n\n".join(trial_summaries)
                task = f"Score these clinical trials for relevance to the patient:\n\n{trials_text}"
            
            elif current_state_name == "prepare_summaries":
                # For summaries, provide the top 10 ranked trials
                ranked_trials = sm.global_memory.get("ranked_trials", [])[:10]
                
                trial_data = []
                for trial in ranked_trials:
                    phase = trial.get("phase", ["Unknown"])[0] if isinstance(trial.get("phase"), list) else trial.get("phase", "Unknown")
                    locations = trial.get("locations", {})
                    cities = locations.get("cities", []) if isinstance(locations, dict) else []
                    location_str = cities[0] if cities else "Location not specified"
                    
                    trial_data.append({
                        "nct_id": trial.get("nct_id"),
                        "title": trial.get("title", "")[:100],
                        "phase": phase,
                        "status": trial.get("status"),
                        "location": location_str,
                        "conditions": trial.get("conditions", [])[:3]
                    })
                
                import json
                task = f"Summarize these top 10 trials:\n\n{json.dumps(trial_data, indent=2)}"
            
            else:
                task = "Process the data from previous states in memory"
            
            print(f"Task: {task[:100]}...")
            
            # Execute state with LLM
            result = await agent.execute_state(task)
            
            if result.get('state_result'):
                print(f"✓ State completed")
                print(f"  Memory keys updated: {list(result['state_result'].keys())}")
            else:
                print(f"⚠ State returned no result")
        
        if step >= max_steps:
            print(f"\n⚠ Stopped after {max_steps} steps (safety limit)")
        
        return True
    
    # Run the async function
    asyncio.run(run_state_machine())
    
    # Verify results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    if "search_queries" in sm.global_memory:
        print(f"\n✓ Search Queries Generated: {len(sm.global_memory['search_queries'])}")
        for i, query in enumerate(sm.global_memory['search_queries'], 1):
            print(f"   {i}. {query}")
    
    if "raw_trials" in sm.global_memory:
        print(f"\n✓ Raw Trials Retrieved: {len(sm.global_memory['raw_trials'])}")
    
    if "filtered_trials" in sm.global_memory:
        print(f"✓ Active Trials After Filtering: {len(sm.global_memory['filtered_trials'])}")
    
    if "ranked_trials" in sm.global_memory:
        print(f"✓ Trials Ranked: {len(sm.global_memory['ranked_trials'])}")
        if sm.global_memory['ranked_trials']:
            print(f"\n   Top 3 Trials:")
            for i, trial in enumerate(sm.global_memory['ranked_trials'][:3], 1):
                score = trial.get('relevance_score', 'N/A')
                title = trial.get('title', 'No title')[:70]
                nct = trial.get('nct_id', 'Unknown')
                print(f"   {i}. [{nct}] Score: {score} - {title}")
    
    if "trial_summaries" in sm.global_memory:
        summaries = sm.global_memory['trial_summaries']
        print(f"\n✓ Trial Summaries Prepared: {len(summaries)}")
        if summaries:
            print(f"\n   First Summary:")
            first = summaries[0]
            print(f"   NCT ID: {first.get('nct_id')}")
            print(f"   Title: {first.get('title')}")
            print(f"   Phase: {first.get('phase')}")
            print(f"   Status: {first.get('status')}")
        else:
            print(f"   (No summaries - no trials found)")
    
    # Check completion
    if sm.global_memory.get("trial_discovery_complete"):
        print("\n" + "=" * 80)
        print("✅ TRIAL DISCOVERY COMPLETE - ALL 5 STATES EXECUTED SUCCESSFULLY")
        print("=" * 80)
        return True
    else:
        print("\n❌ Trial discovery did not complete")
        return False

if __name__ == "__main__":
    success = test_trial_discovery()
    sys.exit(0 if success else 1)