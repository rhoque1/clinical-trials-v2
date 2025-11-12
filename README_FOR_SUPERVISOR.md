# Clinical Trial Matching System - Supervisor Demo Guide

## Quick Start: Testing RAG vs General Search

### Run the Demo

```bash
python DEMO_FOR_SUPERVISOR.py
```

**What it does:**
- Runs the SAME patient case through both methods
- Shows results side-by-side
- Highlights differences in rankings
- Takes ~5-10 minutes

---

## System Architecture

### Method 1: General Search (Baseline)
**File:** Phase 2 of `agents/workflow_engine.py` → `run_trial_discovery()`

**How it works:**
1. Search ClinicalTrials.gov API with keywords
2. Deduplicate and filter active trials
3. Rank trials using LLM-based relevance scoring
4. Return top matches

**Limitations:**
- No clinical knowledge integration
- Relies only on trial descriptions
- May miss nuanced biomarker requirements

---

### Method 2: RAG-Enhanced Search (Your Full System)
**Files:**
- Phase 2: `agents/workflow_engine.py` → `run_trial_discovery()` (same as above)
- Phase 3: `agents/workflow_engine.py` → `run_knowledge_enhancement()`
- RAG Logic: `state_machines/knowledge_enhanced_ranking.py`
- Knowledge Base: `tools/clinical_rag.py`

**How it works:**
1. **Start with general search** (Phase 2 - same as Method 1)
2. **Retrieve relevant clinical knowledge** (Phase 3):
   - Query vectorstore for NCCN guidelines
   - Query vectorstore for FDA drug labels
   - Query vectorstore for biomarker information
3. **Re-rank trials** using retrieved knowledge
4. **Return knowledge-enhanced matches**

**Knowledge Base Contents:**
- **NCCN Guidelines:** 44MB of treatment recommendations
- **FDA Drug Labels:** 20MB of approved drug information
- **Biomarker Guides:** 8KB of biomarker-drug associations
- **Total Vectorstore:** 22MB indexed

**Advantages:**
- Clinically informed rankings
- Better biomarker matching
- Considers treatment guidelines
- More interpretable (can trace back to knowledge sources)

---

## File Guide

### To Test Yourself:

| Purpose | File | Command |
|---------|------|---------|
| **Side-by-side demo** | `DEMO_FOR_SUPERVISOR.py` | `python DEMO_FOR_SUPERVISOR.py` |
| **Full evaluation (20 cases)** | `run_phase1_ablation_fixed.py` | `python run_phase1_ablation_fixed.py` |
| **Quick validation (5 cases)** | `test_curated_ground_truth.py` | `python test_curated_ground_truth.py` |

### System Components:

| Component | File | Description |
|-----------|------|-------------|
| **Workflow Orchestrator** | `agents/workflow_engine.py` | Main pipeline (Phase 1-3) |
| **Trial Discovery** | `state_machines/trial_discovery.py` | General search logic |
| **RAG Enhancement** | `state_machines/knowledge_enhanced_ranking.py` | RAG re-ranking logic |
| **Knowledge Base** | `tools/clinical_rag.py` | RAG retrieval system |
| **Vectorstore** | `vectorstore/clinical_guidelines.faiss` | Indexed knowledge (22MB) |

---

## Research Progress Summary

### Completed:
1. ✅ **System Architecture** - Multi-agent pipeline with 3 phases
2. ✅ **Knowledge Base** - NCCN guidelines + FDA labels (22MB vectorstore)
3. ✅ **Evaluation Framework** - 20 test cases with curated ground truth
4. ✅ **Bug Fixes** - Unicode encoding, ground truth compatibility
5. ✅ **Diagnostic Tools** - Automated ground truth validation

### Current Status:
- **Ready for Phase 1 Experiment**: RAG vs No-RAG comparison on 20 test cases
- **Expected Timeline**: 8 weeks to submission-ready paper (per RESEARCH_STRATEGY.md)

### Next Steps (from RESEARCH_STRATEGY.md):
1. **Week 1-2**: Run Phase 1 experiment, compute Precision@3, MRR
2. **Week 3-4**: Targeted knowledge base improvements based on failure modes
3. **Week 5-6**: Ablation studies, statistical testing
4. **Week 7-8**: Paper writing, visualization

---

## Understanding the Output

### Demo Output Example:

```
COMPARISON: General Search vs RAG-Enhanced
==================================================
Rank   General Search       RAG-Enhanced         Change
--------------------------------------------------
1      NCT12345678          NCT12345678          =
2      NCT87654321          NCT99999999          ↑ 5
3      NCT99999999          NCT87654321          ↓ 1
...
```

**Interpretation:**
- `=` No change
- `↑ N` RAG moved trial UP by N positions (more relevant with knowledge)
- `↓ N` RAG moved trial DOWN by N positions (less relevant with knowledge)
- `OUT` Trial dropped out of top 10

### Metrics You'll See:

- **Precision@3**: % of top 3 trials that are ground truth (clinically appropriate)
- **Precision@5**: % of top 5 trials that are ground truth
- **MRR (Mean Reciprocal Rank)**: Average of 1/rank for first ground truth hit
- **Hit Rate**: % of cases where ground truth appears in top K

---

## Key Research Questions (from RESEARCH_STRATEGY.md)

**RQ1**: Does RAG-based knowledge enhancement improve trial ranking accuracy?
- **Test**: Compare Method 1 (General) vs Method 2 (RAG)
- **Hypothesis**: RAG improves Precision@3 by 15-25%

**RQ2**: Which knowledge sources contribute most to accuracy?
- **Test**: Ablation study (Guidelines only, FDA only, Both, Neither)
- **Hypothesis**: Guidelines + FDA > either alone

**RQ3**: Does multi-stage pipeline outperform single-pass retrieval?
- **Test**: Two-stage (API + RAG) vs End-to-end retrieval
- **Hypothesis**: Two-stage balances recall/precision

---

## Troubleshooting

### If demo fails:

1. **Check vectorstore exists:**
   ```bash
   dir vectorstore\clinical_guidelines.faiss
   ```
   If missing, rebuild:
   ```bash
   python tools\clinical_rag.py
   ```

2. **Check environment variables:**
   - Ensure `.env` has valid `OPENAI_API_KEY`

3. **Check test data:**
   ```bash
   dir evaluation\sample_profiles
   ```
   Should have 20 JSON files

4. **Unicode errors (Windows):**
   - Already fixed via `fix_encoding_global.py`
   - Auto-imported in all scripts

---

## Questions?

- **System Architecture**: See `agents/workflow_engine.py:run_workflow()`
- **RAG Logic**: See `state_machines/knowledge_enhanced_ranking.py`
- **Research Plan**: See `RESEARCH_STRATEGY.md` (full 8-week plan)
- **Evaluation Results**: See `evaluation/results/` directory

---

## Summary for Supervisor

**Bottom Line:**
- **General Search**: Uses keyword matching + LLM scoring (Phase 2 only)
- **RAG-Enhanced**: Adds clinical knowledge retrieval + re-ranking (Phase 2 + 3)
- **Demo File**: `DEMO_FOR_SUPERVISOR.py` - run this to see the difference
- **Expected Result**: RAG should re-prioritize trials based on clinical guidelines

The demo will show you exactly how RAG changes the rankings by incorporating NCCN guidelines and FDA drug information.
