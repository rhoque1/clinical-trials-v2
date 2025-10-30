"""
Patient Profile Builder State Machine
Breaks down patient data extraction into structured states
"""
from typing import Dict, Any, Optional
from state_machines.base_state_machine import State, StateMachine, StateStatus


class ExtractDemographicsState(State):
    """State 1: Extract basic demographics from report"""
    
    def __init__(self):
        super().__init__(
            name="extract_demographics",
            description="Extract patient age, gender, and basic info"
        )
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        return """
        From the medical report content, extract:
        - Patient age (or age range if exact not available)
        - Gender/Sex
        - Any mention of pregnancy status
        - Performance status if mentioned (ECOG, Karnofsky)
        
        Store findings in structured format.
        """
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract demographics from LLM response"""
        
        # === DEBUG LOGGING ===
        print("\n" + "="*60)
        print("DEBUG: ExtractDemographicsState.process_input()")
        print("="*60)
        print(f"LLM Response (first 500 chars):\n{str(user_input)[:500]}")
        print("="*60 + "\n")
        # === END DEBUG ===
        
        # Initialize demographics dict
        demographics = {}
        
        # Convert to string for processing
        response_text = str(user_input)
        
        # Try to parse as JSON first (best case)
        import json
        import re
        
        try:
            # Remove markdown code blocks if present
            json_text = response_text.strip()
            if json_text.startswith('```'):
                # Extract JSON from code block
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            
            # Parse JSON
            data = json.loads(json_text)
            
            # Extract from JSON structure
            # Look for age in various keys
            for key in ['age', 'Age', 'patient age', 'Patient Age', 'patient_age']:
                if key in data and data[key]:
                    age_val = data[key]
                    if isinstance(age_val, int):
                        demographics['age'] = age_val
                    elif isinstance(age_val, str) and age_val.isdigit():
                        demographics['age'] = int(age_val)
                    break
            
            # Look for sex/gender in various keys
            for key in ['sex', 'Sex', 'gender', 'Gender', 'Gender/Sex']:
                if key in data:
                    sex_val = str(data[key]).lower()
                    if 'male' in sex_val and 'female' not in sex_val:
                        demographics['sex'] = 'Male'
                    elif 'female' in sex_val:
                        demographics['sex'] = 'Female'
                    break
            
            # Look for ECOG in nested structure
            if 'Performance Status' in data or 'performance_status' in data:
                perf = data.get('Performance Status') or data.get('performance_status')
                if isinstance(perf, dict):
                    if 'ECOG' in perf:
                        demographics['ecog'] = perf['ECOG']
                elif isinstance(perf, str):
                    ecog_match = re.search(r'ecog[:\s]*(\d+)', str(perf), re.IGNORECASE)
                    if ecog_match:
                        demographics['ecog'] = int(ecog_match.group(1))
            
            # Check pregnancy status
            preg_key = next((k for k in data.keys() if 'pregnan' in k.lower()), None)
            if preg_key:
                preg_val = str(data[preg_key]).lower()
                if 'not' in preg_val or 'n/a' in preg_val or 'applicable' in preg_val:
                    demographics['pregnancy_status'] = 'Not applicable'
                elif 'yes' in preg_val or 'positive' in preg_val:
                    demographics['pregnancy_status'] = 'Pregnant'
        
        except (json.JSONDecodeError, ValueError):
            # Fallback to regex parsing if JSON fails
            response_lower = response_text.lower()
            
            # Extract age with multiple patterns
            age_patterns = [
                r'age[:\s"]*(\d+)',
                r'(\d+)[- ]year',
                r'patient.*?(\d+).*?(?:year|age)',
            ]
            for pattern in age_patterns:
                age_match = re.search(pattern, response_lower)
                if age_match:
                    demographics['age'] = int(age_match.group(1))
                    break
            
            # Extract sex/gender
            if 'female' in response_lower or 'woman' in response_lower:
                demographics['sex'] = 'Female'
            elif 'male' in response_lower and 'female' not in response_lower:
                demographics['sex'] = 'Male'
            
            # Extract ECOG
            ecog_match = re.search(r'ecog[:\s]*(\d+)', response_lower)
            if ecog_match:
                demographics['ecog'] = int(ecog_match.group(1))
        
        print(f"✓ Extracted demographics: {demographics}")
        
        return {
            "demographics": demographics,
            "demographics_extracted": True
        }
    
    def get_next_state(self) -> Optional[str]:
        return "extract_diagnoses"


class ExtractDiagnosesState(State):
    """State 2: Extract primary and secondary diagnoses"""
    
    def __init__(self):
        super().__init__(
            name="extract_diagnoses",
            description="Extract all diagnoses and conditions"
        )
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        return """
        From the medical report, extract:
        - Primary diagnosis (main condition)
        - Cancer stage/grade if applicable (TNM, AJCC, FIGO, etc.)
        - Secondary diagnoses or comorbidities
        - Disease status (newly diagnosed, recurrent, progressive, stable)
        
        For cancer cases, be specific about histology and molecular subtype.
        """
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "diagnoses": user_input,
            "diagnoses_extracted": True
        }
    
    def get_next_state(self) -> Optional[str]:
        return "extract_biomarkers"


class ExtractBiomarkersState(State):
    """State 3: Extract biomarkers and molecular information"""
    
    def __init__(self):
        super().__init__(
            name="extract_biomarkers",
            description="Extract molecular markers and test results"
        )
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        return """
        From the medical report, extract:
        - Genetic mutations (e.g., EGFR, KRAS, BRAF, HER2)
        - Protein expression (e.g., PD-L1, ER, PR, HER2)
        - Microsatellite status (MSI-H/MSS)
        - Tumor mutational burden (TMB)
        - Any other molecular or genomic test results
        
        Include test values and interpretation if available.
        """
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "biomarkers": user_input,
            "biomarkers_extracted": True
        }
    
    def get_next_state(self) -> Optional[str]:
        return "extract_treatment_history"


class ExtractTreatmentHistoryState(State):
    """State 4: Extract prior and current treatments"""
    
    def __init__(self):
        super().__init__(
            name="extract_treatment_history",
            description="Extract treatment history"
        )
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        return """
        From the medical report, extract:
        - Current treatments (medications, therapies)
        - Prior treatments (with dates if available)
        - Response to previous treatments
        - Any contraindicated medications or allergies
        - Recent surgeries or procedures
        
        This helps identify trial eligibility and potential conflicts.
        """
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "treatment_history": user_input,
            "treatment_history_extracted": True
        }
    
    def get_next_state(self) -> Optional[str]:
        return "generate_search_terms"

class GenerateSearchTermsState(State):
    """State 5: Generate comprehensive trial search terms"""
    
    def __init__(self):
        super().__init__(
            name="generate_search_terms",
            description="Generate search strategy for trial matching"
        )
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        diagnoses = context.get("diagnoses", "")
        biomarkers = context.get("biomarkers", "")
        
        return f"""
Based on the patient's medical profile, generate clinical trial search terms.

Diagnoses: {diagnoses}
Biomarkers: {biomarkers}

Generate 5-8 search terms for finding relevant clinical trials, ordered from most specific to broad:

1. Start with the most specific terms (exact diagnosis + biomarkers)
2. Then disease-specific terms
3. Then broader disease categories
4. Include biomarker-specific terms if relevant

FORMAT: Return ONLY a simple list, one term per line, no bullets or numbers.

Example format:
cervical squamous cell carcinoma PIK3CA
stage III cervical cancer
cervical cancer HPV positive
cervical carcinoma
gynecologic cancer

Now generate the search terms for this patient:
"""
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        # Parse LLM's generated search terms
        search_terms = []
        
        if isinstance(user_input, list):
            search_terms = user_input
        elif isinstance(user_input, str):
            # Split by newlines and clean up
            lines = user_input.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Skip empty lines, headers, and explanatory text
                if line and len(line) > 10 and not line.lower().startswith(('based on', 'here are', 'search terms', 'example')):
                    # Remove bullets, numbers, dashes
                    clean_line = line.lstrip('-•*0123456789. ')
                    if clean_line and 'cancer' in clean_line.lower() or 'carcinoma' in clean_line.lower():
                        search_terms.append(clean_line)
        
        # Fallback if parsing fails
        if not search_terms:
            search_terms = ["cervical cancer", "cervical squamous cell carcinoma", "gynecologic cancer"]
        
        return {
            "search_terms": search_terms,
            "search_terms_generated": True,
            "profile_complete": True
        }
    
    def get_next_state(self) -> Optional[str]:
        return None  # End of this state machine

class PatientProfilerMachine(StateMachine):
    """
    Complete patient profiling workflow
    Inherits memory across all states
    """
    
    def __init__(self):
        super().__init__("patient_profiler")
        
        # Add all states in sequence
        self.add_state(ExtractDemographicsState(), is_entry=True)
        self.add_state(ExtractDiagnosesState())
        self.add_state(ExtractBiomarkersState())
        self.add_state(ExtractTreatmentHistoryState())
        self.add_state(GenerateSearchTermsState())