# Quick Start Guide - For Supervisor

## 🚀 Launch the Web Interface (EASIEST METHOD)

### Windows:
**Double-click this file:**
```
START_WEB_DEMO.bat
```

### Mac/Linux:
```bash
streamlit run app.py
```

**Then:**
1. Browser will open automatically at `http://localhost:8501`
2. If not, manually open: http://localhost:8501

---

## 📱 Using the Web Interface

### Step 1: Select a Patient Case
- Use the dropdown in the sidebar to select a patient case
- Example: "lung_egfr_exon19 - 62M with metastatic NSCLC..."

### Step 2: Run the Methods

**Three options:**

1. **🔍 Run General Search** - Baseline method (no RAG)
2. **🧠 Run RAG-Enhanced** - Full system with knowledge base
3. **⚡ Run Both (Compare)** - Side-by-side comparison (RECOMMENDED)

### Step 3: View Results

**Three tabs will appear:**

1. **📊 General Search** - Shows trials found by keyword matching
2. **🧠 RAG-Enhanced** - Shows trials after RAG re-ranking
3. **🔄 Comparison** - Side-by-side comparison showing what changed

---

## 🎯 What to Look For

### Key Metrics:

1. **Ground Truth Found** - How many expert-labeled trials appear in top results
   - Higher = Better accuracy
   - Ground truth trials marked with 🎯

2. **Rankings Changed** - How many trials were re-ranked by RAG
   - Shows RAG's impact

3. **Precision@N** - % of top N trials that are ground truth
   - Measures clinical relevance

### Visual Indicators:

- **Green cards** 🎯 = Ground truth trials (expert-labeled as appropriate)
- **↑ N** = RAG moved this trial UP by N positions
- **↓ N** = RAG moved this trial DOWN by N positions
- **=** = No change in ranking
- **OUT** = Trial dropped out of top N

---

## 📊 Example Interpretation

**If you see:**
```
Rank  General Search    RAG-Enhanced      Change
----  ---------------   ---------------   ------
1     NCT12345678       NCT12345678       =
2     NCT87654321       NCT99999999 🎯    ↑ 5
3     NCT99999999 🎯    NCT87654321       ↓ 1
```

**This means:**
- Trial NCT99999999 (ground truth) was at rank 7 in general search
- RAG identified it as more relevant and moved it UP to rank 2
- This shows RAG is using clinical knowledge to improve rankings

---

## 🎓 Understanding the Methods

### General Search (Baseline):
- **What:** Keyword matching + basic LLM ranking
- **Knowledge Used:** None
- **Speed:** Fast (~30 seconds)
- **Files:** Phase 2 of `agents/workflow_engine.py`

### RAG-Enhanced (Your System):
- **What:** General search + clinical knowledge re-ranking
- **Knowledge Used:**
  - NCCN Guidelines (44MB)
  - FDA Drug Labels (20MB)
  - Biomarker databases
- **Speed:** Slower (~60 seconds) due to knowledge retrieval
- **Files:** Phase 2 + Phase 3 of `agents/workflow_engine.py`

---

## 🔧 Troubleshooting

### Web interface won't start:

**1. Check Streamlit is installed:**
```bash
pip install streamlit
```

**2. Run manually:**
```bash
streamlit run app.py
```

**3. Check port availability:**
- Default port is 8501
- If busy, Streamlit will try 8502, 8503, etc.

### "No test cases found" error:

**Check file exists:**
```bash
dir evaluation\test_cases.json
```

If missing, the evaluation data is corrupted. Contact the developer.

### Results take too long:

- Each search takes ~30-60 seconds
- "Run Both" will take ~90-120 seconds total
- This is normal - the system is calling OpenAI API and searching thousands of trials

### Unicode/encoding errors:

- Should be fixed automatically via `fix_encoding_global.py`
- If you see garbled text, let the developer know

---

## 💡 Tips for Demo

### Best Test Cases to Show:

1. **lung_egfr_exon19** - Lung cancer with specific mutation (shows biomarker matching)
2. **breast_her2_brca** - Breast cancer with HER2+ and BRCA mutation (complex case)
3. **melanoma_braf_v600e** - Melanoma with BRAF mutation (common case)

### What to Highlight:

1. **Ground truth trials** (🎯) moving up in rankings with RAG
2. **Clinical knowledge** being applied (sidebar shows what knowledge sources are used)
3. **Interpretability** - System can explain why trials were ranked higher
4. **Practical utility** - Top 3-5 results are what clinicians actually see

### Expected Results:

- RAG should find **more ground truth trials** in top 10
- Rankings should **change 30-50%** of the time
- Ground truth trials should **move UP** with RAG

---

## 📁 File Reference

| Purpose | File | Description |
|---------|------|-------------|
| **Web Interface** | `app.py` | Streamlit web app |
| **Launch Script** | `START_WEB_DEMO.bat` | Windows launcher |
| **General Search** | `agents/workflow_engine.py` | Phase 2 (line ~150) |
| **RAG Enhancement** | `agents/workflow_engine.py` | Phase 3 (line ~250) |
| **Knowledge Base** | `vectorstore/clinical_guidelines.faiss` | 22MB FAISS index |

---

## 📞 Questions?

If something doesn't work:
1. Check the console/terminal for error messages
2. Try a different test case
3. Restart the web server (Ctrl+C, then re-run)
4. Contact the developer with the error message

---

## 🎯 Expected Demo Flow

**For your supervisor:**

1. **Launch:** Double-click `START_WEB_DEMO.bat`
2. **Select:** Choose "lung_egfr_exon19" from dropdown
3. **Click:** "⚡ Run Both (Compare)"
4. **Wait:** ~90 seconds for both methods to complete
5. **Review:**
   - Check "Comparison" tab
   - Look for 🎯 ground truth trials
   - See how RAG changed rankings
6. **Repeat:** Try 2-3 different cases to see consistency

**Total demo time:** 5-10 minutes per case

---

## ✅ Success Criteria

Your supervisor should observe:

1. ✅ RAG finds MORE ground truth trials in top 10
2. ✅ RAG moves clinically relevant trials HIGHER
3. ✅ System provides clear comparison (before/after)
4. ✅ Interface is easy to use (non-technical users can operate)

If you see these results, the system is working as designed! 🎉
