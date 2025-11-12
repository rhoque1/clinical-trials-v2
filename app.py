"""
Clinical Trial Matching System - Web Demo
==========================================

Web interface for comparing General Search vs RAG-Enhanced Search

Usage:
    streamlit run app.py

Then open browser to: http://localhost:8501
"""
import fix_encoding_global
import streamlit as st
import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Page config
st.set_page_config(
    page_title="Clinical Trial Matching Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .method-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .result-card {
        border-left: 4px solid #1f77b4;
        padding: 15px;
        margin: 10px 0;
        background-color: #f0f8ff;
    }
    .trial-item {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 8px 0;
        background-color: white;
    }
    .ground-truth {
        background-color: #d4edda !important;
        border-left: 4px solid #28a745 !important;
    }
</style>
""", unsafe_allow_html=True)


class TrialMatchingDemo:
    """Web interface for trial matching demo"""

    def __init__(self):
        self.test_cases_path = Path("evaluation/test_cases.json")
        self.sample_profiles_dir = Path("evaluation/sample_profiles")

        # Load test cases
        if self.test_cases_path.exists():
            with open(self.test_cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data["test_cases"]
        else:
            self.test_cases = []

    def get_test_case_options(self):
        """Get formatted options for test case selection"""
        options = {}
        for tc in self.test_cases:
            case_id = tc["case_id"]
            summary = tc.get("patient_summary", "No summary")[:80]
            options[f"{case_id} - {summary}..."] = case_id
        return options

    async def run_general_search(self, patient_profile):
        """Run general search (no RAG)"""
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode
        import agents.workflow_engine as wf_module

        # Disable RAG
        wf_module.DISABLE_RAG_FOR_EXPERIMENT = True

        try:
            engine = WorkflowEngine(mode=WorkflowMode.WIZARD)
            discovery_result = await engine.run_trial_discovery(patient_profile)

            if not discovery_result.get("success"):
                return None, "Discovery failed"

            trials = discovery_result.get("ranked_trials", [])
            return trials, None

        except Exception as e:
            return None, str(e)
        finally:
            wf_module.DISABLE_RAG_FOR_EXPERIMENT = False

    async def run_rag_enhanced_search(self, patient_profile):
        """Run RAG-enhanced search"""
        from agents.workflow_engine import WorkflowEngine
        from agents.orchestrator import WorkflowMode
        import agents.workflow_engine as wf_module

        # Enable RAG
        wf_module.DISABLE_RAG_FOR_EXPERIMENT = False

        try:
            engine = WorkflowEngine(mode=WorkflowMode.WIZARD)

            # Phase 2: Discovery
            discovery_result = await engine.run_trial_discovery(patient_profile)
            if not discovery_result.get("success"):
                return None, "Discovery failed"

            trials = discovery_result.get("ranked_trials", [])

            # Phase 3: RAG Enhancement
            enhancement_result = await engine.run_knowledge_enhancement(
                patient_profile,
                trials
            )

            if not enhancement_result.get("success"):
                return trials, "Enhancement failed, returning unenhanced results"

            enhanced_trials = enhancement_result.get("ranked_trials", [])
            return enhanced_trials, None

        except Exception as e:
            return None, str(e)


def display_trial_card(trial, rank, ground_truth_ncts=None, show_score=True):
    """Display a single trial as a card"""
    nct_id = trial.get("nct_id", "N/A")
    title = trial.get("title", "No title")
    score = trial.get("score", 0)
    status = trial.get("overall_status", "Unknown")
    phases = ", ".join(trial.get("phases", []))

    is_ground_truth = ground_truth_ncts and nct_id in ground_truth_ncts

    card_class = "ground-truth" if is_ground_truth else ""

    st.markdown(f"""
    <div class="trial-item {card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>#{rank} - {nct_id}</strong>
                {' 🎯 GROUND TRUTH' if is_ground_truth else ''}
            </div>
            <div style="text-align: right;">
                {f'<span style="font-size: 1.2rem; font-weight: bold; color: #1f77b4;">Score: {score}</span>' if show_score else ''}
            </div>
        </div>
        <div style="margin-top: 8px;">
            <strong>Title:</strong> {title}
        </div>
        <div style="margin-top: 8px; font-size: 0.9rem; color: #666;">
            <strong>Status:</strong> {status} | <strong>Phase:</strong> {phases if phases else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main app"""

    # Header
    st.markdown('<div class="main-header">🏥 Clinical Trial Matching System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Compare General Search vs RAG-Enhanced Search</div>', unsafe_allow_html=True)

    demo = TrialMatchingDemo()

    if not demo.test_cases:
        st.error("❌ No test cases found. Please ensure evaluation/test_cases.json exists.")
        return

    # Sidebar
    st.sidebar.title("⚙️ Configuration")

    # Test case selection
    test_case_options = demo.get_test_case_options()
    selected_display = st.sidebar.selectbox(
        "Select Patient Case",
        options=list(test_case_options.keys()),
        index=1 if len(test_case_options) > 1 else 0
    )
    selected_case_id = test_case_options[selected_display]

    # Load selected test case
    test_case = next((tc for tc in demo.test_cases if tc["case_id"] == selected_case_id), None)

    if not test_case:
        st.error("❌ Selected test case not found")
        return

    # Display patient info
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Patient Profile")
    patient_summary = test_case.get("patient_summary", "No summary available")
    st.sidebar.info(patient_summary)

    # Ground truth info
    ground_truth_ncts = [gt["nct_id"] for gt in test_case.get("ground_truth_trials", [])]
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Ground Truth Trials")
    st.sidebar.caption(f"{len(ground_truth_ncts)} expert-labeled trial(s)")
    for nct in ground_truth_ncts:
        st.sidebar.code(nct, language=None)

    # Number of trials to show
    st.sidebar.markdown("---")
    num_trials = st.sidebar.slider("Number of trials to display", 5, 20, 10)

    # Main area - Method explanations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="method-card">
            <h3>📊 Method 1: General Search</h3>
            <p><strong>How it works:</strong></p>
            <ol>
                <li>Search ClinicalTrials.gov API</li>
                <li>Rank by keyword relevance</li>
                <li>LLM-based scoring</li>
            </ol>
            <p><strong>No knowledge base used</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="method-card">
            <h3>🧠 Method 2: RAG-Enhanced</h3>
            <p><strong>How it works:</strong></p>
            <ol>
                <li>General search (same as Method 1)</li>
                <li>Retrieve clinical knowledge from:</li>
                <ul style="margin-left: 20px;">
                    <li>NCCN Guidelines (44MB)</li>
                    <li>FDA Drug Labels (20MB)</li>
                    <li>Biomarker databases</li>
                </ul>
                <li>Re-rank using retrieved knowledge</li>
            </ol>
            <p><strong>Knowledge-enhanced results</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        run_general = st.button("🔍 Run General Search", use_container_width=True, type="primary")

    with col2:
        run_rag = st.button("🧠 Run RAG-Enhanced", use_container_width=True, type="primary")

    with col3:
        run_both = st.button("⚡ Run Both (Compare)", use_container_width=True, type="secondary")

    # Initialize session state
    if 'general_results' not in st.session_state:
        st.session_state.general_results = None
    if 'rag_results' not in st.session_state:
        st.session_state.rag_results = None

    # Load patient profile
    profile_path = demo.sample_profiles_dir / f"{selected_case_id}.json"
    if not profile_path.exists():
        st.error(f"❌ Patient profile not found: {profile_path}")
        return

    with open(profile_path, 'r', encoding='utf-8') as f:
        patient_profile = json.load(f)

    # Run general search
    if run_general or run_both:
        with st.spinner("🔍 Running general search..."):
            try:
                trials, error = asyncio.run(demo.run_general_search(patient_profile))
                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    st.session_state.general_results = trials
                    st.success(f"✅ Found {len(trials)} trials using general search")
            except Exception as e:
                st.error(f"❌ Exception: {str(e)}")

    # Run RAG-enhanced search
    if run_rag or run_both:
        with st.spinner("🧠 Running RAG-enhanced search..."):
            try:
                trials, error = asyncio.run(demo.run_rag_enhanced_search(patient_profile))
                if error:
                    st.warning(f"⚠️ {error}")
                if trials:
                    st.session_state.rag_results = trials
                    st.success(f"✅ Found {len(trials)} trials using RAG-enhanced search")
            except Exception as e:
                st.error(f"❌ Exception: {str(e)}")

    # Display results
    st.markdown("---")
    st.subheader("📊 Results")

    if st.session_state.general_results is None and st.session_state.rag_results is None:
        st.info("👆 Click a button above to run the trial matching system")
        return

    # Create tabs for results
    if st.session_state.general_results and st.session_state.rag_results:
        tab1, tab2, tab3 = st.tabs(["📊 General Search", "🧠 RAG-Enhanced", "🔄 Comparison"])
    elif st.session_state.general_results:
        tab1 = st.tabs(["📊 General Search"])[0]
        tab2, tab3 = None, None
    else:
        tab2 = st.tabs(["🧠 RAG-Enhanced"])[0]
        tab1, tab3 = None, None

    # Tab 1: General Search Results
    if st.session_state.general_results and (tab1 if tab1 else True):
        with (tab1 if tab1 else st.container()):
            st.subheader("General Search Results")

            general_ncts = [t.get("nct_id") for t in st.session_state.general_results[:num_trials]]
            found_in_general = [nct for nct in ground_truth_ncts if nct in general_ncts]

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trials Retrieved", len(st.session_state.general_results))
            with col2:
                precision = len(found_in_general) / len(ground_truth_ncts) if ground_truth_ncts else 0
                st.metric(f"Precision@{num_trials}", f"{precision:.1%}")
            with col3:
                st.metric("Ground Truth Found", f"{len(found_in_general)}/{len(ground_truth_ncts)}")

            # Display trials
            st.markdown(f"**Top {num_trials} Trials:**")
            for i, trial in enumerate(st.session_state.general_results[:num_trials], 1):
                display_trial_card(trial, i, ground_truth_ncts)

    # Tab 2: RAG-Enhanced Results
    if st.session_state.rag_results and (tab2 if tab2 else True):
        with (tab2 if tab2 else st.container()):
            st.subheader("RAG-Enhanced Results")

            rag_ncts = [t.get("nct_id") for t in st.session_state.rag_results[:num_trials]]
            found_in_rag = [nct for nct in ground_truth_ncts if nct in rag_ncts]

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trials Retrieved", len(st.session_state.rag_results))
            with col2:
                precision = len(found_in_rag) / len(ground_truth_ncts) if ground_truth_ncts else 0
                st.metric(f"Precision@{num_trials}", f"{precision:.1%}")
            with col3:
                st.metric("Ground Truth Found", f"{len(found_in_rag)}/{len(ground_truth_ncts)}")

            # Display trials
            st.markdown(f"**Top {num_trials} Trials:**")
            for i, trial in enumerate(st.session_state.rag_results[:num_trials], 1):
                display_trial_card(trial, i, ground_truth_ncts)

    # Tab 3: Comparison
    if tab3 and st.session_state.general_results and st.session_state.rag_results:
        with tab3:
            st.subheader("Side-by-Side Comparison")

            general_ncts = [t.get("nct_id") for t in st.session_state.general_results[:num_trials]]
            rag_ncts = [t.get("nct_id") for t in st.session_state.rag_results[:num_trials]]

            # Calculate changes
            changes = 0
            for i in range(min(num_trials, len(general_ncts), len(rag_ncts))):
                if general_ncts[i] != rag_ncts[i]:
                    changes += 1

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                general_found = sum(1 for nct in ground_truth_ncts if nct in general_ncts)
                st.metric("General: Ground Truth Found", f"{general_found}/{len(ground_truth_ncts)}")
            with col2:
                rag_found = sum(1 for nct in ground_truth_ncts if nct in rag_ncts)
                improvement = rag_found - general_found
                st.metric("RAG: Ground Truth Found", f"{rag_found}/{len(ground_truth_ncts)}",
                         delta=f"{improvement:+d}" if improvement != 0 else None)
            with col3:
                st.metric("Rankings Changed", f"{changes}/{num_trials}")

            # Comparison table
            st.markdown("**Ranking Comparison:**")

            comparison_data = []
            for i in range(num_trials):
                rank = i + 1
                general_nct = general_ncts[i] if i < len(general_ncts) else "-"
                rag_nct = rag_ncts[i] if i < len(rag_ncts) else "-"

                # Calculate change
                if general_nct in rag_ncts:
                    rag_rank = rag_ncts.index(general_nct) + 1
                    diff = rank - rag_rank
                    if diff > 0:
                        change = f"↓ {diff}"
                    elif diff < 0:
                        change = f"↑ {abs(diff)}"
                    else:
                        change = "="
                elif general_nct != "-":
                    change = "OUT"
                else:
                    change = "-"

                # Mark ground truth
                general_marker = " 🎯" if general_nct in ground_truth_ncts else ""
                rag_marker = " 🎯" if rag_nct in ground_truth_ncts else ""

                comparison_data.append({
                    "Rank": rank,
                    "General Search": f"{general_nct}{general_marker}",
                    "RAG-Enhanced": f"{rag_nct}{rag_marker}",
                    "Change": change
                })

            st.dataframe(comparison_data, use_container_width=True, height=400)

            st.caption("**Legend:** ↑ = Moved up | ↓ = Moved down | = = No change | OUT = Dropped out of top N | 🎯 = Ground truth trial")


if __name__ == "__main__":
    main()
