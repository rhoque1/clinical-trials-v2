"""
RAG Configuration Variants for A/B Testing

This module defines different RAG configurations to test which
knowledge sources and retrieval strategies work best.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class RAGConfiguration:
    """Configuration for a RAG variant"""
    config_id: str
    name: str
    description: str

    # Knowledge sources (directories to include)
    include_guidelines: bool = True
    include_drug_labels: bool = True
    include_biomarker_guides: bool = True
    include_trial_corpus: bool = False
    include_published_results: bool = False
    include_actionability_db: bool = False

    # Retrieval parameters
    k_retrieval: int = 3  # Number of chunks to retrieve
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Query construction
    query_template: str = "{diagnoses} {biomarkers} treatment guidelines"

    # Re-ranking
    enable_reranking: bool = False
    reranking_model: str = None


# ============================================================================
# EXPERIMENT 1: Knowledge Source Ablation
# Test which sources actually contribute to accuracy
# ============================================================================

CONFIG_CONTROL = RAGConfiguration(
    config_id="control",
    name="No RAG (Control)",
    description="Baseline - no knowledge enhancement, just keyword ranking",
    include_guidelines=False,
    include_drug_labels=False,
    include_biomarker_guides=False,
    include_trial_corpus=False,
    include_published_results=False,
    include_actionability_db=False
)

CONFIG_GUIDELINES_ONLY = RAGConfiguration(
    config_id="guidelines_only",
    name="Guidelines Only",
    description="NCCN + ASCO guidelines only",
    include_guidelines=True,
    include_drug_labels=False,
    include_biomarker_guides=False,
    include_trial_corpus=False,
    k_retrieval=3
)

CONFIG_GUIDELINES_FDA = RAGConfiguration(
    config_id="guidelines_fda",
    name="Guidelines + FDA Labels",
    description="NCCN/ASCO guidelines + FDA drug labels",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=False,
    include_trial_corpus=False,
    k_retrieval=5
)

CONFIG_CURRENT_SYSTEM = RAGConfiguration(
    config_id="current_system",
    name="Current System (All Sources)",
    description="Current setup: Guidelines + FDA + Biomarker guides + Trial corpus",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=True,
    k_retrieval=3
)

CONFIG_NO_TRIAL_CORPUS = RAGConfiguration(
    config_id="no_trial_corpus",
    name="Without Trial Corpus",
    description="Guidelines + FDA + Biomarker guides, but NO trial corpus",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    k_retrieval=5
)

CONFIG_TRIAL_CORPUS_ONLY = RAGConfiguration(
    config_id="trial_corpus_only",
    name="Trial Corpus Only",
    description="Only the 2000-trial corpus (test if it helps at all)",
    include_guidelines=False,
    include_drug_labels=False,
    include_biomarker_guides=False,
    include_trial_corpus=True,
    k_retrieval=5
)

# ============================================================================
# EXPERIMENT 2: Retrieval Parameters
# Test optimal chunk size and retrieval count
# ============================================================================

CONFIG_SMALL_CHUNKS = RAGConfiguration(
    config_id="small_chunks",
    name="Small Chunks (500 chars)",
    description="Smaller chunks, more granular retrieval",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    chunk_size=500,
    chunk_overlap=100,
    k_retrieval=5
)

CONFIG_LARGE_CHUNKS = RAGConfiguration(
    config_id="large_chunks",
    name="Large Chunks (2000 chars)",
    description="Larger chunks, more context per retrieval",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    chunk_size=2000,
    chunk_overlap=400,
    k_retrieval=3
)

CONFIG_HIGH_K = RAGConfiguration(
    config_id="high_k",
    name="High K Retrieval (k=10)",
    description="Retrieve more chunks for broader context",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    k_retrieval=10
)

# ============================================================================
# EXPERIMENT 3: Query Construction
# Test different query formulations
# ============================================================================

CONFIG_DETAILED_QUERY = RAGConfiguration(
    config_id="detailed_query",
    name="Detailed Query",
    description="More detailed query with stage, histology, treatment line",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    query_template="{diagnoses} {stage} {histology} {biomarkers} {treatment_line} treatment guidelines outcomes",
    k_retrieval=5
)

CONFIG_SIMPLE_QUERY = RAGConfiguration(
    config_id="simple_query",
    name="Simple Query",
    description="Minimal query - just cancer type and main biomarker",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    query_template="{cancer_type} {primary_biomarker} treatment",
    k_retrieval=5
)

# ============================================================================
# EXPERIMENT 4: Future Configurations (when we add new sources)
# ============================================================================

CONFIG_WITH_PUBLISHED_RESULTS = RAGConfiguration(
    config_id="with_published_results",
    name="With Published Trial Results",
    description="Guidelines + FDA + Published trial outcomes from NEJM/JCO/Lancet",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    include_published_results=True,
    k_retrieval=7
)

CONFIG_WITH_ACTIONABILITY = RAGConfiguration(
    config_id="with_actionability",
    name="With Actionability Database",
    description="Guidelines + FDA + OncoKB/CIViC actionability data",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    include_actionability_db=True,
    k_retrieval=7
)

CONFIG_OPTIMAL_HYPOTHESIS = RAGConfiguration(
    config_id="optimal_hypothesis",
    name="Optimal (Hypothesis)",
    description="Best hypothesized config: Guidelines + FDA + Published results + Actionability, no trial corpus",
    include_guidelines=True,
    include_drug_labels=True,
    include_biomarker_guides=True,
    include_trial_corpus=False,
    include_published_results=True,
    include_actionability_db=True,
    k_retrieval=7,
    query_template="{diagnoses} {stage} {biomarkers} {treatment_line} treatment guidelines outcomes"
)


# ============================================================================
# Experiment Definitions
# ============================================================================

EXPERIMENT_1_KNOWLEDGE_ABLATION = {
    "name": "Knowledge Source Ablation Study",
    "description": "Test which knowledge sources contribute to accuracy",
    "hypothesis": "Guidelines + FDA are sufficient; trial corpus adds noise",
    "configs": [
        CONFIG_CONTROL,
        CONFIG_GUIDELINES_ONLY,
        CONFIG_GUIDELINES_FDA,
        CONFIG_NO_TRIAL_CORPUS,
        CONFIG_CURRENT_SYSTEM,
        CONFIG_TRIAL_CORPUS_ONLY
    ],
    "primary_metric": "Precision@3",
    "expected_winner": "guidelines_fda or no_trial_corpus"
}

EXPERIMENT_2_RETRIEVAL_PARAMS = {
    "name": "Retrieval Parameter Optimization",
    "description": "Test chunk size and k values",
    "hypothesis": "Larger chunks (more context) with k=5-7 works best",
    "configs": [
        CONFIG_GUIDELINES_FDA,  # baseline
        CONFIG_SMALL_CHUNKS,
        CONFIG_LARGE_CHUNKS,
        CONFIG_HIGH_K
    ],
    "primary_metric": "NDCG@5",
    "expected_winner": "large_chunks or high_k"
}

EXPERIMENT_3_QUERY_CONSTRUCTION = {
    "name": "Query Formulation Study",
    "description": "Test different query construction strategies",
    "hypothesis": "Detailed queries with stage/line improve precision",
    "configs": [
        CONFIG_GUIDELINES_FDA,  # baseline (current template)
        CONFIG_DETAILED_QUERY,
        CONFIG_SIMPLE_QUERY
    ],
    "primary_metric": "MRR",
    "expected_winner": "detailed_query"
}


def get_all_configs() -> List[RAGConfiguration]:
    """Get all defined configurations"""
    return [
        CONFIG_CONTROL,
        CONFIG_GUIDELINES_ONLY,
        CONFIG_GUIDELINES_FDA,
        CONFIG_CURRENT_SYSTEM,
        CONFIG_NO_TRIAL_CORPUS,
        CONFIG_TRIAL_CORPUS_ONLY,
        CONFIG_SMALL_CHUNKS,
        CONFIG_LARGE_CHUNKS,
        CONFIG_HIGH_K,
        CONFIG_DETAILED_QUERY,
        CONFIG_SIMPLE_QUERY,
        CONFIG_WITH_PUBLISHED_RESULTS,
        CONFIG_WITH_ACTIONABILITY,
        CONFIG_OPTIMAL_HYPOTHESIS
    ]


def get_experiment_configs(experiment_name: str) -> List[RAGConfiguration]:
    """Get configurations for a specific experiment"""
    experiments = {
        "knowledge_ablation": EXPERIMENT_1_KNOWLEDGE_ABLATION,
        "retrieval_params": EXPERIMENT_2_RETRIEVAL_PARAMS,
        "query_construction": EXPERIMENT_3_QUERY_CONSTRUCTION
    }

    if experiment_name not in experiments:
        raise ValueError(f"Unknown experiment: {experiment_name}")

    return experiments[experiment_name]["configs"]
