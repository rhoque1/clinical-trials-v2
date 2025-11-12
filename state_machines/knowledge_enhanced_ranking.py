"""
Phase 2.5: Knowledge-Enhanced Trial Ranking
Uses RAG to enrich trial scoring with clinical guideline context
"""
import sys
sys.path.append('..')

from typing import Dict, Any, Optional, List
from state_machines.base_state_machine import State, StateMachine
from tools.clinical_rag import ClinicalRAG


class KnowledgeEnhancedRankingState(State):
    """
    Enriches trial ranking with clinical practice guideline context
    Inserts between Trial Discovery and Eligibility Analysis
    """
    
    def __init__(self, disable_rag_for_experiment: bool = False):
        super().__init__(
            name="knowledge_enhanced_ranking",
            description="Enrich trial rankings with clinical guideline context"
        )
        
        # === EXPERIMENT CONTROL: Toggle RAG for causation testing ===
        # Set to True to disable RAG and test baseline (control group)
        # Set to False for normal RAG-enhanced operation (treatment group)
        if disable_rag_for_experiment:
            print("\n" + "="*70)
            print("[!]  EXPERIMENT MODE: RAG DISABLED (Control Group)")
            print("="*70 + "\n")
            self.rag = None
            return
        # === END EXPERIMENT CONTROL ===
        
        # Initialize RAG system (loads existing vectorstore)
        self.rag = ClinicalRAG()
        try:
            self.rag.build_vectorstore(force_rebuild=False)
            print("[+] RAG system loaded for knowledge enhancement")
        except Exception as e:
            print(f"[!]  RAG system not available: {e}")
            self.rag = None
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
# === EXPERIMENT: Skip instruction if RAG disabled ===
        if self.rag is None:
            return "RAG is disabled. Return the original trial rankings unchanged."
        # === END EXPERIMENT ===
        patient = context.get("patient_profile", {})
        diagnoses = patient.get("diagnoses", "")
        biomarkers = patient.get("biomarkers", "")
        
        # Get top ranked trials from Phase 2
        ranked_trials = context.get("ranked_trials", [])[:10]  # Top 10 only
        
        # Retrieve relevant clinical guidelines
        guideline_context = ""
        if self.rag:
            query = f"{diagnoses} {biomarkers} treatment guidelines"
            results = self.rag.retrieve(query, k=3)

            # === DEBUG: Show what RAG retrieved ===
            print("\n" + "="*70)
            print("[SEARCH] RAG RETRIEVAL DEBUG")
            print("="*70)
            print(f"Query: {query[:100]}...")
            print(f"\nRetrieved {len(results)} guideline chunks:")
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] Source: {result['source']}")
                print(f"      Category: {result['category']}")
                print(f"      Content preview: {result['content'][:200]}...")
            print("="*70 + "\n")
            
            guideline_context = "\n\n=== RELEVANT CLINICAL GUIDELINES ===\n"
            for i, result in enumerate(results, 1):
                guideline_context += f"\n[Guideline {i}] From {result['source']}:\n"
                guideline_context += f"{result['content'][:500]}...\n"
        
        trial_summaries = "\n\n".join([
            f"Trial {i+1}: {trial['nct_id']} - {trial['title'][:100]}\n"
            f"Intervention: {trial.get('intervention', 'N/A')}\n"
            f"Current Score: {trial.get('score', 50)}"
            for i, trial in enumerate(ranked_trials)
        ])
        
        return f"""
You are enhancing clinical trial rankings with evidence-based guideline context.

PATIENT PROFILE:
Diagnosis: {diagnoses}
Biomarkers: {biomarkers}

{guideline_context}

TOP RANKED TRIALS:
{trial_summaries}

TASK:
For each trial, assess:
1. **Guideline Alignment**: Does the intervention align with standard-of-care recommendations from clinical guidelines?
2. **Evidence Level**: Is this intervention supported by high-quality evidence (Phase 3 trials, FDA approval)?
3. **Appropriateness**: Is this trial appropriate for this patient's specific disease characteristics?

For each trial, provide:
- guideline_score (0-100): Higher if intervention aligns with clinical guidelines
- guideline_rationale: Brief explanation citing the guideline context
- adjusted_score: New overall score combining original ranking + guideline alignment

Return as JSON array:
[
  {{
    "nct_id": "NCT...",
    "original_score": 85,
    "guideline_score": 90,
    "guideline_rationale": "Osimertinib is NCCN Category 1 recommendation for EGFR exon 19 deletions",
    "adjusted_score": 88
  }},
  ...
]
"""
    
    def process_input(self, llm_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM's guideline-enhanced scores"""

        # === EXPERIMENT: Return original scores if RAG disabled ===
        if self.rag is None:
            print("[+] RAG disabled - returning original trial scores (no enhancement)")
            ranked_trials = context.get("ranked_trials", [])
            return {
                "knowledge_enhanced": False,
                "ranked_trials": ranked_trials,
                "enhancement_count": 0
            }
        # === END EXPERIMENT ===
        
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                enhanced_scores = json.loads(json_match.group(0))
            else:
                # Fallback: return original scores
                ranked_trials = context.get("ranked_trials", [])[:10]
                enhanced_scores = [
                    {
                        "nct_id": trial["nct_id"],
                        "original_score": trial.get("score", 50),
                        "guideline_score": 50,
                        "guideline_rationale": "No guideline context available",
                        "adjusted_score": trial.get("score", 50)
                    }
                    for trial in ranked_trials
                ]
            
            # Update ranked_trials with new scores
            ranked_trials = context.get("ranked_trials", [])
            
            # Create mapping of NCT ID to enhanced score
            score_map = {item["nct_id"]: item for item in enhanced_scores}
            
            # Update trials with enhanced scores
            for trial in ranked_trials:
                nct_id = trial["nct_id"]
                if nct_id in score_map:
                    enhanced = score_map[nct_id]
                    trial["original_score"] = trial.get("score", 50)
                    trial["guideline_score"] = enhanced.get("guideline_score", 50)
                    trial["guideline_rationale"] = enhanced.get("guideline_rationale", "")
                    trial["score"] = enhanced.get("adjusted_score", trial.get("score", 50))
            
            # Re-sort by new adjusted scores
            ranked_trials.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            print(f"[+] Knowledge-enhanced ranking complete")
            print(f"  Top 3 trials after guideline enrichment:")
            for i, trial in enumerate(ranked_trials[:3], 1):
                print(f"    {i}. {trial['nct_id']} (Score: {trial.get('score', 'N/A')}, "
                      f"Guideline: {trial.get('guideline_score', 'N/A')})")
            
            return {
                "knowledge_enhanced": True,
                "ranked_trials": ranked_trials,
                "enhancement_count": len(enhanced_scores)
            }
            
        except Exception as e:
            print(f"[!]  Error in knowledge enhancement: {e}")
            # Return original rankings if enhancement fails
            return {
                "knowledge_enhanced": False,
                "ranked_trials": context.get("ranked_trials", []),
                "error": str(e)
            }
    
    def get_next_state(self) -> Optional[str]:
        return None  # This is a standalone enhancement state


class KnowledgeEnhancedRankingMachine(StateMachine):
    """Single-state machine for guideline enrichment"""
    
    def __init__(self, disable_rag_for_experiment: bool = False):
        super().__init__("knowledge_enhanced_ranking")
        self.add_state(KnowledgeEnhancedRankingState(disable_rag_for_experiment), is_entry=True)