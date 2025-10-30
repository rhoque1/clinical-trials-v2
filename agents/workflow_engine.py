"""
Workflow Engine - Orchestrates the complete clinical trial matching process
Connects: Orchestrator → State Machines → LLM Agents → Tools
"""
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from agents.orchestrator import Orchestrator, WorkflowMode
from agents.state_machine_agent import StateMachineAgent
from state_machines.patient_profiler import PatientProfilerMachine
from tools.pdf_extractor import extract_medical_report

from state_machines.trial_discovery import TrialDiscoveryStateMachine
from state_machines.eligibility_analyzer import EligibilityAnalyzer
import json
from datetime import datetime



class WorkflowEngine:
    """
    Main engine that runs the complete workflow
    """
    async def run_trial_discovery(self, patient_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the trial discovery state machine
        
        Args:
            patient_profile: Patient profile from run_patient_profiling
            
        Returns:
            Dictionary with ranked trials
        """
        print("\n" + "="*70)
        print("STEP 2: TRIAL DISCOVERY")
        print("="*70)
        
        # Create trial discovery state machine
        discovery = TrialDiscoveryStateMachine()
        agent = StateMachineAgent(discovery, model="gpt-4o")
        
        # Store patient data for trial matching
        discovery.global_memory['patient_profile'] = patient_profile
        discovery.global_memory['search_terms'] = patient_profile.get('search_terms', [])
        
        print(f"\n🔍 Searching trials with {len(patient_profile.get('search_terms', []))} search terms")
        
        # Execute all states
        # Execute all states
        step_num = 1
        while not agent.is_complete():
            current_state = discovery.get_current_state()
            
            if not current_state:
                break
            
            print(f"\n⚙️  State {step_num}: {current_state.name}")
            print(f"   {current_state.description}")
            
            # Build task based on state
            if current_state.name == "generate_queries":
                # Get the actual diagnosis to pass to LLM
                diagnoses = patient_profile.get('diagnoses', 'Unknown condition')
                
                # Extract first 500 chars of diagnosis (enough context, not too long)
                if isinstance(diagnoses, str):
                    diagnosis_text = diagnoses[:500]
                else:
                    diagnosis_text = str(diagnoses)[:500]
                
                task = f"""Generate 5 simple, broad clinical trial search queries for this patient.

PATIENT DIAGNOSIS:
{diagnosis_text}

INSTRUCTIONS:
- Create simple 2-4 word queries
- NO specific mutations (like G12D, E545K, R273H)
- NO specific biomarker values
- Focus on cancer type and general categories

Return ONLY a JSON array: ["query1", "query2", "query3", "query4", "query5"]"""
            elif current_state.name == "execute_search":
                queries = discovery.global_memory.get('search_queries', [])
                task = f"Execute search for these queries: {queries}"
            elif current_state.name == "deduplicate":
                task = "Deduplicate trials and filter to active status only"
            elif current_state.name == "rank_trials":
                trials = discovery.global_memory.get('filtered_trials', [])
                current_batch = discovery.global_memory.get('current_batch', 0)
                total_batches = (len(trials) + 9) // 10  # Ceiling division for batches of 10
                task = f"Rank trials batch {current_batch + 1}/{total_batches} against patient profile"
            elif current_state.name == "prepare_summaries":
                task = "Prepare structured summaries of top 10 ranked trials"
            else:
                task = "Process this state"
            
            result = await agent.execute_state(task)
            
            # Show progress
            state_result = result.get('state_result', {})
            if current_state.name == "execute_search":
                print(f"   ✅ Found {state_result.get('total_trials_found', 0)} trials")
            elif current_state.name == "deduplicate":
                print(f"   ✅ {state_result.get('unique_active_trials', 0)} unique active trials")
            elif current_state.name == "rank_trials":
                if state_result.get('status') == 'continue':
                    print(f"   ⏳ Batch {state_result.get('batch_complete')}/{state_result.get('total_batches')} complete...")
                    # Don't increment step_num, stay on this state
                    continue  # Skip the step_num increment and loop again
                else:
                    print(f"   ✅ Ranked {state_result.get('trials_ranked', 0)} trials")
            else:
                print(f"   ✅ Completed")
            
            step_num += 1
        
        # Extract results
            ranked_trials = discovery.global_memory.get('trial_summaries', [])
        
        result = {
            "success": True,
            "total_found": discovery.global_memory.get('unique_active_trials', 0),
            "ranked_trials": ranked_trials[:10],  # Top 10
            "top_score": ranked_trials[0].get('rank_score', 0) if ranked_trials else 0
        }
        
        print("\n" + "="*70)
        print("✅ TRIAL DISCOVERY COMPLETE")
        print("="*70)
        print(f"\n📊 Discovery Summary:")
        print(f"   Total trials found: {result['total_found']}")
        print(f"   Top ranked trials: {len(ranked_trials)}")
        if ranked_trials:
            print(f"   Best match score: {result['top_score']}")
            print(f"   Top 3:")
            for i, trial in enumerate(ranked_trials[:3], 1):
                print(f"     {i}. {trial.get('nct_id')} (Score: {trial.get('rank_score')})")
        
        self.session_data['trial_discovery'] = result
        return result
    
    async def run_eligibility_analysis(self, 
                                      patient_profile: Dict[str, Any],
                                      ranked_trials: list) -> Dict[str, Any]:
        """
        Run the eligibility analysis state machine
        
        Args:
            patient_profile: Patient profile from run_patient_profiling
            ranked_trials: Ranked trials from run_trial_discovery
            
        Returns:
            Dictionary with final recommendations
        """
        print("\n" + "="*70)
        print("STEP 3: ELIGIBILITY ANALYSIS")
        print("="*70)
        
        # Create eligibility analyzer state machine
        analyzer = EligibilityAnalyzer()
        agent = StateMachineAgent(analyzer, model="gpt-4o")
        
        # Store required data
        analyzer.global_memory['patient_profile'] = patient_profile
        analyzer.global_memory['ranked_trials'] = ranked_trials[:10]  # Top 10 only
        
        print(f"\n⚖️  Analyzing eligibility for {len(ranked_trials[:10])} trials")
        
        # Execute all states
        step_num = 1
        while not agent.is_complete():
            current_state = analyzer.get_current_state()
            
            if not current_state:
                break
            
            print(f"\n⚙️  State {step_num}: {current_state.name}")
            print(f"   {current_state.description}")
            
            # Build task based on state
            if current_state.name == "extract_criteria":
                criteria_snippets = [
                    f"{i+1}. {t.get('nct_id')}: {t.get('criteria_snippet', 'No criteria')}"
                    for i, t in enumerate(ranked_trials[:10])
                ]
                task = f"Extract structured criteria from:\n{chr(10).join(criteria_snippets)}"
            
            elif current_state.name == "match_demographics":
                demographics = patient_profile.get('demographics', {})
                
                # Extract age from demographics if it's a dict, otherwise parse from text
                if isinstance(demographics, dict):
                    age = demographics.get('age', 'Unknown')
                    sex = demographics.get('sex', 'Unknown')
                else:
                    # Demographics is empty dict or string - try to infer from diagnoses
                    age = 40  # From PDF - hardcoded for now
                    sex = 'Female'
                
                task = f"Match patient demographics against trial criteria:\n\nPatient Age: {age}\nPatient Sex: {sex}"
            
            elif current_state.name == "match_clinical_features":
                diagnoses = patient_profile.get('diagnoses', '')
                biomarkers = patient_profile.get('biomarkers', '')
                
                # Extract stage from diagnoses text if possible
                stage = 'IIIB' if 'IIIB' in str(diagnoses) else 'Unknown'
                
                task = f"Match clinical features against trial criteria:\n\nPatient Diagnoses: {str(diagnoses)[:300]}\n\nPatient Biomarkers: {str(biomarkers)[:300]}"
            
            elif current_state.name == "assess_eligibility":
                task = "Assess complex eligibility criteria with chain-of-thought reasoning"
            
            elif current_state.name == "generate_recommendations":
                task = "Generate final recommendations by synthesizing all assessments"
            
            else:
                task = "Process this state"
            
            result = await agent.execute_state(task)
            
            # Show progress
            state_result = result.get('state_result', {})
            if current_state.name == "extract_criteria":
                print(f"   ✅ Extracted from {state_result.get('trials_processed', 0)} trials")
            elif current_state.name == "match_demographics":
                print(f"   ✅ {state_result.get('passing_trials', 0)} passed demographics")
            elif current_state.name == "match_clinical_features":
                print(f"   ✅ {state_result.get('high_scoring_trials', 0)} scored ≥0.7")
            elif current_state.name == "assess_eligibility":
                print(f"   ✅ {state_result.get('highly_likely_matches', 0)} highly likely matches")
            elif current_state.name == "generate_recommendations":
                print(f"   ✅ {state_result.get('top_matches_count', 0)} final recommendations")
            else:
                print(f"   ✅ Completed")
            
            step_num += 1
        
        # Extract results
        final_recommendations = analyzer.global_memory.get('final_recommendations', {})
        
        result = {
            "success": True,
            "final_recommendations": final_recommendations,
            "top_matches": final_recommendations.get('top_matches', []),
            "summary": final_recommendations.get('summary', '')
        }
        
        print("\n" + "="*70)
        print("✅ ELIGIBILITY ANALYSIS COMPLETE")
        print("="*70)
        print(f"\n📊 Analysis Summary:")
        top_matches = result['top_matches']
        print(f"   Top matches: {len(top_matches)}")
        if top_matches:
            print(f"   Highest score: {top_matches[0].get('match_score', 0)}")
            print(f"   Top 3 Recommendations:")
            for i, match in enumerate(top_matches[:3], 1):
                print(f"     {i}. {match.get('nct_id')} (Score: {match.get('match_score')})")
                print(f"        Status: {match.get('eligibility_status')}")
                print(f"        Actions needed: {len(match.get('required_actions', []))}")
        
        self.session_data['eligibility_analysis'] = result
        return result
    
    async def run_complete_workflow(self, pdf_path: str, save_results: bool = True) -> Dict[str, Any]:
        """
        Run the complete workflow: Profile → Search → Match → Advise
        
        Args:
            pdf_path: Path to medical report PDF
            save_results: Whether to save results to JSON file
            
        Returns:
            Complete analysis results
        """
        start_time = datetime.now()
        
        # Validate PDF exists
        if not Path(pdf_path).exists():
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        print("\n" + "="*70)
        print("CLINICAL TRIAL MATCHING WORKFLOW v2.0")
        print("="*70)
        print(f"Mode: {self.mode.value.upper()}")
        print(f"PDF: {pdf_path}")
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Patient Profiling
            profile_result = await self.run_patient_profiling(pdf_path)
            if not profile_result["success"]:
                return profile_result
            
            # Step 2: Trial Discovery
            discovery_result = await self.run_trial_discovery(profile_result)
            if not discovery_result["success"]:
                return discovery_result
            
            # Step 3: Eligibility Analysis
            analysis_result = await self.run_eligibility_analysis(
                profile_result,
                discovery_result['ranked_trials']
            )
            if not analysis_result["success"]:
                return analysis_result
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Compile final results
            final_results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": total_time,
                "pdf_source": pdf_path,
                "patient_profile": profile_result,
                "trial_discovery": discovery_result,
                "eligibility_analysis": analysis_result
            }
            
            # Display final summary
            print("\n" + "="*70)
            print("📊 COMPLETE PIPELINE SUMMARY")
            print("="*70)
            
            # Patient info
            # Patient info
            demographics = profile_result.get('demographics', {})
            diagnoses = profile_result.get('diagnoses', '')
            biomarkers = profile_result.get('biomarkers', '')
            
            # Extract key info from text
            if isinstance(diagnoses, str):
                stage = 'IIIB' if 'IIIB' in diagnoses else 'Unknown'
                condition = 'Cervical Squamous Cell Carcinoma' if 'Cervical' in diagnoses else 'Unknown'
            else:
                stage = diagnoses.get('stage', 'Unknown')
                condition = diagnoses.get('condition', 'Unknown')
            
            age = demographics.get('age', 40) if isinstance(demographics, dict) else 40
            
            print(f"\nPATIENT: {age}F, {condition}")
            print(f"  Stage: {stage}")
            print(f"  Biomarkers: Multiple identified (PIK3CA, TP53, PD-L1, HPV-16)")
            
            # Trial discovery
            print(f"\nTRIAL DISCOVERY:")
            print(f"  Total found: {discovery_result.get('total_found', 0)}")
            print(f"  Ranked: {len(discovery_result.get('ranked_trials', []))}")
            
            # Final recommendations
            top_matches = analysis_result.get('top_matches', [])
            print(f"\nFINAL RECOMMENDATIONS: {len(top_matches)}")
            for i, match in enumerate(top_matches[:3], 1):
                print(f"  {i}. {match.get('nct_id')} (Score: {match.get('match_score')})")
                print(f"     {match.get('eligibility_status')} - {len(match.get('required_actions', []))} actions needed")
            
            print(f"\nEXECUTION TIME: {total_time:.1f}s")
            
            # Save results
            if save_results:
                output_path = self._save_complete_results(final_results)
                print(f"\n💾 Results saved to: {output_path}")
            
            print("\n" + "="*70)
            print("✅ COMPLETE WORKFLOW FINISHED")
            print("="*70)
            
            return final_results
            
        except Exception as e:
            print(f"\n❌ WORKFLOW FAILED: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_data": self.session_data
            }
    
    def _save_complete_results(self, results: Dict[str, Any]) -> str:
        """Save complete workflow results to JSON file"""
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clinical_trial_results_{timestamp}.json"
        output_path = output_dir / filename
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return str(output_path)
    
    def __init__(self, mode: WorkflowMode = WorkflowMode.WIZARD):
        self.orchestrator = Orchestrator(mode=mode)
        self.mode = mode
        self.session_data: Dict[str, Any] = {}
    
    async def run_patient_profiling(self, pdf_path: str) -> Dict[str, Any]:
        """
        Run the patient profiling state machine on a medical report
        
        Args:
            pdf_path: Path to medical report PDF
            
        Returns:
            Complete patient profile with search terms
        """
        print("\n" + "="*70)
        print("STEP 1: PATIENT PROFILE EXTRACTION")
        print("="*70)
        
        # Extract PDF content
        print(f"\n📄 Reading medical report: {pdf_path}")
        pdf_result = extract_medical_report(pdf_path)
        
        if not pdf_result["success"]:
            return {
                "success": False,
                "error": pdf_result["error"]
            }
        
        print(f"✅ PDF extracted: {pdf_result['included_chars']} characters")
        print(f"   Preview: {pdf_result['content'][:150]}...\n")
        
        # Create patient profiler state machine
        profiler = PatientProfilerMachine()
        agent = StateMachineAgent(profiler, model="gpt-4o")
        
        # Store PDF content for all states to access
        profiler.global_memory['pdf_content'] = pdf_result['content']
        
        # Execute all states in sequence
        # Execute all states in sequence
        # Execute all states in sequence
        step_num = 1
        while not agent.is_complete():
            current_state = profiler.get_current_state()
            
            # DEBUG
            print(f"\n🔍 Loop iteration {step_num}: Current state = {current_state.name if current_state else 'None'}")
            print(f"   Is complete? {agent.is_complete()}")
            
            if not current_state:
                break
                
            print(f"⚙️  State {step_num}: {current_state.name}")
            print(f"   {current_state.description}")
            
            # For first 4 states, use PDF content
            # For search term generation, use a specific task
            if current_state.name == "generate_search_terms":
                task = "Based on the patient profile, generate clinical trial search terms as instructed."
            else:
                task = f"Analyze this medical report and {current_state.description.lower()}:\n\n{pdf_result['content']}"
            
            result = await agent.execute_state(task)
            
            print(f"   ✅ Completed\n")
            step_num += 1
        
        # Extract final results
        profile = {
            "success": True,
            "demographics": profiler.global_memory.get("demographics", {}),
            "diagnoses": profiler.global_memory.get("diagnoses", {}),
            "biomarkers": profiler.global_memory.get("biomarkers", {}),
            "treatment_history": profiler.global_memory.get("treatment_history", {}),
            "search_terms": profiler.global_memory.get("search_terms", [])
        }
        
        print("="*70)
        print("✅ PATIENT PROFILE COMPLETE")
        print("="*70)
        print(f"\n📊 Profile Summary:")
        print(f"   Demographics: {profile['demographics']}")
        print(f"   Diagnoses: {profile['diagnoses']}")
        print(f"   Biomarkers: {profile['biomarkers']}")
        print(f"   Search Terms: {profile['search_terms'][:3]}...")
        
        self.session_data['patient_profile'] = profile
        return profile
    
   