"""
Keyword-based baseline matcher for clinical trial matching.
Mimics traditional ClinicalTrials.gov search behavior using keyword extraction
and TF-IDF similarity ranking.
"""

from typing import Dict, List, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class KeywordBaseline:
    """
    Baseline clinical trial matcher using keyword search and basic filtering.
    
    This represents the "traditional" approach that our LLM-based system
    will be compared against in evaluation.
    """
    
    def __init__(self, api_client):
        """
        Initialize keyword baseline matcher.
        
        Args:
            api_client: ClinicalTrialsAPI instance for searching trials
        """
        self.api_client = api_client
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)  # unigrams and bigrams
        )
    
    def extract_keywords(self, patient_profile: Dict[str, Any]) -> List[str]:
        """
        Extract search keywords from patient profile JSON.

        Args:
            patient_profile: Output from Phase 1 (Patient Profiler)

        Returns:
            List of keyword strings for API search

        Example output:
            ["cervical cancer", "stage IIIB", "squamous cell", "PD-L1 positive",
             "HPV positive", "recurrent disease"]
        """
        keywords = []

        # Priority 1: Diagnosis (highest priority)
        clinical_features = patient_profile.get("clinical_features", {})
        diagnosis = clinical_features.get("diagnosis", "")
        if diagnosis:
            keywords.append(diagnosis.lower())

        # Priority 2: Stage
        stage = clinical_features.get("stage", "")
        if stage:
            keywords.append(f"stage {stage}".lower())

        # Priority 3: Histology
        histology = clinical_features.get("histology", "")
        if histology and histology.lower() != diagnosis.lower():
            keywords.append(histology.lower())

        # Priority 4: Key biomarkers (skip negative/normal values)
        biomarkers = patient_profile.get("biomarkers", {})
        for marker, value in biomarkers.items():
            if value and value.lower() not in ["negative", "wild-type", "normal", "mss"]:
                # Create meaningful biomarker phrases
                if "positive" in value.lower():
                    keywords.append(f"{marker} positive".lower())
                elif "mutation" in value.lower():
                    keywords.append(f"{marker} mutation".lower())
                else:
                    # For specific values like "15% CPS", include marker name
                    keywords.append(f"{marker}".lower())

        # Priority 5: Treatment status keywords
        treatment_history = patient_profile.get("treatment_history", {})
        current_status = treatment_history.get("current_status", "")
        if current_status:
            # Extract keywords like "recurrent", "progressive", "refractory"
            status_lower = current_status.lower()
            if any(term in status_lower for term in ["recurrent", "progressive", "refractory", "resistant"]):
                keywords.append(current_status.lower())

        # Use pre-computed search_terms if available (from Phase 1)
        search_terms = patient_profile.get("search_terms", [])
        if search_terms:
            keywords.extend([term.lower() for term in search_terms])

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen and kw.strip():
                seen.add(kw)
                unique_keywords.append(kw.strip())

        return unique_keywords
    
    def search_trials(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """
        Query ClinicalTrials.gov API with extracted keywords.

        Args:
            keywords: List of search terms
            max_results: Maximum number of trials to retrieve

        Returns:
            List of trial dictionaries with metadata
        """
        if not keywords:
            return []

        # Use the search_clinical_trials_targeted function from the API module
        # It expects a list of conditions and returns studies
        result = self.api_client(
            conditions=keywords[:3],  # Use top 3 keywords to avoid overly restrictive search
            max_studies=max_results
        )

        # Handle the wrapped response format
        if isinstance(result, dict) and result.get("status") == "success":
            trials = result.get("data", [])
        elif isinstance(result, dict) and result.get("status") == "error":
            print(f"API Error: {result.get('title', 'Unknown error')}")
            return []
        else:
            trials = result if isinstance(result, list) else []

        # The API already filters for RECRUITING/NOT_YET_RECRUITING/ACTIVE_NOT_RECRUITING
        # Now we need to enrich the trial data with full text for ranking
        enriched_trials = []
        for trial in trials:
            # Create a full text representation for TF-IDF ranking
            trial_text_parts = [
                trial.get("title", ""),
                trial.get("official_title", ""),
                trial.get("brief_summary", ""),
                " ".join(trial.get("conditions", [])),
                " ".join(trial.get("interventions", []))
            ]
            trial["full_text"] = " ".join(filter(None, trial_text_parts))
            enriched_trials.append(trial)

        return enriched_trials
    
    def apply_basic_filters(self, patient_profile: Dict[str, Any],
                           trials: List[Dict]) -> List[Dict]:
        """
        Apply basic eligibility filters (age, sex, ECOG).

        Args:
            patient_profile: Patient data from Phase 1
            trials: List of candidate trials

        Returns:
            Filtered list of trials meeting basic criteria
        """
        filtered = []

        # Extract patient demographics
        demographics = patient_profile.get("demographics", {})
        patient_age = demographics.get("age")
        patient_sex = demographics.get("sex", "").upper()
        patient_ecog = demographics.get("ecog")

        for trial in trials:
            eligibility = trial.get("eligibility", {})

            # Check 1: Age filter
            min_age_str = eligibility.get("min_age", "N/A")
            max_age_str = eligibility.get("max_age", "N/A")

            # Parse age strings (e.g., "18 Years" -> 18)
            min_age = self._parse_age(min_age_str)
            max_age = self._parse_age(max_age_str)

            if patient_age is not None:
                if min_age is not None and patient_age < min_age:
                    continue  # Patient too young
                if max_age is not None and patient_age > max_age:
                    continue  # Patient too old

            # Check 2: Sex filter
            trial_gender = eligibility.get("gender", "ALL").upper()
            if trial_gender not in ["ALL", "UNKNOWN"]:
                # Map trial gender to patient sex
                if trial_gender == "MALE" and patient_sex != "MALE":
                    continue
                if trial_gender == "FEMALE" and patient_sex != "FEMALE":
                    continue

            # Check 3: ECOG filter (optional - most trials don't specify in API)
            # We'll be conservative and accept the trial if ECOG is not specified
            # In reality, ECOG is usually in the detailed eligibility criteria text

            # If all checks pass, include the trial
            filtered.append(trial)

        return filtered

    def _parse_age(self, age_str: str) -> Optional[int]:
        """
        Parse age string from API (e.g., '18 Years', 'N/A', '65 Years') into integer.

        Args:
            age_str: Age string from ClinicalTrials.gov API

        Returns:
            Integer age or None if not specified
        """
        if not age_str or age_str.upper() in ["N/A", "NOT SPECIFIED", "UNKNOWN"]:
            return None

        # Extract numeric part
        import re
        match = re.search(r'\d+', age_str)
        if match:
            return int(match.group())

        return None
    
    def rank_by_similarity(self, patient_profile: Dict[str, Any],
                          trials: List[Dict], top_k: int = 5) -> List[tuple]:
        """
        Rank trials by TF-IDF similarity to patient profile.

        Args:
            patient_profile: Patient data
            trials: Filtered candidate trials
            top_k: Number of top trials to return

        Returns:
            List of (trial, score) tuples, sorted by score descending
        """
        if not trials:
            return []

        # Step 1: Create patient text representation
        patient_text_parts = []

        # Add diagnosis and clinical features
        clinical_features = patient_profile.get("clinical_features", {})
        for key, value in clinical_features.items():
            if value:
                patient_text_parts.append(str(value))

        # Add biomarkers
        biomarkers = patient_profile.get("biomarkers", {})
        for marker, value in biomarkers.items():
            if value:
                patient_text_parts.append(f"{marker} {value}")

        # Add treatment history
        treatment_history = patient_profile.get("treatment_history", {})
        prior_treatments = treatment_history.get("prior_treatments", [])
        patient_text_parts.extend(prior_treatments)

        current_status = treatment_history.get("current_status", "")
        if current_status:
            patient_text_parts.append(current_status)

        # Add search terms if available
        search_terms = patient_profile.get("search_terms", [])
        patient_text_parts.extend(search_terms)

        patient_text = " ".join(patient_text_parts)

        # Step 2: Collect trial texts (already enriched with full_text in search_trials)
        trial_texts = [trial.get("full_text", "") for trial in trials]

        # Step 3: Compute TF-IDF vectors
        # Combine patient text and trial texts for vectorization
        all_texts = [patient_text] + trial_texts

        # Fit and transform
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Patient vector is the first one
        patient_vector = tfidf_matrix[0:1]

        # Trial vectors are the rest
        trial_vectors = tfidf_matrix[1:]

        # Step 4: Calculate cosine similarity
        similarities = cosine_similarity(patient_vector, trial_vectors)[0]

        # Step 5: Create (trial, score) tuples and sort
        trial_scores = []
        for i, trial in enumerate(trials):
            # Scale similarity to 0-100
            score = similarities[i] * 100
            trial_scores.append((trial, score))

        # Sort by score descending
        trial_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top_k
        return trial_scores[:top_k]
    
    def match_patient(self, patient_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method: End-to-end baseline matching pipeline.
        
        Args:
            patient_profile: Output from Phase 1 (Patient Profiler)
            
        Returns:
            Dictionary with:
            {
                "method": "keyword_baseline",
                "top_trials": [
                    {
                        "nct_id": "NCT12345678",
                        "title": "...",
                        "score": 78.5,
                        "reasoning": "Matched keywords: cervical cancer, PD-L1+"
                    },
                    ...
                ],
                "metadata": {
                    "keywords_used": [...],
                    "trials_searched": 50,
                    "trials_filtered": 15
                }
            }
        """
        result = {
            "method": "keyword_baseline",
            "top_trials": [],
            "metadata": {}
        }
        
        # Step 1: Extract keywords
        keywords = self.extract_keywords(patient_profile)
        
        # Step 2: Search trials
        trials = self.search_trials(keywords)
        
        # Step 3: Apply basic filters
        filtered_trials = self.apply_basic_filters(patient_profile, trials)
        
        # Step 4: Rank by similarity
        ranked = self.rank_by_similarity(patient_profile, filtered_trials, top_k=5)
        
        # Step 5: Format output
        result["metadata"]["keywords_used"] = keywords
        result["metadata"]["trials_searched"] = len(trials)
        result["metadata"]["trials_filtered"] = len(filtered_trials)

        # Format top_trials list
        for trial, score in ranked:
            # Extract keywords that matched (simplified - just use top keywords)
            matched_keywords = keywords[:3]  # Top 3 keywords used in search

            result["top_trials"].append({
                "nct_id": trial.get("nct_id", "Unknown"),
                "title": trial.get("title", "Unknown"),
                "score": round(score, 1),
                "reasoning": f"Matched keywords: {', '.join(matched_keywords)}"
            })

        return result


def load_patient_profile(filepath: str) -> Dict[str, Any]:
    """
    Helper function: Load patient profile JSON from Phase 1 output.
    
    Args:
        filepath: Path to patient profile JSON file
        
    Returns:
        Patient profile dictionary
    """
    import json
    with open(filepath, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Test the baseline on tccr.pdf case
    from clinical_trials_api import ClinicalTrialsAPI
    
    # Initialize
    api = ClinicalTrialsAPI()
    baseline = KeywordBaseline(api)
    
    # Load patient profile (you'll need the actual path)
    patient = load_patient_profile("output/patient_profile_tccr.json")
    
    # Run matching
    results = baseline.match_patient(patient)
    
    # Print results
    print(f"\nKeyword Baseline Results:")
    print(f"Keywords used: {results['metadata']['keywords_used']}")
    print(f"Trials searched: {results['metadata']['trials_searched']}")
    print(f"Trials after filtering: {results['metadata']['trials_filtered']}")
    print(f"\nTop 5 Matches:")
    for i, trial in enumerate(results['top_trials'], 1):
        print(f"{i}. {trial['nct_id']} (Score: {trial['score']:.1f})")
        print(f"   {trial['title']}")
        print(f"   Reasoning: {trial['reasoning']}\n")