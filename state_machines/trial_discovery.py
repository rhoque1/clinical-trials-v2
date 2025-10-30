from state_machines.base_state_machine import State, StateMachine
from typing import Dict, Any, List, Optional
import json

class GenerateSearchQueriesState(State):
    """State 1: Expand search terms into multiple query strategies"""
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        # NOTE: Context may not be reliably passed, so we'll construct the instruction
        # to work with the task string that will include patient info
        
        return """You are a clinical trial search query optimizer for ClinicalTrials.gov.

You will receive patient diagnosis information in the task.

YOUR TASK: Generate EXACTLY 5 simple, broad search queries.

MANDATORY RULES - NO EXCEPTIONS:
1. Use ONLY 2-4 words per query
2. NO specific biomarkers (PIK3CA, TP53, KRAS mutation variants like G12D, etc.)
3. NO specific mutations or molecular details
4. NO virus subtypes (HPV-16, HPV-18) - use "HPV positive" if needed
5. NO stage details (IIIB, IVA) - use "advanced" or "locally advanced"
6. ALWAYS include the primary cancer type

QUERY STRUCTURE:
Query 1: "[main cancer type]" (e.g., "cervical cancer", "appendiceal cancer")
Query 2: "[broader related cancer]" (e.g., "peritoneal cancer", "colorectal cancer")
Query 3: "[cancer type] treatment" (e.g., "cervical cancer treatment")
Query 4: "[cancer type] [general category]" (e.g., "cervical cancer HPV", "colorectal cancer")
Query 5: "[alternative term]" (e.g., "cervical carcinoma", "gastrointestinal cancer")

EXAMPLES:

For Cervical Cancer:
["cervical cancer", "gynecologic cancer", "cervical cancer treatment", "cervical cancer HPV", "cervical carcinoma"]

For Appendiceal Cancer / Pseudomyxoma Peritonei:
["appendiceal cancer", "peritoneal cancer", "appendiceal adenocarcinoma", "colorectal cancer", "gastrointestinal cancer"]

For Breast Cancer:
["breast cancer", "metastatic breast cancer", "breast cancer treatment", "breast carcinoma", "invasive breast cancer"]

For Lung Cancer:
["lung cancer", "advanced lung cancer", "lung cancer treatment", "non-small cell lung cancer", "lung carcinoma"]

Return ONLY a JSON array of exactly 5 strings.
Format: ["query1", "query2", "query3", "query4", "query5"]

NO explanations, NO markdown, JUST the JSON array."""

    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into query list"""
        
        # === DEBUG ===
        print("\n" + "="*60)
        print("DEBUG: GenerateSearchQueriesState.process_input()")
        print("="*60)
        print(f"LLM Response (first 300 chars):\n{llm_response[:300]}")
        print("="*60 + "\n")
        # === END DEBUG ===
        
        try:
            # Extract JSON from response
            llm_response = llm_response.strip()
            
            # Try to find JSON array in the response
            import re
            
            # Method 1: Look for JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', llm_response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group(1))
            else:
                # Method 2: Look for a JSON array anywhere in the response
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    queries = json.loads(json_match.group(0))
                else:
                    # Method 3: Try parsing the whole response
                    queries = json.loads(llm_response)
            
            if not isinstance(queries, list):
                raise ValueError("Response is not a list")
            
            # Validate we have queries
            if len(queries) == 0:
                raise ValueError("Empty query list")
            
            # Clean queries: remove extra whitespace, ensure they're strings
            cleaned_queries = []
            for q in queries[:5]:  # Limit to 5
                if isinstance(q, str):
                    cleaned = q.strip()
                    if cleaned:
                        cleaned_queries.append(cleaned)
            
            if len(cleaned_queries) < 3:
                raise ValueError(f"Only {len(cleaned_queries)} valid queries found, need at least 3")
            
            print(f"✓ Generated {len(cleaned_queries)} search queries:")
            for i, q in enumerate(cleaned_queries, 1):
                print(f"  {i}. '{q}'")
            
            return {"search_queries": cleaned_queries}
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            # Fallback: use search terms but SIMPLIFY them
            print(f"⚠ Query generation failed ({str(e)}), creating simple fallback queries")
            
            # Get diagnosis to create simple queries
            patient_profile = global_memory.get("patient_profile", {})
            diagnoses = patient_profile.get("diagnoses", "")
            
            # Create simple fallback queries based on cancer type
            fallback_queries = []
            
            if "cervical" in diagnoses.lower():
                fallback_queries = [
                    "cervical cancer",
                    "advanced cervical cancer",
                    "cervical cancer treatment",
                    "cervical cancer HPV",
                    "cervical carcinoma"
                ]
            elif "breast" in diagnoses.lower():
                fallback_queries = [
                    "breast cancer",
                    "metastatic breast cancer",
                    "breast cancer treatment",
                    "breast carcinoma",
                    "invasive breast cancer"
                ]
            elif "lung" in diagnoses.lower():
                fallback_queries = [
                    "lung cancer",
                    "advanced lung cancer",
                    "non-small cell lung cancer",
                    "NSCLC",
                    "lung carcinoma"
                ]
            else:
                # Generic fallback
                search_terms = global_memory.get("search_terms", [])
                fallback_queries = search_terms[:5] if search_terms else ["cancer"]
            
            print(f"  Using {len(fallback_queries)} fallback queries:")
            for i, q in enumerate(fallback_queries, 1):
                print(f"  {i}. '{q}'")
            
            return {"search_queries": fallback_queries}
    
    def get_next_state(self) -> Optional[str]:
        return "execute_search"


class ExecuteTrialSearchState(State):
    """State 2: Execute API calls to ClinicalTrials.gov"""
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are a clinical trial API executor.

You will receive search queries. Your task is to:
1. Acknowledge the queries received
2. State that you will execute the searches via the API tool

This is a pass-through state. Just confirm you understand the queries.
Keep your response brief (1-2 sentences)."""

    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actual API calls"""
        from tools.clinical_trials_api import search_clinical_trials_targeted
        
        queries = global_memory.get("search_queries", [])
        all_trials = []
        
        print(f"🔍 Executing {len(queries)} API searches...")
        
        for idx, query in enumerate(queries, 1):
            print(f"  Query {idx}/{len(queries)}: '{query}'")
            result = search_clinical_trials_targeted([query], max_studies=20)
            
            # FIXED: API returns {"status": "success", "data": [...]}
            if result.get("status") == "success":
                trials = result.get("data", [])  # Changed from "trials" to "data"
                all_trials.extend(trials)
                print(f"    → Found {len(trials)} trials")
            else:
                error_msg = result.get("detail", result.get("message", "Unknown error"))
                print(f"    → Error: {error_msg}")
        
        print(f"✓ Total trials retrieved: {len(all_trials)}")
        return {"raw_trials": all_trials, "total_trials_found": len(all_trials)}
    
    def get_next_state(self) -> Optional[str]:
        return "deduplicate"


class DeduplicateAndFilterState(State):
    """State 3: Remove duplicates and filter out inactive trials"""
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are a clinical trial data processor.

You will receive raw trial data. Your task is to:
1. Acknowledge the number of trials received
2. State that you will deduplicate and filter the results

This is a pass-through state. Keep your response brief (1-2 sentences)."""

    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Deduplicate by NCT ID and filter"""
        raw_trials = global_memory.get("raw_trials", [])
        
        # Deduplicate by NCT ID
        seen_nct_ids = set()
        unique_trials = []
        
        for trial in raw_trials:
            nct_id = trial.get("nct_id", "")
            if nct_id and nct_id not in seen_nct_ids:
                seen_nct_ids.add(nct_id)
                unique_trials.append(trial)
        
        # Filter for active trials (recruiting, not yet recruiting, enrolling by invitation)
        active_statuses = ["RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING"]
        filtered_trials = []
        
        for trial in unique_trials:
            status = trial.get("status", "").upper()
            if any(active_status in status for active_status in active_statuses):
                filtered_trials.append(trial)
        
        print(f"📊 Deduplication: {len(raw_trials)} → {len(unique_trials)} unique trials")
        print(f"📊 Filtering: {len(unique_trials)} → {len(filtered_trials)} active trials")
        
        return {
            "filtered_trials": filtered_trials,
            "unique_active_trials": len(filtered_trials)
        }
    
    def get_next_state(self) -> Optional[str]:
        return "rank_trials"


class RankTrialsState(State):
    """State 4: Score and rank trials by relevance"""
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        patient_profile = context.get("patient_profile", {})
        trials = context.get("filtered_trials", [])
        
        # Get first batch of trials (max 10)
        batch_size = 10
        current_batch = context.get("current_batch", 0)
        start_idx = current_batch * batch_size
        end_idx = min(start_idx + batch_size, len(trials))
        batch_trials = trials[start_idx:end_idx]
        
        # Format trial information concisely
        trial_info = []
        for i, trial in enumerate(batch_trials, start=start_idx + 1):
            info = f"""
Trial {i}:
- NCT ID: {trial.get('nct_id', 'Unknown')}
- Title: {trial.get('title', 'Unknown')[:100]}
- Phase: {trial.get('phase', 'Unknown')}
- Conditions: {', '.join(trial.get('conditions', [])[:3])}
- Brief: {trial.get('brief_summary', '')[:200]}
"""
            trial_info.append(info)
        
        diagnoses = str(patient_profile.get('diagnoses', ''))[:500]
        biomarkers = str(patient_profile.get('biomarkers', ''))[:300]
        
        return f"""
Score these {len(batch_trials)} clinical trials for relevance to the patient profile.

PATIENT PROFILE:
Diagnoses: {diagnoses}
Biomarkers: {biomarkers}

TRIALS TO SCORE:
{''.join(trial_info)}

SCORING CRITERIA:
- Condition match (0-40 points): How well does trial target patient's condition?
- Biomarker relevance (0-30 points): Does trial require/target patient's biomarkers?
- Treatment approach (0-20 points): Is treatment mechanism appropriate?
- Trial phase (0-10 points): Higher phases = more established

OUTPUT FORMAT (CRITICAL - Must be valid JSON):
{{
  "scores": [
    {{"trial_index": 1, "score": 85, "reasoning": "Perfect match for condition and biomarkers"}},
    {{"trial_index": 2, "score": 72, "reasoning": "Good condition match, phase unclear"}},
    ...
  ]
}}

Return ONLY the JSON object, nothing else.
"""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Parse scores and rank trials"""
        filtered_trials = global_memory.get("filtered_trials", [])
        batch_size = 10
        current_batch = global_memory.get("current_batch", 0)
        all_scores = global_memory.get("all_trial_scores", [])
        
        try:
            # === DEBUG LOGGING ===
            print("\n" + "="*60)
            print(f"DEBUG: RankTrialsState.process_input() - Batch {current_batch + 1}")
            print("="*60)
            print(f"Total trials: {len(filtered_trials)}")
            print(f"Current batch: {current_batch + 1} of {(len(filtered_trials) + batch_size - 1) // batch_size}")
            print(f"LLM Response (first 500 chars):\n{llm_response[:500]}")
            print("="*60 + "\n")
            # === END DEBUG ===
            
            # Extract JSON from response
            llm_response = llm_response.strip()
            
            # Remove markdown code blocks if present
            if llm_response.startswith('```'):
                lines = llm_response.split('\n')
                llm_response = '\n'.join(lines[1:-1])
            
            # Parse JSON
            import json
            data = json.loads(llm_response)
            scores_list = data.get('scores', [])
            
            # Add scores to this batch of trials
            start_idx = current_batch * batch_size
            for score_obj in scores_list:
                # LLM returns trial_index starting at 1 for each batch
                # We need to map it to the actual position in filtered_trials
                batch_trial_idx = score_obj.get('trial_index', 0) - 1  # 0-indexed within batch
                actual_idx = start_idx + batch_trial_idx  # Actual index in full trial list
                
                if 0 <= actual_idx < len(filtered_trials):
                    filtered_trials[actual_idx]['rank_score'] = score_obj.get('score', 50)
                    filtered_trials[actual_idx]['rank_reasoning'] = score_obj.get('reasoning', '')
                    all_scores.append({
                        'index': actual_idx,
                        'score': score_obj.get('score', 50)
                    })
            
            # Check if we have more batches to process
            next_batch = current_batch + 1
            total_batches = (len(filtered_trials) + batch_size - 1) // batch_size
            
            if next_batch < total_batches:
                # More batches to process
                global_memory['current_batch'] = next_batch
                global_memory['all_trial_scores'] = all_scores
                print(f"✓ Batch {current_batch + 1}/{total_batches} scored, continuing...")
                return {
                    "status": "continue",
                    "batch_complete": current_batch + 1,
                    "total_batches": total_batches
                }
            else:
                # All batches done - finalize ranking
                print(f"✓ All {total_batches} batches scored!")
                
                # Assign default scores to any trials that didn't get scored
                for i, trial in enumerate(filtered_trials):
                    if 'rank_score' not in trial or trial['rank_score'] is None:
                        trial['rank_score'] = 50
                
                # Sort by score descending
                filtered_trials.sort(key=lambda x: x.get('rank_score', 0), reverse=True)
                
                # Store results
                global_memory['ranked_trials'] = filtered_trials
                global_memory['trials_ranked'] = len(filtered_trials)
                
                # Clean up batch tracking
                if 'current_batch' in global_memory:
                    del global_memory['current_batch']
                if 'all_trial_scores' in global_memory:
                    del global_memory['all_trial_scores']
                
                return {
                    "status": "success",
                    "trials_ranked": len(filtered_trials),
                    "top_score": filtered_trials[0].get('rank_score', 0) if filtered_trials else 0
                }
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠ Scoring failed ({str(e)}), assigning default scores")
            
            # Fallback: assign default scores
            for trial in filtered_trials:
                trial['rank_score'] = 50
            
            global_memory['ranked_trials'] = filtered_trials
            
            return {
                "status": "error",
                "error": str(e),
                "trials_ranked": 0
            }
    
    def get_next_state(self) -> Optional[str]:
        return "prepare_summaries"


class PrepareTrialSummariesState(State):
    """State 5: Create concise summaries of top trials"""
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        # === DEBUG LOGGING ===
        from pprint import pformat
        ranked_trials = context.get("ranked_trials", [])[:10] if context else []
        
        print("\n" + "="*80)
        print("DEBUG: PrepareTrialSummariesState - ACTUAL TRIALS FROM API")
        print("="*80)
        print(f"Number of ranked trials: {len(ranked_trials)}")
        if ranked_trials:
            print("\nFirst 3 trials from API:")
            for i, trial in enumerate(ranked_trials[:3], 1):
                print(f"\n{i}. NCT ID: {trial.get('nct_id', 'MISSING')}")
                print(f"   Title: {trial.get('title', 'MISSING')[:80]}")
                print(f"   Status: {trial.get('status', 'MISSING')}")
                print(f"   Score: {trial.get('rank_score', 'MISSING')}")
        else:
            print("NO TRIALS FOUND!")
        print("="*80 + "\n")
        # === END DEBUG ===
        
        # Build trial list for LLM
        if not ranked_trials:
            return "No trials found to summarize."
        
        trial_data_text = "HERE ARE THE ACTUAL TRIAL DATA YOU MUST USE:\n\n"
        for i, trial in enumerate(ranked_trials, 1):
            locations = trial.get("locations", {})
            if isinstance(locations, dict):
                cities = locations.get("cities", [])
                location_str = cities[0] if cities else "Location not specified"
            else:
                location_str = "Location not specified"
            
            phase = trial.get("phase", "Unknown")
            if isinstance(phase, list):
                phase = phase[0] if phase else "Unknown"
            
            trial_data_text += f"""Trial {i}:
NCT ID: {trial.get('nct_id', 'Unknown')}
Title: {trial.get('title', 'No title')}
Phase: {phase}
Status: {trial.get('status', 'Unknown')}
Location: {location_str}
Rank Score: {trial.get('rank_score', 0)}
Brief Summary: {trial.get('brief_summary', 'Not available')[:200]}

"""
        
        return f"""{trial_data_text}

CRITICAL INSTRUCTIONS:
1. You MUST use the EXACT NCT IDs listed above
2. You MUST use the EXACT titles listed above
3. DO NOT create, invent, or modify any NCT IDs
4. DO NOT create fictional trial information

Create a JSON array summarizing these trials. Use ONLY the data provided above.

Return format:
[
{{
    "nct_id": "<EXACT NCT ID from above>",
    "title": "<EXACT title from above, truncated to 80 chars>",
    "phase": "<phase from above>",
    "status": "<status from above>",
    "location": "<location from above>",
    "rank_score": <score from above>,
    "key_criteria": ["See ClinicalTrials.gov for full criteria"]
}}
]

Return ONLY valid JSON. No explanation, no markdown."""

    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Parse summaries"""
        ranked_trials = global_memory.get("ranked_trials", [])[:10]
        
        try:
            # Extract JSON from response
            llm_response = llm_response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in llm_response:
                llm_response = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                lines = llm_response.split("\n")
                llm_response = "\n".join([l for l in lines if not l.startswith("```")])
            
            summaries = json.loads(llm_response)
            
            # Validate it's a list
            if not isinstance(summaries, list):
                raise ValueError("Response is not a list")
            
            print(f"📋 Prepared {len(summaries)} trial summaries")
            
            return {
                "trial_summaries": summaries,
                "trial_discovery_complete": True
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: create basic summaries from ranked trials
            print(f"⚠ Summary parsing failed ({str(e)}), creating basic summaries")
            
            basic_summaries = []
            for trial in ranked_trials:
                # Extract location intelligently
                locations = trial.get("locations", {})
                if isinstance(locations, dict):
                    cities = locations.get("cities", [])
                    location_str = cities[0] if cities else "See trial details"
                else:
                    location_str = "See trial details"
                
                # Handle phase (could be list or string)
                phase = trial.get("phase", "Unknown")
                if isinstance(phase, list):
                    phase = phase[0] if phase else "Unknown"
                
                basic_summaries.append({
                    "nct_id": trial.get("nct_id", "Unknown"),
                    "title": trial.get("title", "No title")[:80],
                    "phase": phase,
                    "status": trial.get("status", "Unknown"),
                    "location": location_str,
                    "rank_score": trial.get("rank_score", 0),
                    "key_criteria": ["See full eligibility criteria on ClinicalTrials.gov"]
                })
            
            return {
                "trial_summaries": basic_summaries,
                "trial_discovery_complete": True
            }
    
    def get_next_state(self) -> Optional[str]:
        return None  # Terminal state


class TrialDiscoveryStateMachine(StateMachine):
    """State machine for discovering and ranking clinical trials"""
    
    def __init__(self):
        super().__init__(name="TrialDiscovery")
        
        # Create all states
        state1 = GenerateSearchQueriesState(
            name="generate_queries",
            description="Generate optimized search queries from patient search terms"
        )
        state2 = ExecuteTrialSearchState(
            name="execute_search",
            description="Execute API searches to retrieve clinical trials"
        )
        state3 = DeduplicateAndFilterState(
            name="deduplicate",
            description="Remove duplicate trials and filter for active status"
        )
        state4 = RankTrialsState(
            name="rank_trials",
            description="Score and rank trials by relevance to patient profile"
        )
        state5 = PrepareTrialSummariesState(
            name="prepare_summaries",
            description="Create concise summaries of top-ranked trials"
        )
        
        # Add states to machine (first one with is_entry=True)
        self.add_state(state1, is_entry=True)
        self.add_state(state2)
        self.add_state(state3)
        self.add_state(state4)
        self.add_state(state5)