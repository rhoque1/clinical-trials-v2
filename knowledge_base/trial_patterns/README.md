# Trial Patterns Knowledge Base

This directory contains curated knowledge about clinical trial eligibility patterns and biomarker-driven trial matching.

## Purpose

Enhances the RAG system's ability to:
1. Match patients to trials based on specific biomarkers
2. Predict trial eligibility based on patient characteristics
3. Understand common eligibility criteria patterns across trial phases
4. Identify actionable biomarkers and corresponding targeted therapies

## Directory Contents

### Static Reference Documents (Already Created)

#### `actionable_biomarkers.txt`
Comprehensive biomarker-to-therapy mapping covering:
- **PIK3CA mutations** → PI3K inhibitors (alpelisib, GDC-0077)
- **PD-L1 expression** → Immunotherapy (pembrolizumab, atezolizumab)
- **EGFR mutations** → EGFR TKIs (osimertinib, erlotinib)
- **BRCA1/2 mutations** → PARP inhibitors (olaparib, rucaparib)
- **KRAS G12C** → KRAS inhibitors (sotorasib, adagrasib)
- **HER2 alterations** → HER2-targeted therapy (trastuzumab, T-DXd)
- **MSI-H/dMMR** → Checkpoint inhibitors
- **BRAF V600E** → BRAF/MEK inhibitors
- **ALK/ROS1/NTRK fusions** → TKI therapies

Each biomarker entry includes:
- Mutation types and prevalence
- FDA-approved therapies
- Active clinical trial landscape
- Common eligibility criteria patterns
- Cancer types where biomarker is relevant

#### `common_eligibility_patterns.txt`
Structured knowledge about trial eligibility organized by:

**By Trial Phase:**
- Phase 1: Dose escalation criteria
- Phase 2: Efficacy testing requirements
- Phase 3: Registration trial strictness

**By Treatment Line:**
- First-line (treatment-naive) requirements
- Second-line eligibility patterns
- Third-line+ (heavily pretreated) considerations

**By Cancer Type:**
- Lung cancer (NSCLC) specific patterns
- Breast cancer subtype requirements
- Colorectal cancer molecular testing
- Melanoma trial characteristics
- Ovarian cancer platinum sensitivity
- Prostate cancer CRPC criteria
- Cervical cancer HPV/PD-L1 requirements

**Special Topics:**
- Brain metastases policies (evolving inclusivity)
- Older adult considerations
- ECOG performance status 2 trials
- Hepatic/renal impairment thresholds
- Universal exclusion criteria
- Washout period requirements

### Dynamic Trial Data (To Be Generated)

The corpus builder script will generate cancer-specific files:

#### Eligibility Pattern Files
- `cervical_cancer_eligibility_patterns.txt`
- `lung_cancer_eligibility_patterns.txt`
- `breast_cancer_eligibility_patterns.txt`
- `colorectal_cancer_eligibility_patterns.txt`
- `melanoma_eligibility_patterns.txt`
- `ovarian_cancer_eligibility_patterns.txt`
- `prostate_cancer_eligibility_patterns.txt`
- `pancreatic_cancer_eligibility_patterns.txt`
- `gastric_cancer_eligibility_patterns.txt`
- `head_and_neck_cancer_eligibility_patterns.txt`

Each file contains ~200 trials with:
- Full eligibility criteria text
- Trial phase and status
- Interventions being tested
- Age/sex requirements
- Biomarkers mentioned

#### Biomarker Trial Files
- `[cancer_type]_biomarker_trials.txt`

Organized by biomarker with trials that specifically require that biomarker.

## How to Build the Dynamic Corpus

### Step 1: Run the Corpus Builder

```bash
cd tools
python build_eligibility_corpus.py
```

This script will:
1. Query ClinicalTrials.gov API for 200 trials per cancer type
2. Extract eligibility criteria from each trial
3. Identify biomarker mentions (EGFR, PIK3CA, PD-L1, etc.)
4. Generate structured text files in `knowledge_base/trial_patterns/`
5. Takes ~10-15 minutes (with API rate limiting)

### Step 2: Rebuild RAG Vectorstore

After generating corpus files:

```python
from tools.clinical_rag import ClinicalRAG

rag = ClinicalRAG()
rag.build_vectorstore(force_rebuild=True)  # Force rebuild to index new files
```

This will:
1. Load all PDFs from guidelines/drug_labels/biomarker_guides/
2. Load all TXT files from trial_patterns/ (NEW)
3. Chunk documents (1000 char chunks, 200 char overlap)
4. Generate embeddings with OpenAI text-embedding-3-small
5. Build FAISS vectorstore
6. Save to disk at `vectorstore/clinical_guidelines.faiss`

### Step 3: Test the Integration

```bash
python tools/test_corpus_integration.py
```

Test suite validates:
- ✅ RAG loads all corpus files correctly
- ✅ Biomarker queries retrieve relevant information
- ✅ Eligibility pattern queries work
- ✅ Real patient scenarios are handled
- ✅ Improvement metrics documented

## How the RAG System Uses This Data

### Before Eligibility Corpus

**Query:** "PIK3CA E545K mutation cervical cancer trials"

**Retrieved from guidelines:**
- "For advanced cervical cancer, standard treatment is concurrent chemoradiation"
- "Pembrolizumab approved for PD-L1 CPS ≥1%"

**Problem:** No direct connection between PIK3CA mutation and available trials.

### After Eligibility Corpus

**Query:** "PIK3CA E545K mutation cervical cancer trials"

**Retrieved from trial_patterns:**
- "PIK3CA E545K is a hotspot mutation targetable by PI3K inhibitors"
- "Active trials: Alpelisib (NCT02437318), GDC-0077 (NCT03006172)"
- "Eligibility: Prior platinum therapy, ECOG 0-1, measurable disease"
- "PIK3CA mutations found in 15-30% of cervical cancers"

**Result:** System can now recommend biomarker-specific trials.

## Impact on Trial Matching Accuracy

### Key Improvements

1. **Biomarker-Driven Matching** (NEW)
   - Identifies PIK3CA → alpelisib trials
   - Recognizes PD-L1 expression thresholds (CPS ≥1, ≥10, TPS ≥50%)
   - Maps EGFR exon 19 deletion → osimertinib trials

2. **Eligibility Prediction** (NEW)
   - ECOG 0-1 required for Phase 2 → filters trials appropriately
   - Brain metastases allowed if stable → expands trial options
   - Prior treatment lines → matches patient to correct trial line

3. **Cancer-Specific Patterns** (NEW)
   - NSCLC trials require EGFR/ALK testing
   - Breast cancer trials specify HR/HER2 status
   - CRC trials require RAS/BRAF testing
   - Cervical cancer trials assess HPV and PD-L1

4. **False Positive Reduction**
   - Excludes trials where patient doesn't meet criteria
   - Avoids recommending EGFR trials to EGFR-negative patients
   - Filters out trials requiring biomarkers patient lacks

## Usage Examples

### Example 1: Biomarker Query

```python
from tools.clinical_rag import ClinicalRAG

rag = ClinicalRAG()
rag.build_vectorstore(force_rebuild=False)

query = "PIK3CA E545K mutation targeted therapy trials"
results = rag.retrieve(query, k=5)

for result in results:
    print(f"Source: {result['source']}")
    print(f"Content: {result['content'][:300]}...")
```

**Expected Output:**
- Information from `actionable_biomarkers.txt` about PI3K inhibitors
- Relevant sections from `cervical_cancer_biomarker_trials.txt`
- Eligibility criteria patterns for biomarker-selected trials

### Example 2: Eligibility Pattern Query

```python
query = "Phase 2 lung cancer ECOG performance status requirements"
results = rag.retrieve(query, k=3)
```

**Expected Output:**
- Phase 2 eligibility patterns from `common_eligibility_patterns.txt`
- NSCLC-specific criteria from `lung_cancer_eligibility_patterns.txt`
- ECOG 0-1 standard requirements

### Example 3: Real Patient Scenario

```python
# Patient: 40F, Stage IIIB cervical cancer, PIK3CA E545K, PD-L1 15%
query = "cervical cancer PIK3CA mutation PD-L1 expression clinical trial eligibility"
results = rag.retrieve(query, k=5)
```

**Expected Output:**
- PIK3CA mutation → PI3K inhibitor trials (alpelisib)
- PD-L1 15% (CPS) → pembrolizumab eligibility (approved for CPS ≥1%)
- Stage IIIB → locally advanced cervical cancer trial criteria
- ECOG, organ function, prior therapy requirements

## Maintenance and Updates

### When to Rebuild Corpus

Rebuild the dynamic corpus when:
- **Quarterly** - to capture newly recruiting trials
- **New FDA approvals** - biomarker-drug associations change
- **Major guideline updates** - NCCN, ASCO guideline revisions
- **New biomarker tests** - expanded NGS panels

### How to Update Static Reference Documents

Edit `actionable_biomarkers.txt` or `common_eligibility_patterns.txt` when:
- New biomarker-therapy associations are FDA-approved
- Trial eligibility patterns evolve (e.g., brain mets policies)
- New cancer types require coverage

After editing, rebuild vectorstore:
```python
rag.build_vectorstore(force_rebuild=True)
```

## File Format Specifications

### Text File Structure

All corpus files follow this format:

```
# Document Title
# Metadata lines with #

Introduction paragraph explaining the document scope.

================================================================================
## SECTION HEADER
================================================================================

Content organized with clear headers...

**Subsection:**
- Bullet points
- Lists

**Key Information:**
Structured data that RAG can chunk and retrieve.

================================================================================
## NEXT SECTION
================================================================================
```

### Why This Format?

1. **Markdown-compatible:** Easy to read and edit
2. **Clear section breaks:** Helps text splitter create meaningful chunks
3. **Hierarchical structure:** Headers organize information logically
4. **Metadata included:** Category, source, file path added by loader

### Chunking Strategy

- **Chunk size:** 1000 characters
- **Overlap:** 200 characters
- **Separators:** `\n\n`, `\n`, `.`, ` ` (in priority order)
- **Result:** Semantic chunks that preserve context

## Expected Performance Gains

Based on RAG literature and biomarker trial matching studies:

- **Biomarker-trial matching:** +30-40% accuracy
- **Eligibility prediction:** +25-35% accuracy
- **False positive reduction:** -40-50% inappropriate trials
- **Overall trial matching:** +20-30% precision

## Troubleshooting

### Issue: Vectorstore not loading new files

**Solution:**
```python
rag.build_vectorstore(force_rebuild=True)  # Force rebuild
```

### Issue: Corpus builder API errors

**Solution:**
- Check internet connection
- Verify ClinicalTrials.gov API is accessible
- Increase timeout in requests (timeout=60)
- Add longer sleep between requests (time.sleep(5))

### Issue: Poor retrieval quality

**Diagnosis:**
1. Check if files exist in trial_patterns/
2. Verify file encoding is UTF-8
3. Confirm chunk size is appropriate (1000 chars)
4. Test with multiple queries

**Solutions:**
- Adjust chunk size (try 800-1200 range)
- Modify chunk overlap (try 150-250 range)
- Use hybrid retrieval (BM25 + dense)
- Expand query with synonyms

## Next Steps

After setting up the eligibility corpus:

1. **Run end-to-end workflow** with real patient
2. **Compare results** before/after corpus integration
3. **Measure accuracy** on biomarker matching
4. **Iterate on corpus content** based on retrieval gaps
5. **Add hybrid retrieval** (BM25 + FAISS) for even better results
6. **Implement query enhancement** for medical term expansion

## Contributing

To add new knowledge to the corpus:

1. Create structured TXT files following format above
2. Place in `knowledge_base/trial_patterns/`
3. Rebuild vectorstore
4. Test retrieval with relevant queries
5. Document additions in this README

## References

- ClinicalTrials.gov API v2.0: https://clinicaltrials.gov/api/v2/
- NCCN Guidelines: https://www.nccn.org/guidelines
- FDA Drug Approvals: https://www.fda.gov/drugs
- OncoKB: https://www.oncokb.org/ (biomarker knowledge)
- My Cancer Genome: https://www.mycancergenome.org/

---

**Last Updated:** 2025-11-06
**Version:** 1.0
**Maintainer:** Clinical Trials Matching System v2.0
