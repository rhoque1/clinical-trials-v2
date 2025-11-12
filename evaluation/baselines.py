"""
Baseline Methods for Clinical Trial Matching
4 methods to compare against the RAG-enhanced system
"""
import asyncio
import json
from typing import Dict, List, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Baseline 1: Keyword Search
class KeywordSearchBaseline:
    """
    Baseline 1: Use ClinicalTrials.gov API only, no re-ranking
    Returns trials in the order provided by the API
    """

    def __init__(self):
        from tools.search_clinical_trials import search_clinical_trials
        self.search_tool = search_clinical_trials

    async def rank_trials(self, patient_profile: Dict[str, Any]) -> List[Dict]:
        """
        Search trials using API, return in API order (no re-ranking)
        """
        search_terms = patient_profile.get('search_terms', [])

        # Collect all trials from all search terms
        all_trials = []
        seen_nct_ids = set()

        for term in search_terms:
            results = await self.search_tool(term, max_results=20)

            if results.get('success'):
                for trial in results.get('trials', []):
                    nct_id = trial.get('nct_id')
                    if nct_id and nct_id not in seen_nct_ids:
                        seen_nct_ids.add(nct_id)
                        all_trials.append({
                            'nct_id': nct_id,
                            'title': trial.get('title', ''),
                            'status': trial.get('status', ''),
                            'score': 1.0,  # No ranking, all equal
                            'method': 'keyword_search'
                        })

        return all_trials[:50]  # Return top 50


# Baseline 2: TF-IDF Vector Similarity
class TFIDFBaseline:
    """
    Baseline 2: TF-IDF vector similarity between patient profile and trial descriptions
    No LLM, pure classical IR
    """

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        from tools.search_clinical_trials import search_clinical_trials

        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.cosine_similarity = cosine_similarity
        self.search_tool = search_clinical_trials

    async def rank_trials(self, patient_profile: Dict[str, Any]) -> List[Dict]:
        """
        1. Search trials using API
        2. Build TF-IDF vectors for patient profile and trial descriptions
        3. Rank by cosine similarity
        """
        search_terms = patient_profile.get('search_terms', [])

        # Collect all trials
        all_trials = []
        seen_nct_ids = set()

        for term in search_terms:
            results = await self.search_tool(term, max_results=20)

            if results.get('success'):
                for trial in results.get('trials', []):
                    nct_id = trial.get('nct_id')
                    if nct_id and nct_id not in seen_nct_ids:
                        seen_nct_ids.add(nct_id)
                        all_trials.append(trial)

        if not all_trials:
            return []

        # Build patient query
        patient_query = self._build_patient_query(patient_profile)

        # Build corpus: [patient_query] + [trial_description_1, trial_description_2, ...]
        trial_descriptions = [self._build_trial_description(t) for t in all_trials]
        corpus = [patient_query] + trial_descriptions

        # Compute TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # Cosine similarity between patient (index 0) and all trials (index 1+)
        patient_vector = tfidf_matrix[0]
        trial_vectors = tfidf_matrix[1:]
        similarities = self.cosine_similarity(patient_vector, trial_vectors)[0]

        # Rank trials by similarity
        ranked_trials = []
        for i, trial in enumerate(all_trials):
            ranked_trials.append({
                'nct_id': trial.get('nct_id'),
                'title': trial.get('title', ''),
                'status': trial.get('status', ''),
                'score': float(similarities[i]),
                'method': 'tfidf'
            })

        # Sort by score descending
        ranked_trials.sort(key=lambda x: x['score'], reverse=True)

        return ranked_trials[:50]

    def _build_patient_query(self, profile: Dict) -> str:
        """Build text query from patient profile"""
        parts = []

        if profile.get('diagnoses'):
            parts.append(str(profile['diagnoses']))
        if profile.get('biomarkers'):
            parts.append(str(profile['biomarkers']))
        if profile.get('search_terms'):
            parts.extend(profile['search_terms'])

        return " ".join(parts)

    def _build_trial_description(self, trial: Dict) -> str:
        """Build text description from trial"""
        parts = []

        if trial.get('title'):
            parts.append(trial['title'])
        if trial.get('brief_summary'):
            parts.append(trial['brief_summary'])
        if trial.get('conditions'):
            parts.extend(trial['conditions'])

        return " ".join(parts)


# Baseline 3: Zero-Shot GPT-4
class ZeroShotGPT4Baseline:
    """
    Baseline 3: Single LLM call, no RAG, no multi-agent
    Provide patient profile + trial list, ask LLM to rank
    """

    def __init__(self):
        from openai import AsyncOpenAI
        from dotenv import load_dotenv
        import os

        load_dotenv()
        api_key = os.getenv("open_ai")
        if not api_key:
            raise ValueError("open_ai not found in .env")

        self.client = AsyncOpenAI(api_key=api_key)

        from tools.search_clinical_trials import search_clinical_trials
        self.search_tool = search_clinical_trials

    async def rank_trials(self, patient_profile: Dict[str, Any]) -> List[Dict]:
        """
        1. Search trials using API
        2. Send patient + trials to GPT-4
        3. Ask it to rank
        """
        search_terms = patient_profile.get('search_terms', [])

        # Collect all trials
        all_trials = []
        seen_nct_ids = set()

        for term in search_terms:
            results = await self.search_tool(term, max_results=15)  # Limit to avoid token overflow

            if results.get('success'):
                for trial in results.get('trials', []):
                    nct_id = trial.get('nct_id')
                    if nct_id and nct_id not in seen_nct_ids:
                        seen_nct_ids.add(nct_id)
                        all_trials.append(trial)

        if not all_trials:
            return []

        # Build prompt for GPT-4
        prompt = self._build_ranking_prompt(patient_profile, all_trials[:30])  # Limit to 30 trials

        # Call GPT-4
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a clinical trial matching expert. Rank trials by relevance to the patient."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2000
            )

            # Parse response
            ranked_trials = self._parse_ranking_response(response.choices[0].message.content, all_trials)
            return ranked_trials

        except Exception as e:
            print(f"Error in zero-shot GPT-4: {e}")
            return []

    def _build_ranking_prompt(self, profile: Dict, trials: List[Dict]) -> str:
        """Build prompt for GPT-4 ranking"""

        # Patient info
        patient_info = f"""
PATIENT PROFILE:
Age: {profile.get('demographics', {}).get('age', 'Unknown')}
Sex: {profile.get('demographics', {}).get('sex', 'Unknown')}
Diagnosis: {profile.get('diagnoses', 'Unknown')}
Biomarkers: {profile.get('biomarkers', 'None')}
Treatment Line: {profile.get('treatment_history', {}).get('treatment_line', 'Unknown')}
Prior Therapies: {profile.get('treatment_history', {}).get('prior_therapies', [])}
"""

        # Trial list
        trials_info = "\n\nAVAILABLE TRIALS:\n"
        for i, trial in enumerate(trials, 1):
            trials_info += f"\n{i}. NCT ID: {trial.get('nct_id', 'Unknown')}\n"
            trials_info += f"   Title: {trial.get('title', 'Unknown')[:200]}\n"
            trials_info += f"   Status: {trial.get('status', 'Unknown')}\n"

            if trial.get('brief_summary'):
                trials_info += f"   Summary: {trial['brief_summary'][:300]}...\n"

        # Ranking instruction
        instruction = """
TASK:
Rank these clinical trials by relevance to this patient. Consider:
1. Biomarker matching (most important)
2. Disease stage and histology
3. Treatment line appropriateness
4. Eligibility requirements

Return ONLY a JSON array of objects with this format:
[
  {"nct_id": "NCT12345678", "score": 0.95, "reason": "Perfect biomarker match"},
  {"nct_id": "NCT87654321", "score": 0.80, "reason": "Good disease match"},
  ...
]

Rank from highest to lowest relevance (top 10 trials only).
"""

        return patient_info + trials_info + instruction

    def _parse_ranking_response(self, response_text: str, all_trials: List[Dict]) -> List[Dict]:
        """Parse GPT-4 response to extract rankings"""

        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                print("Could not find JSON in response")
                return []

            rankings = json.loads(json_match.group(0))

            # Build ranked trial list
            ranked_trials = []
            for item in rankings:
                nct_id = item.get('nct_id')
                score = item.get('score', 0.5)

                # Find full trial info
                trial_info = next((t for t in all_trials if t.get('nct_id') == nct_id), None)

                if trial_info:
                    ranked_trials.append({
                        'nct_id': nct_id,
                        'title': trial_info.get('title', ''),
                        'status': trial_info.get('status', ''),
                        'score': float(score),
                        'method': 'zero_shot_gpt4',
                        'reason': item.get('reason', '')
                    })

            return ranked_trials

        except Exception as e:
            print(f"Error parsing GPT-4 response: {e}")
            return []


# Baseline 4: Your System (RAG + Multi-Agent)
class RAGEnhancedSystem:
    """
    Baseline 4: Your full system (Phase 1 + 2 + 3)
    This is the method we're trying to prove is better
    """

    async def rank_trials(self, patient_profile: Dict[str, Any]) -> List[Dict]:
        """
        Run full pipeline:
        1. Patient profiling (if needed)
        2. Trial discovery (API search + keyword ranking)
        3. Knowledge enhancement (RAG-based re-ranking)
        """
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode

        engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

        # Phase 2: Trial Discovery
        discovery_result = await engine.run_trial_discovery(patient_profile)

        if not discovery_result.get('success'):
            print(f"Trial discovery failed: {discovery_result.get('error')}")
            return []

        # Phase 3: Knowledge Enhancement
        enhancement_result = await engine.run_knowledge_enhancement(
            patient_profile,
            discovery_result['ranked_trials']
        )

        if not enhancement_result.get('success'):
            print(f"Knowledge enhancement failed: {enhancement_result.get('error')}")
            return discovery_result.get('ranked_trials', [])

        # Return final ranked trials
        final_trials = enhancement_result.get('ranked_trials', [])

        # Add method tag
        for trial in final_trials:
            trial['method'] = 'rag_enhanced'

        return final_trials


# Factory function
def get_baseline(method_name: str):
    """Get baseline method by name"""

    methods = {
        'keyword_search': KeywordSearchBaseline,
        'tfidf': TFIDFBaseline,
        'zero_shot_gpt4': ZeroShotGPT4Baseline,
        'rag_enhanced': RAGEnhancedSystem
    }

    if method_name not in methods:
        raise ValueError(f"Unknown method: {method_name}. Choose from: {list(methods.keys())}")

    return methods[method_name]()


# Test function
async def test_baseline(method_name: str, case_id: str = "cervical_pdl1_standard"):
    """Test a single baseline on a single case"""

    print(f"\n{'='*70}")
    print(f"TESTING: {method_name}")
    print(f"Case: {case_id}")
    print(f"{'='*70}")

    # Load patient profile
    profile_path = Path(__file__).parent / "sample_profiles" / f"{case_id}.json"
    with open(profile_path) as f:
        patient_profile = json.load(f)

    # Get baseline method
    baseline = get_baseline(method_name)

    # Rank trials
    ranked_trials = await baseline.rank_trials(patient_profile)

    # Show top 5
    print(f"\nTop 5 trials:")
    for i, trial in enumerate(ranked_trials[:5], 1):
        print(f"{i}. {trial.get('nct_id', 'Unknown')} (score: {trial.get('score', 0):.3f})")
        print(f"   {trial.get('title', 'No title')[:80]}...")

    print(f"\nTotal trials ranked: {len(ranked_trials)}")

    return ranked_trials


if __name__ == "__main__":
    # Test each baseline
    import sys

    if len(sys.argv) > 1:
        method = sys.argv[1]
        asyncio.run(test_baseline(method))
    else:
        print("Usage: python baselines.py <method>")
        print("Methods: keyword_search, tfidf, zero_shot_gpt4, rag_enhanced")
