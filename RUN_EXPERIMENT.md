# Run RAG Effectiveness Experiment

## What This Tests

**Question:** Does your RAG system actually improve trial matching accuracy?

**Method:** Compare two conditions:
- **Control:** No RAG (just keyword ranking)
- **Treatment:** Current RAG system (with all knowledge sources)

**Measures:** Precision@3, Precision@5, MRR (Mean Reciprocal Rank)

---

## Prerequisites

1. ✅ You have run the system at least once successfully
2. ✅ Your vectorstore is built (`vectorstore/clinical_guidelines.faiss` exists)
3. ✅ You have valid `.env` with `open_ai` API key
4. ✅ Sample test data exists (`evaluation/sample_profiles/` has 5 JSON files)

---

## Step 1: Verify Setup

```bash
# Check sample profiles exist
ls evaluation/sample_profiles/

# Should see:
# cervical_pdl1_standard.json
# lung_egfr_exon19.json
# breast_her2_brca.json
# colorectal_msi_high.json
# melanoma_braf_v600e.json
```

If not, run:
```bash
python evaluation/create_sample_data.py
```

---

## Step 2: Run the Experiment

```bash
python evaluation/simple_evaluator.py
```

**Time:** ~30-45 minutes (5 test cases × 2 conditions × ~3-5 min each)

---

## What Happens During the Run

For each test case, the system will:

1. **Load patient profile** (from evaluation/sample_profiles/)
2. **Run trial discovery** (Phase 2: search ClinicalTrials.gov)
3. **Run knowledge enhancement** (Phase 2.5: RAG or skip if control)
4. **Calculate metrics** (is ground truth trial in top 3?)
5. **Display results**

You'll see output like:
```
==================================================
Testing: Control (No RAG)
Case: cervical_pdl1_standard
==================================================

Running trial discovery...
Running knowledge enhancement (RAG=disabled)...

[RESULTS]
  Precision@3: 66.7%
  MRR: 0.500
  First hit rank: 2
  Top 5 trials:
    1. NCT99999999 (score: 85)
    2. NCT04649151 (score: 82) [GROUND TRUTH]
    3. NCT88888888 (score: 78)
```

---

## Step 3: Review Results

After completion, you'll see:

```
==================================================
FINAL COMPARISON
==================================================

Metric               Control         With RAG        Change
----------------------------------------------------------------------
Precision@3          66.7%           80.0%           +20.0%
MRR                  0.550           0.650           +18.2%

==================================================
CONCLUSION
==================================================
[POSITIVE] RAG improves accuracy by 20.0%
[RECOMMENDATION] KEEP RAG in production
```

**Results file:** `evaluation/results/simple_experiment_YYYYMMDD_HHMMSS.json`

---

## Interpreting Results

### If RAG Helps (+10% or more)
✅ **RAG is effective**
- Keep RAG enabled in production
- Your knowledge base is providing valuable context
- Consider adding more high-quality sources

### If RAG Hurts (-5% or more)
❌ **RAG is adding noise**
- Disable RAG (set DISABLE_RAG_FOR_EXPERIMENT = True permanently)
- Fall back to keyword ranking
- Your knowledge sources may be low quality or redundant

### If RAG is Neutral (±5%)
⚠️ **RAG has minimal impact**
- Consider disabling to reduce complexity
- Or investigate why it's not helping:
  - Are queries well-constructed?
  - Is retrieval finding relevant chunks?
  - Are knowledge sources appropriate?

---

## Troubleshooting

### Error: "ModuleNotFoundError: agents"
```bash
# Make sure you're in the project root
cd C:\Users\hoque\github\clinical-trials-v2
python evaluation/simple_evaluator.py
```

### Error: "Vectorstore not found"
```bash
# Build vectorstore first
python tools/clinical_rag.py
```

### Error: "API timeout"
- Increase timeout in workflow_engine.py
- Or reduce number of test cases (edit simple_evaluator.py, use only first 2 cases)

### Experiment takes too long
- Expected: 30-45 minutes for 5 cases × 2 conditions
- If longer, check API rate limits or network

---

## What Gets Saved

### Results File
`evaluation/results/simple_experiment_YYYYMMDD_HHMMSS.json`

Contains:
- All test case results (metrics, top 5 trials)
- Per-case precision, MRR
- Success/failure status
- Timestamps

### Example result entry:
```json
{
  "config_name": "With RAG",
  "test_case_id": "cervical_pdl1_standard",
  "metrics": {
    "precision@1": 0.0,
    "precision@3": 1.0,
    "precision@5": 1.0,
    "mrr": 0.5,
    "first_hit_rank": 2
  },
  "top_5_trials": [
    {
      "rank": 1,
      "nct_id": "NCT99999999",
      "score": 85,
      "is_ground_truth": false
    },
    {
      "rank": 2,
      "nct_id": "NCT04649151",
      "score": 82,
      "is_ground_truth": true
    }
  ]
}
```

---

## Next Steps After Experiment

### If RAG is helpful:
1. ✅ Keep RAG enabled
2. Run Phase 2 experiment (test individual knowledge sources)
3. Optimize retrieval parameters (chunk size, k)
4. Add more high-quality sources (published results, actionability DB)

### If RAG is not helpful:
1. ❌ Disable RAG in production
2. Focus on improving keyword ranking
3. Add biomarker-specific search queries
4. Implement treatment line filtering

---

## Manual Verification (Optional)

Want to verify results manually? Pick one test case:

```bash
# Check what the ground truth is
cat evaluation/test_cases.json | grep -A 20 "cervical_pdl1_standard"

# Run the full workflow manually
python -c "
import asyncio
from agents.workflow_engine import WorkflowEngine
from agents.orchestrator import WorkflowMode

async def test():
    engine = WorkflowEngine(WorkflowMode.WIZARD)
    # Load profile
    import json
    with open('evaluation/sample_profiles/cervical_pdl1_standard.json') as f:
        profile = json.load(f)

    # Run discovery
    discovery = await engine.run_trial_discovery(profile)

    # Run RAG enhancement
    enhanced = await engine.run_knowledge_enhancement(profile, discovery['ranked_trials'])

    # Check top 3
    for i, trial in enumerate(enhanced['ranked_trials'][:3], 1):
        print(f'{i}. {trial[\"nct_id\"]}')

asyncio.run(test())
"
```

---

## Questions?

- **"How do I know if the difference is statistically significant?"**
  - For 5 test cases, a 20%+ difference is likely meaningful
  - For rigorous stats, need 10+ test cases (add more in test_cases.json)

- **"Can I test specific knowledge sources?"**
  - Yes, but need the full evaluator (evaluation/rag_evaluator.py)
  - That one requires modifying workflow_engine to accept configs
  - This simple version just tests RAG on/off

- **"What if results vary a lot between test cases?"**
  - That's expected - some cases may benefit more from RAG
  - Look at the aggregate (average) metrics
  - Also look at which specific cases improve/worsen

---

## Ready?

```bash
python evaluation/simple_evaluator.py
```

**Time:** 30-45 minutes
**Output:** Clear recommendation to keep or disable RAG
**File:** evaluation/results/simple_experiment_*.json

Good luck! 🚀
