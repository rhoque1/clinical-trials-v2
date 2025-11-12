"""
RAG Evaluation Framework

Comprehensive testing system for measuring and optimizing RAG effectiveness
in clinical trial matching.

Quick Start:
    >>> from evaluation.rag_evaluator import RAGEvaluator
    >>> evaluator = RAGEvaluator()
    >>> await evaluator.run_experiment("knowledge_ablation")

See evaluation/QUICK_START.md for detailed instructions.
"""

from evaluation.rag_evaluator import RAGEvaluator
from evaluation.rag_configurations import (
    RAGConfiguration,
    get_all_configs,
    get_experiment_configs,
    CONFIG_CONTROL,
    CONFIG_GUIDELINES_ONLY,
    CONFIG_GUIDELINES_FDA,
    CONFIG_CURRENT_SYSTEM,
    CONFIG_NO_TRIAL_CORPUS
)
from evaluation.analyze_results import ResultsAnalyzer

__version__ = "1.0.0"
__all__ = [
    "RAGEvaluator",
    "ResultsAnalyzer",
    "RAGConfiguration",
    "get_all_configs",
    "get_experiment_configs"
]
