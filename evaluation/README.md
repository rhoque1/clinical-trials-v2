# RAG Evaluation Framework

Comprehensive testing system to measure which RAG configurations improve trial matching accuracy.

## Overview

This framework enables rigorous A/B testing of different RAG configurations to determine:
- Which knowledge sources are most valuable
- Optimal retrieval parameters (chunk size, k value)
- Best query construction strategies
- Overall impact of RAG on accuracy

## Directory Structure

```
evaluation/
├── test_cases.json              # Ground truth test cases with expert-labeled trials
├── rag_configurations.py        # Different RAG configs to test
├── rag_evaluator.py            # Automated evaluation runner
├── analyze_results.py          # Statistical analysis and recommendations
├── README.md                   # This file
└── results/                    # Generated experiment results
    ├── experiment_*.json       # Full experiment results
    ├── *_YYYYMMDD_*.json      # Individual config results
    └── analysis_report.txt     # Analysis summary
```

## Quick Start

### 1. Run Knowledge Ablation Experiment

Tests which knowledge sources actually improve accuracy:

```bash
cd C:\Users\hoque\github\clinical-trials-v2
python -m evaluation.rag_evaluator
```

This will test:
- ❌ **Control** (No RAG baseline)
- 📘 **Guidelines Only** (NCCN + ASCO)
- 📘💊 **Guidelines + FDA** (+ drug labels)
- 📘💊🧬 **Guidelines + FDA + Biomarker Guides**
- 📘💊🧬📊 **Current System** (+ 2000 trial corpus)
- 📊 **Trial Corpus Only**

### 2. Analyze Results

```bash
python -m evaluation.analyze_results
```

Generates:
- Comparison table of all configs
- Statistical significance tests
- Actionable recommendations
- Identification of best configuration

### 3. View Results

Results saved to `evaluation/results/`:
- `experiment_knowledge_ablation_*.json` - Full experiment data
- `analysis_report.txt` - Summary with recommendations

## Test Cases

Ground truth test cases represent real clinical scenarios with expert-labeled trials that SHOULD rank highly:

### Current Test Cases

1. **cervical_pdl1_standard** - Stage IIIB cervical cancer, PD-L1+ (CPS 50%)
   - Ground truth: KEYNOTE-826 (pembrolizumab), atezolizumab trials
   - NCCN Category 1 recommendation

2. **lung_egfr_exon19** - Metastatic NSCLC, EGFR exon 19 deletion
   - Ground truth: FLAURA2 (osimertinib), MARIPOSA trials
   - First-line EGFR TKI

3. **breast_her2_brca** - HER2+ breast cancer, BRCA1+, post-trastuzumab
   - Ground truth: T-DXd, tucatinib trials
   - Second-line HER2 therapy

4. **colorectal_msi_high** - Stage IV CRC, MSI-H/dMMR, BRAF V600E
   - Ground truth: KEYNOTE-177 (pembrolizumab), nivolumab+ipilimumab
   - First-line immunotherapy

5. **melanoma_braf_v600e** - Unresectable stage III, BRAF V600E
   - Ground truth: COMBI-d/v (dabrafenib+trametinib), COLUMBUS trials
   - BRAF/MEK inhibitor

### Adding New Test Cases

Edit `evaluation/test_cases.json`:

```json
{
  "case_id": "new_case_id",
  "patient_summary": "Clinical description",
  "ground_truth_trials": [
    {
      "nct_id": "NCT12345678",
      "trial_name": "Trial name",
      "rationale": "Why this trial should rank high",
      "expected_rank": "top3",
      "confidence": "very_high"
    }
  ],
  "key_biomarkers": ["MARKER1", "MARKER2"],
  "treatment_line": "first_line",
  "nccn_recommendation": "NCCN guideline text"
}
```

## RAG Configurations

Defined in `rag_configurations.py`:

### Experiment 1: Knowledge Source Ablation

Tests which sources matter:
- `CONFIG_CONTROL` - No RAG
- `CONFIG_GUIDELINES_ONLY` - NCCN/ASCO guidelines
- `CONFIG_GUIDELINES_FDA` - Guidelines + FDA labels
- `CONFIG_NO_TRIAL_CORPUS` - All except trial corpus
- `CONFIG_CURRENT_SYSTEM` - Everything including corpus
- `CONFIG_TRIAL_CORPUS_ONLY` - Only the trial corpus

### Experiment 2: Retrieval Parameters

Tests chunk size and k:
- `CONFIG_SMALL_CHUNKS` - 500 char chunks, k=5
- `CONFIG_LARGE_CHUNKS` - 2000 char chunks, k=3
- `CONFIG_HIGH_K` - k=10 retrieval

### Experiment 3: Query Construction

Tests query formulations:
- `CONFIG_DETAILED_QUERY` - Full context (stage, histology, line)
- `CONFIG_SIMPLE_QUERY` - Minimal (cancer type + main biomarker)

### Adding New Configurations

```python
CONFIG_MY_TEST = RAGConfiguration(
    config_id="my_test",
    name="My Test Config",
    description="What I'm testing",
    include_guidelines=True,
    include_drug_labels=True,
    include_trial_corpus=False,
    k_retrieval=5,
    chunk_size=1000,
    query_template="{diagnoses} {biomarkers} treatment"
)
```

## Evaluation Metrics

### Precision@K
Percentage of ground truth trials found in top K results
- **P@1**: Top 1 trial is correct?
- **P@3**: At least one ground truth in top 3?
- **P@5**: At least one ground truth in top 5?

**Target: ≥80% P@3 for "excellent" performance**

### Mean Reciprocal Rank (MRR)
Average of 1/rank for first correct trial
- Perfect score: 1.0 (correct trial ranked #1)
- Good score: ≥0.5 (correct trial in top 2 on average)

### NDCG@5
Normalized Discounted Cumulative Gain
- Measures ranking quality considering confidence levels
- Accounts for position (higher ranks = better)
- Perfect score: 1.0

### Statistical Significance
Paired t-tests between configurations
- p < 0.05: Statistically significant difference
- Cohen's d: Effect size (small/medium/large)

## Running Custom Experiments

### Quick Test (Single Config, Single Case)

```python
from evaluation.rag_evaluator import RAGEvaluator
from evaluation.rag_configurations import CONFIG_GUIDELINES_FDA
import asyncio

evaluator = RAGEvaluator()
result = asyncio.run(
    evaluator.quick_test(CONFIG_GUIDELINES_FDA, "cervical_pdl1_standard")
)
```

### Full Config Evaluation (All Test Cases)

```python
evaluator = RAGEvaluator()
result = asyncio.run(
    evaluator.evaluate_config(CONFIG_GUIDELINES_FDA)
)
```

### Run Specific Experiment

```python
evaluator = RAGEvaluator()
asyncio.run(
    evaluator.run_experiment("knowledge_ablation")
)
```

## Interpreting Results

### Sample Output

```
CONFIGURATION COMPARISON
────────────────────────────────────────────────────────────────────
Config                          P@1    P@3    P@5    MRR    NDCG@5
────────────────────────────────────────────────────────────────────
Guidelines + FDA Labels         40%    85%    95%    0.625  0.812
Guidelines Only                 35%    80%    90%    0.588  0.771
Without Trial Corpus            38%    82%    92%    0.601  0.788
Current System (With Corpus)    32%    75%    88%    0.551  0.734
Trial Corpus Only               15%    45%    60%    0.321  0.512
No RAG (Control)                28%    68%    82%    0.492  0.681
────────────────────────────────────────────────────────────────────
```

### Key Insights

1. **Guidelines + FDA performs best** (85% P@3)
2. **Trial corpus DECREASES accuracy** (75% vs 82% without it)
3. **RAG helps significantly** (68% → 85% improvement over control)

### Recommendations

```
✅ KEEP RAG: Improves accuracy by 25% over baseline
✅ INCLUDE FDA LABELS: Adds 5% improvement over guidelines only
❌ REMOVE TRIAL CORPUS: Decreases accuracy by 7 percentage points
🏆 OPTIMAL CONFIG: Use 'guidelines_fda' (P@3 = 85%)
```

## Expected Timeline

- **Run Experiment 1** (Knowledge Ablation): ~30-45 minutes
  - 6 configs × 5 test cases × ~1-2 min per case
- **Analysis**: ~1 minute
- **Total**: ~1 hour for complete knowledge ablation study

## Troubleshooting

### "No experiments found"
```bash
# Run evaluator first
python -m evaluation.rag_evaluator
```

### "Test case not found"
Check `evaluation/test_cases.json` exists and has valid cases

### "API timeout"
Increase timeout in workflow_engine or reduce concurrent calls

### "Vectorstore build failed"
Check that knowledge_base/ directories exist with content

## Next Steps After Initial Results

1. **If trial corpus helps**: Keep it, investigate why
2. **If trial corpus hurts**: Remove it, rebuild without it
3. **If FDA labels don't help**: Remove to reduce noise
4. **If RAG doesn't help at all**: Investigate query construction or use keyword baseline

## Future Enhancements

### Planned Additions

1. **Published trial results corpus**
   - NEJM, JCO, Lancet trial outcome papers
   - Add to `knowledge_base/published_results/`

2. **Biomarker actionability databases**
   - OncoKB, CIViC, PMKB exports
   - Add to `knowledge_base/actionability/`

3. **Re-ranking models**
   - Cross-encoder re-rankers
   - `CONFIG_WITH_RERANKING`

4. **Multi-modal retrieval**
   - Dense + sparse hybrid search
   - BM25 + vector similarity

## Contact / Questions

See main project README or workflow_engine documentation.
