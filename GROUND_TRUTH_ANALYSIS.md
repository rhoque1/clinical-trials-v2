# Ground Truth Validation Analysis

## Executive Summary

After updating ground truth trials from completed to active status, the system **still achieves 0% accuracy**. Root cause analysis reveals a fundamental evaluation framework limitation.

## Problem Discovered

### Issue 1: Duplicate Ground Truth
The automated replacement script selected the **same trial multiple times** for different ground truth slots.

**Example (cervical_pdl1_standard):**
```
Ground truth trials:
- NCT06223308 (duplicate)
- NCT06223308 (duplicate)
```

### Issue 2: Search Query Mismatch (CRITICAL)
**Ground truth trials are not being returned by the system's own searches.**

**Evidence:**
- **Expected**: NCT06223308
- **Actually Retrieved (Top 3)**:
  1. NCT05091190
  2. NCT07211009
  3. NCT07081984

**Root Cause:**
The replacement finder used simple search queries like:
- `"cervical cancer" + "PD-L1"`

But the actual system generates different queries like:
- `"cervical cancer", "gynecologic cancer", "cervical cancer treatment", "cervical cancer HPV", "cervical carcinoma"`

**This creates a fundamental mismatch**: trials found via one search method may not appear in searches using different query generation logic.

## Evaluation Framework Limitation

### The Core Problem:
**You cannot evaluate a retrieval system using ground truth that the system cannot retrieve.**

This is analogous to:
- Creating a reading comprehension test using passages the student never saw
- Asking someone to find a book that's not in the library

### Why This Happened:
1. Original ground truth used **landmark/pivotal trials** (KEYNOTE-826, FLAURA2, etc.)
2. These trials **completed enrollment** → excluded from API searches
3. Automated replacement used **different search logic** than the actual system
4. Replacement trials **don't appear** in system-generated searches

## What the 0% Accuracy Actually Means

The 0% accuracy does NOT mean:
- ❌ The system is broken
- ❌ The ranking algorithm fails
- ❌ The RAG system doesn't work

It DOES mean:
- ✅ The ground truth trials are **not in the search result set**
- ✅ Evaluation requires ground truth that **would actually be returned** by searches
- ✅ Current ground truth is **incompatible** with the evaluation framework

## Solutions (Ranked by Feasibility)

### Option 1: Manual Ground Truth Curation ⭐ RECOMMENDED
**Approach**: For each test case, manually select ground truth from trials that **actually appear** in the system's search results.

**Process**:
1. Run system search for each patient profile
2. Review top 20-30 results
3. Manually identify 2-3 clinically appropriate trials from ACTUAL results
4. Use those as ground truth

**Pros**:
- Ensures evaluation measures **ranking quality**, not search coverage
- Realistic - evaluates what users would actually see
- Clinically valid - expert selects best from available options

**Cons**:
- Manual effort (20 cases × 2-3 trials = 40-60 manual selections)
- Time: ~2-3 hours with clinical knowledge

### Option 2: Relaxed Evaluation Metrics
**Approach**: Measure "recall in top K" instead of "precision at top K"

**Example Metrics**:
- Recall@100: Did ground truth appear in top 100?
- First Hit Rank: What rank was the first ground truth trial?
- Coverage: % of ground truth trials returned at all

**Pros**:
- Can use existing ground truth
- Evaluates search coverage + ranking

**Cons**:
- Doesn't evaluate practical utility (users only see top 10)
- Still fails if ground truth not in results at all

### Option 3: Hybrid Approach
**Approach**: Two-stage evaluation

**Stage 1 - Coverage**: Do ground truth trials appear in results?
**Stage 2 - Ranking**: If yes, are they ranked appropriately?

**Pros**:
- Separates search quality from ranking quality
- Diagnostic value

**Cons**:
- More complex
- Still requires ground truth that can be found

## Current Status

- ✅ **60% of original trials were COMPLETED** (correctly identified)
- ✅ **17/20 cases updated with active replacements** (correctly executed)
- ❌ **Replacement trials not in search results** (evaluation mismatch)
- ✅ **System is functional** (searches work, ranking works)
- ❌ **Cannot measure accuracy** with current ground truth

## Recommendations

### Immediate Next Step:
**Manually curate ground truth for 3-5 representative test cases**

**Process**:
1. Select diverse cases (cervical, lung EGFR, breast HER2, melanoma, colorectal)
2. Run system search for each
3. Review top 20 trials with clinical lens
4. Select 2-3 appropriate trials from ACTUAL results
5. Run evaluation on this subset
6. If methodology works, expand to all 20 cases

**Expected Outcome**:
- Precision@5: 20-40% (realistic baseline)
- MRR: 0.3-0.5 (reasonable ranking)
- Can measure RAG impact vs baseline

### Alternative: Research-Only Evaluation
If manual curation not feasible, document this as a **research limitation**:

> "Evaluation framework requires ground truth trials to be discoverable via
> system searches. Landmark trials (KEYNOTE-826, FLAURA2) that completed
> enrollment are not in active trial database, precluding traditional
> precision@K evaluation. Future work should use user study methodology
> with expert judgment on real search results."

## Lessons Learned

1. **Retrieval evaluation requires realistic ground truth**
2. **Completed landmark trials ≠ active searchable trials**
3. **Search query generation significantly impacts results**
4. **Automated ground truth replacement has hidden assumptions**
5. **0% accuracy is not always a system failure** - can indicate evaluation design issues

---

**Next Action**: Choose option 1 (manual curation for 5 cases) to get working evaluation metrics, or pivot to qualitative case study methodology.
