# Clinical Trial Matching System v2.0

An intelligent clinical trial matching system that uses RAG (Retrieval-Augmented Generation) to enhance trial discovery and ranking for cancer patients.

## Overview

This system matches cancer patients to relevant clinical trials using a multi-phase workflow:

1. **Patient Profiling** - Extracts structured medical information from patient narratives
2. **Trial Discovery** - Searches ClinicalTrials.gov API and performs initial ranking
3. **Knowledge Enhancement** - Uses RAG to retrieve clinical knowledge from:
   - NCCN Guidelines (44MB)
   - FDA Drug Labels (20MB)
   - Biomarker databases
4. **Eligibility Analysis** - Deep eligibility criteria matching

## Features

- **Web Interface** - Interactive Streamlit app for comparing search methods
- **RAG-Enhanced Ranking** - Improves trial relevance using clinical knowledge base
- **Ground Truth Validation** - Compare results against expert-labeled trials
- **Side-by-Side Comparison** - Visualize improvements from RAG enhancement

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (for LLM-based processing)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/clinical-trials-v2.git
cd clinical-trials-v2
```

### 2. Create Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Streamlit Web Interface

### Quick Start

```bash
streamlit run app.py
```

Or use the provided batch file (Windows):

```bash
START_WEB_DEMO.bat
```

The app will open automatically in your default browser at `http://localhost:8501`

### What the Interface Does

The web app provides an interactive demo that:

1. **Select Patient Cases** - Choose from pre-loaded patient profiles
2. **Run Searches** - Execute either:
   - General Search (baseline)
   - RAG-Enhanced Search (knowledge-augmented)
   - Both methods for comparison
3. **View Results** - See ranked trials with:
   - Ground truth highlighting (expert-labeled trials)
   - Precision metrics
   - Side-by-side comparisons

### Using the Interface

1. **Select a Patient Case** from the sidebar dropdown
2. **Review Patient Profile** and ground truth trials in the sidebar
3. **Choose a Search Method**:
   - Click "Run General Search" for baseline results
   - Click "Run RAG-Enhanced" for knowledge-augmented results
   - Click "Run Both (Compare)" to see side-by-side comparison
4. **Analyze Results**:
   - Green cards indicate ground truth trials found
   - View precision metrics and ranking changes
   - Use the comparison tab to see detailed differences

## Project Structure

```
clinical-trials-v2/
├── agents/                      # Agent implementations
│   ├── orchestrator.py         # Main workflow orchestrator
│   ├── state_machine_agent.py  # State machine agent
│   └── workflow_engine.py      # Workflow execution engine
├── state_machines/              # State machine workflows
│   ├── patient_profiler.py     # Patient profiling workflow
│   ├── trial_discovery.py      # Trial discovery workflow
│   └── knowledge_enhanced_ranking.py  # RAG enhancement workflow
├── tools/                       # Tool implementations
│   ├── clinical_rag.py         # RAG retrieval system
│   └── api_tools.py            # ClinicalTrials.gov API
├── evaluation/                  # Test cases and evaluation
│   ├── test_cases.json         # Ground truth test cases
│   └── sample_profiles/        # Patient profile JSON files
├── vectorstore/                 # FAISS vector store for RAG
│   ├── clinical_guidelines.faiss
│   └── clinical_guidelines.pkl
├── app.py                       # Streamlit web interface
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## System Architecture

### Workflow Phases

1. **Phase 1: Patient Profiling**
   - Extracts cancer type, stage, biomarkers, treatments
   - Structures information for trial matching

2. **Phase 2: Trial Discovery**
   - Searches ClinicalTrials.gov API
   - Filters by condition, location, status
   - Initial LLM-based ranking

3. **Phase 3: RAG Enhancement** (Optional)
   - Retrieves relevant clinical knowledge
   - Re-ranks trials using knowledge context
   - Improves relevance and precision

4. **Phase 4: Eligibility Analysis**
   - Deep analysis of eligibility criteria
   - Detailed matching logic

### RAG Knowledge Base

The system uses a FAISS vector store containing:
- **NCCN Guidelines** - Evidence-based cancer treatment guidelines
- **FDA Drug Labels** - Official prescribing information
- **Biomarker Information** - Molecular marker databases

## Development

### Running Tests

```bash
# Test complete workflow
python tests/test_complete_workflow.py

# Test RAG retrieval
python run_rag_test.py

# Test ground truth validation
python test_curated_ground_truth.py
```

### Rebuilding Vector Store

If you need to rebuild the knowledge base:

```bash
python rebuild_vectorstore.py
```

## API Keys

This system requires:
- **OpenAI API Key** - For LLM-based processing (required)

Set in `.env` file:
```
OPENAI_API_KEY=your_key_here
```

## Performance Metrics

The system tracks:
- **Precision@K** - Percentage of ground truth trials found in top K results
- **Ranking Changes** - How RAG enhancement affects trial ordering
- **Ground Truth Recovery** - Success rate at finding expert-labeled trials

## Troubleshooting

### Port Already in Use

If port 8501 is already in use:

```bash
streamlit run app.py --server.port 8502
```

### Import Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt --upgrade
```

### Encoding Issues

The system includes `fix_encoding_global.py` to handle encoding issues automatically.

### OpenAI API Errors

- Verify your API key is set in `.env`
- Check you have sufficient credits/quota
- Ensure network connectivity

## Citation

If you use this system in research, please cite:

```
Clinical Trial Matching System v2.0
RAG-Enhanced Trial Discovery and Ranking
[Your Name/Institution]
2025
```

## License

[Specify your license here]

## Contact

For questions or issues, please contact [your contact information]

## Acknowledgments

- ClinicalTrials.gov for trial data
- NCCN for clinical guidelines
- OpenAI for LLM capabilities
