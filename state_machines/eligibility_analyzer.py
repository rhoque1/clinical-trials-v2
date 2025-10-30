"""
Eligibility Analyzer State Machine - Phase 3
Analyzes patient eligibility for clinical trials using hybrid rule-based and LLM reasoning.
"""

from typing import Dict, Any, Optional, List
from .base_state_machine import State, StateMachine
import json
import re


# ============================================================================
# STATE 1: Extract Trial Criteria
# ============================================================================
class ExtractTrialCriteriaState(State):
    """Parse inclusion/exclusion criteria from trial summaries into structured format."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are a clinical trial eligibility expert. Parse trial criteria into structured format.

For each trial, extract:
- Inclusion criteria (age, stage, biomarkers, histology, performance status)
- Exclusion criteria (prior treatments, comorbidities, organ dysfunction)

Return JSON format:
{
  "NCT_ID": {
    "inclusion": [
      {"type": "age", "operator": ">=", "value": 18},
      {"type": "stage", "values": ["IIIB", "IVA", "IVB"]},
      {"type": "biomarker", "name": "PD-L1", "threshold": 1, "unit": "%"}
    ],
    "exclusion": [
      {"type": "prior_treatment", "agent": "pembrolizumab"},
      {"type": "condition", "name": "brain_metastases", "modifier": "active"}
    ]
  }
}"""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        # Parse LLM JSON response
        try:
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                structured_criteria = json.loads(json_match.group(1))
            else:
                structured_criteria = json.loads(llm_response)
            
            global_memory["structured_criteria"] = structured_criteria
            return {
                "status": "success",
                "trials_processed": len(structured_criteria),
                "structured_criteria": structured_criteria
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse criteria: {str(e)}",
                "raw_response": llm_response[:500]
            }
    
    def get_next_state(self) -> Optional[str]:
        return "match_demographics"


# ============================================================================
# STATE 2: Match Demographics
# ============================================================================
class MatchDemographicsState(State):
    """Rule-based matching of age and sex criteria."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are performing deterministic demographic matching.

For each trial, check:
1. Age eligibility (patient age vs trial requirements)
2. Sex eligibility (if trial has sex restrictions)

Return JSON:
{
  "NCT_ID": {
    "age_eligible": true/false,
    "age_reasoning": "Patient is 40, trial requires >=18",
    "sex_eligible": true/false,
    "sex_reasoning": "Patient is female, trial allows all sexes",
    "demographic_pass": true/false
  }
}"""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                demographic_matches = json.loads(json_match.group(1))
            else:
                demographic_matches = json.loads(llm_response)
            
            global_memory["demographic_matches"] = demographic_matches
            
            # Count how many trials pass demographics
            passing_trials = sum(1 for trial in demographic_matches.values() 
                               if trial.get("demographic_pass", False))
            
            return {
                "status": "success",
                "passing_trials": passing_trials,
                "demographic_matches": demographic_matches
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse demographics: {str(e)}"
            }
    
    def get_next_state(self) -> Optional[str]:
        return "match_clinical_features"


# ============================================================================
# STATE 3: Match Clinical Features
# ============================================================================
class MatchClinicalFeaturesState(State):
    """Hybrid rule-based and LLM fuzzy matching for stage, histology, biomarkers."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are performing clinical feature matching using both exact and fuzzy logic.

For each trial (that passed demographics), assess:
1. Stage matching (exact or compatible stages)
2. Histology matching (exact or fuzzy - e.g., "squamous" matches "squamous cell carcinoma")
3. Biomarker matching (presence/absence, thresholds)
4. Performance status (if available)

Use these match types:
- "exact": Perfect match
- "fuzzy_high": Very likely compatible (95%+ confidence)
- "fuzzy_medium": Probably compatible (70-94% confidence)
- "fuzzy_low": Possibly compatible (50-69% confidence)
- "mismatch": Not compatible

Return JSON:
{
  "NCT_ID": {
    "stage_match": "exact",
    "stage_reasoning": "Patient IIIB matches trial requirement IIIB/IVA/IVB",
    "histology_match": "fuzzy_high",
    "histology_reasoning": "Patient 'squamous cell carcinoma' matches trial 'squamous'",
    "biomarker_matches": {
      "PD-L1": {"status": "match", "reasoning": "Patient 15% exceeds trial threshold 1%"},
      "HPV": {"status": "match", "reasoning": "Patient HPV-16+ matches trial HPV+ requirement"}
    },
    "clinical_score": 0.92
  }
}

Clinical score formula: (stage_weight * stage_score + histology_weight * histology_score + biomarker_weight * biomarker_score) / total_weight
Use weights: stage=0.3, histology=0.3, biomarkers=0.4"""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                clinical_matches = json.loads(json_match.group(1))
            else:
                clinical_matches = json.loads(llm_response)
            
            global_memory["clinical_matches"] = clinical_matches
            
            # Count high-scoring trials
            high_scoring = sum(1 for trial in clinical_matches.values() 
                             if trial.get("clinical_score", 0) >= 0.7)
            
            return {
                "status": "success",
                "high_scoring_trials": high_scoring,
                "clinical_matches": clinical_matches
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse clinical features: {str(e)}"
            }
    
    def get_next_state(self) -> Optional[str]:
        return "assess_eligibility"


# ============================================================================
# STATE 4: Assess Eligibility
# ============================================================================
class AssessEligibilityState(State):
    """LLM-driven assessment of complex eligibility criteria with chain-of-thought reasoning."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        return """You are a clinical trial eligibility expert performing detailed assessment.

For trials with high clinical scores (>=0.7), evaluate complex criteria that require medical reasoning:
- "Adequate organ function" - assess based on available labs
- "Life expectancy > X months" - infer from stage and performance status
- "Active brain metastases" - check imaging reports
- "Prior treatment requirements" - match treatment history
- "Washout periods" - calculate time since last therapy
- "Contraindications" - identify potential safety concerns

Use chain-of-thought reasoning for EACH complex criterion.

Return JSON:
{
  "NCT_ID": {
    "complex_criteria_assessment": [
      {
        "criterion": "adequate organ function",
        "assessment": "likely_eligible",
        "confidence": 0.7,
        "reasoning": "No organ dysfunction mentioned in report, but recent labs not available",
        "missing_data": ["Complete blood count", "Liver function tests"],
        "risk_level": "low"
      }
    ],
    "overall_eligibility": "highly_likely" | "likely" | "possible" | "unlikely",
    "confidence": 0.75,
    "barriers": ["Missing recent lab work"],
    "strengths": ["Exact stage match", "PD-L1 positive"]
  }
}

Confidence scoring:
- 0.9-1.0: All criteria clearly met
- 0.7-0.89: Most criteria met, minor gaps
- 0.5-0.69: Some criteria met, significant gaps
- <0.5: Major barriers present"""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                eligibility_assessments = json.loads(json_match.group(1))
            else:
                eligibility_assessments = json.loads(llm_response)
            
            global_memory["eligibility_assessments"] = eligibility_assessments
            
            # Count highly likely matches
            highly_likely = sum(1 for trial in eligibility_assessments.values() 
                              if trial.get("overall_eligibility") in ["highly_likely", "likely"])
            
            return {
                "status": "success",
                "highly_likely_matches": highly_likely,
                "eligibility_assessments": eligibility_assessments
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse eligibility assessments: {str(e)}"
            }
    
    def get_next_state(self) -> Optional[str]:
        return "generate_recommendations"


# ============================================================================
# STATE 5: Generate Recommendations
# ============================================================================
class GenerateRecommendationsState(State):
    """Synthesize all assessments into actionable recommendations."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)

    def get_instruction(self, context: Dict[str, Any] = None) -> str:
        # === DEBUG LOGGING ===
        print("\n" + "="*80)
        print("DEBUG: GenerateRecommendationsState.get_instruction() called")
        print("="*80)
        
        # Handle case where context might not be a dict
        if not context or not isinstance(context, dict):
            print("ERROR: Context is not a dictionary!")
            print(f"Context type: {type(context)}")
            print("="*80 + "\n")
            return "No valid context provided. Cannot generate recommendations."
        
        print(f"Context keys: {list(context.keys())}")
        
        # Get the actual trial data
        ranked_trials = context.get("ranked_trials", [])
        
        # Validate ranked_trials is a list
        if not isinstance(ranked_trials, list):
            print(f"ERROR: ranked_trials is not a list! Type: {type(ranked_trials)}")
            ranked_trials = []
        
        print(f"Number of trials in context: {len(ranked_trials)}")
        if ranked_trials:
            first_trial = ranked_trials[0]
            if isinstance(first_trial, dict):
                print(f"First trial NCT ID: {first_trial.get('nct_id', 'MISSING')}")
            else:
                print(f"ERROR: First trial is not a dict! Type: {type(first_trial)}")
        print("="*80 + "\n")
        # === END DEBUG ===
        
        if not ranked_trials:
            return "No trials available to generate recommendations."
        
        # Build trial list with ACTUAL data
        trial_data_text = "HERE ARE THE ACTUAL CLINICAL TRIALS YOU MUST USE:\n\n"
        for i, trial in enumerate(ranked_trials[:10], 1):
            if not isinstance(trial, dict):
                continue
                
            trial_data_text += f"""Trial {i}:
    NCT ID: {trial.get('nct_id', 'Unknown')}
    Title: {trial.get('title', 'No title')}
    Phase: {trial.get('phase', 'Unknown')}
    Status: {trial.get('status', 'Unknown')}
    Location: {trial.get('location', 'Not specified')}
    Key Criteria: {', '.join(trial.get('key_criteria', ['See ClinicalTrials.gov']))}

    """
        
        # Get patient diagnosis for context
        patient_profile = context.get("patient_profile", {})
        if isinstance(patient_profile, dict):
            diagnoses = patient_profile.get('diagnoses', 'Not available')
            if isinstance(diagnoses, str):
                diagnoses = diagnoses[:300]
            else:
                diagnoses = 'Not available'
        else:
            diagnoses = 'Not available'
        
        return f"""{trial_data_text}

    PATIENT CONTEXT (for reference):
    {diagnoses}

    CRITICAL INSTRUCTIONS - READ CAREFULLY:
    1. You MUST use ONLY the EXACT NCT IDs listed above
    2. You MUST use ONLY the EXACT trial titles listed above
    3. DO NOT create, invent, fabricate, or modify ANY NCT IDs
    4. DO NOT create fictional trial information
    5. Each recommendation MUST reference an actual trial from the list above

    Create a JSON report with the top 3-5 most relevant trials from the list above.

    Return format:
    {{
    "top_matches": [
        {{
        "rank": 1,
        "nct_id": "<EXACT NCT ID from above>",
        "trial_title": "<EXACT title from above>",
        "match_score": 85,
        "eligibility_status": "highly_likely",
        "strengths": ["List 2-3 key matches"],
        "concerns": ["List 1-2 concerns if any"],
        "required_actions": ["List specific next steps"],
        "estimated_time_to_enrollment": "2-4 weeks",
        "next_steps": "Contact information from trial data",
        "location": "<location from above>"
        }}
    ],
    "summary": "Brief summary of findings",
    "overall_recommendation": "Primary recommendation"
    }}

    Return ONLY valid JSON. No explanation, no markdown blocks."""
    
    def process_input(self, llm_response: str, global_memory: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                final_recommendations = json.loads(json_match.group(1))
            else:
                final_recommendations = json.loads(llm_response)
            
            global_memory["final_recommendations"] = final_recommendations
            
            return {
                "status": "success",
                "top_matches_count": len(final_recommendations.get("top_matches", [])),
                "final_recommendations": final_recommendations
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse recommendations: {str(e)}"
            }
    
    def get_next_state(self) -> Optional[str]:
        return None  # Terminal state


# ============================================================================
# ELIGIBILITY ANALYZER STATE MACHINE
# ============================================================================
class EligibilityAnalyzer(StateMachine):
    """
    Phase 3: Eligibility Analyzer
    Analyzes patient eligibility for top-ranked trials using hybrid reasoning.
    """
    
    def __init__(self):
        super().__init__(name="EligibilityAnalyzer")
        
        # State 1: Extract structured criteria from trial summaries
        state1 = ExtractTrialCriteriaState(
            name="extract_criteria",
            description="Parse inclusion/exclusion criteria into structured format"
        )
        self.add_state(state1, is_entry=True)
        
        # State 2: Rule-based demographic matching
        state2 = MatchDemographicsState(
            name="match_demographics",
            description="Match age and sex criteria using deterministic rules"
        )
        self.add_state(state2)
        
        # State 3: Hybrid clinical feature matching
        state3 = MatchClinicalFeaturesState(
            name="match_clinical_features",
            description="Match stage, histology, biomarkers using rules + LLM fuzzy logic"
        )
        self.add_state(state3)
        
        # State 4: Complex eligibility assessment
        state4 = AssessEligibilityState(
            name="assess_eligibility",
            description="Evaluate complex criteria with chain-of-thought reasoning"
        )
        self.add_state(state4)
        
        # State 5: Final recommendations
        state5 = GenerateRecommendationsState(
            name="generate_recommendations",
            description="Synthesize assessments into actionable recommendations"
        )
        self.add_state(state5)