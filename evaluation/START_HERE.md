# RAG Evaluation - START HERE

## Your Situation

You have a RAG system with multiple knowledge sources (NCCN guidelines, FDA labels, 8.8MB trial corpus). You want to know:

**"What actually helps? What adds noise? Should I keep the trial corpus?"**

---

## What I Built

A testing framework that runs your system with/without RAG on 5 test cases and measures if RAG improves accuracy.

**Objective measurement. No bias. Just data.**

---

## Quick Start (45 minutes)

### 1. Create Test Data (already done)
```bash
cd C:\Users\hoque\github\clinical-trials-v2
python evaluation/create_sample_data.py
```

**Output:** 5 patient profiles in `evaluation/sample_profiles/`

---

### 2. Run Experiment
```bash
python evaluation/simple_evaluator.py
```

**What this does:**
- Tests 5 patient cases
- Runs each case WITHOUT RAG (control)
- Runs each case WITH RAG (current system)
- Compares results

**Time:** 30-45 minutes

**What you'll see:**
```
Testing: Control (No RAG)
Case: cervical_pdl1_standard
[RESULTS]
  Precision@3: 66.7%
  First hit rank: 2

Testing: With RAG
Case: cervical_pdl1_standard
[RESULTS]
  Precision@3: 100.0%
  First hit rank: 1
```

---

### 3. Get Results

**At the end:**
```
FINAL COMPARISON
Metric          Control    With RAG    Change
Precision@3     66.7%      80.0%       +20.0%

CONCLUSION:
[POSITIVE] RAG improves accuracy by 20.0%
[RECOMMENDATION] KEEP RAG in production
```

**OR:**

```
CONCLUSION:
[NEGATIVE] RAG decreases accuracy by -10.0%
[RECOMMENDATION] DISABLE RAG - use keyword ranking only
```

---

## What Gets Measured

### Precision@3 (Primary Metric)
**"Is the correct trial in the top 3 results?"**

**Example:**
- Ground truth: NCT04649151 (KEYNOTE-826 for PD-L1+ cervical cancer)
- Your system ranks it #2 → ✅ Precision@3 = 100% (found in top 3)
- Your system ranks it #7 → ❌ Precision@3 = 0% (not in top 3)

**Target:** ≥80% for excellent performance

### Mean Reciprocal Rank (MRR)
**"What's the average rank of correct trials?"**
- Always ranked #1 → MRR = 1.0 (perfect)
- Always ranked #2 → MRR = 0.5
- Always ranked #5 → MRR = 0.2

**Target:** ≥0.6

---

## The Test Cases

5 realistic clinical scenarios with expert-labeled ground truth:

1. **Cervical cancer, PD-L1+ (CPS 50%)** → Should find KEYNOTE-826 (pembrolizumab)
2. **Lung NSCLC, EGFR exon 19 deletion** → Should find FLAURA2 (osimertinib)
3. **Breast cancer, HER2+, BRCA1+** → Should find T-DXd trials
4. **Colorectal, MSI-H, BRAF V600E** → Should find KEYNOTE-177
5. **Melanoma, BRAF V600E** → Should find COMBI-d/v (dabrafenib+trametinib)

**These are FDA-approved, guideline-recommended trials. They MUST rank highly.**

---

## Possible Outcomes

### Outcome 1: RAG Helps (+10% or more) ✅
```
Control: 68% P@3
With RAG: 85% P@3
Improvement: +25%

ACTION: Keep RAG. Your knowledge base is valuable.
```

### Outcome 2: RAG Hurts (-5% or more) ❌
```
Control: 75% P@3
With RAG: 68% P@3
Decline: -10%

ACTION: Disable RAG. It's adding noise, not signal.
```

### Outcome 3: RAG Neutral (±5%) ⚠️
```
Control: 72% P@3
With RAG: 74% P@3
Change: +3%

ACTION: Consider disabling to reduce complexity.
```

---

## What This Tells You

### If RAG helps:
- ✅ Your knowledge sources are high quality
- ✅ Guidelines provide valuable context
- ✅ Keep investing in RAG optimization

### If RAG hurts:
- ❌ Knowledge sources may be redundant (trial corpus?)
- ❌ Retrieval is pulling irrelevant chunks
- ❌ Simpler keyword ranking works better

### Either way:
- You'll have **objective data** to make decisions
- No more guessing about what helps
- Clear path forward

---

## After the Experiment

### If RAG is effective:
1. Run Phase 2: Test individual sources (guidelines vs FDA vs corpus)
2. Optimize parameters (chunk size, k value)
3. Add high-value sources (published trial results, actionability DB)

### If RAG isn't effective:
1. Disable RAG in production
2. Improve keyword ranking
3. Add biomarker-specific search queries

---

## Files Created

```
evaluation/
├── START_HERE.md              ← You are here
├── test_cases.json            # 5 ground truth test cases
├── simple_evaluator.py        # Simple RAG on/off test
├── sample_profiles/           # Generated patient data
│   ├── cervical_pdl1_standard.json
│   ├── lung_egfr_exon19.json
│   └── ... (5 files)
└── results/                   # Generated after run
    └── simple_experiment_*.json

RUN_EXPERIMENT.md              ← Detailed instructions
```

---

## Ready to Run?

```bash
cd C:\Users\hoque\github\clinical-trials-v2
python evaluation/simple_evaluator.py
```

**Expected time:** 30-45 minutes
**Expected output:** Clear recommendation with data
**Next steps:** Based on results

---

## Need Help?

### Common Issues

**"No module named 'evaluation'"**
→ Run from project root: `cd C:\Users\hoque\github\clinical-trials-v2`

**"Vectorstore not found"**
→ Build it first: `python tools/clinical_rag.py` or run workflow once

**"API timeout"**
→ Normal for some cases, experiment will continue

**"Takes too long"**
→ Expected 3-5 min per case × 5 cases × 2 conditions = 30-45 min total

---

## Key Points

1. **Objective:** No bias. Just measuring if RAG helps or hurts.
2. **Controlled:** Same test cases, same trials, only RAG on/off changes.
3. **Clear:** You get a definitive recommendation at the end.
4. **Fast:** 45 minutes to answer your key question.

---

## What You'll Learn

After this experiment, you'll definitively know:

✅ Does RAG improve accuracy? (Yes/No)
✅ By how much? (+20%? -10%?)
✅ Should you keep it? (Clear recommendation)
✅ What to do next? (Next steps based on results)

**No more uncertainty. Just data-driven decisions.**

---

## Go!

```bash
python evaluation/simple_evaluator.py
```

See you in 45 minutes with results. 🚀
