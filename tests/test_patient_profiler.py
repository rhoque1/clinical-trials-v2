"""
Test the Patient Profiler state machine workflow
"""
import sys
sys.path.append('..')

from state_machines.patient_profiler import PatientProfilerMachine


def test_patient_profiler_workflow():
    """Test the complete patient profiling workflow"""
    print("Testing Patient Profiler State Machine...")
    print("=" * 60)
    
    # Create the profiler
    profiler = PatientProfilerMachine()
    
    # Verify initial state
    current = profiler.get_current_state()
    assert current.name == "extract_demographics", "Should start with demographics"
    print(f"[OK] Step 1: {current.name}")
    print(f"   Instruction: {current.get_instruction({})[:80]}...")
    
    # Simulate state 1: Demographics
    demo_data = {
        "age": "62",
        "gender": "Female",
        "performance_status": "ECOG 1"
    }
    result1 = profiler.execute_current_state(demo_data)
    print(f"[OK] Demographics extracted: {result1['demographics']}")
    
    # Check transition to state 2
    current = profiler.get_current_state()
    assert current.name == "extract_diagnoses", "Should transition to diagnoses"
    print(f"\n[OK] Step 2: {current.name}")
    
    # Simulate state 2: Diagnoses
    diagnosis_data = {
        "primary": "Stage IIIA Non-Small Cell Lung Cancer",
        "histology": "Adenocarcinoma",
        "status": "Newly diagnosed"
    }
    result2 = profiler.execute_current_state(diagnosis_data)
    print(f"[OK] Diagnoses extracted: {result2['diagnoses']}")
    
    # Check memory inheritance
    assert "demographics" in profiler.global_memory, "Should have demographics in memory"
    assert "diagnoses" in profiler.global_memory, "Should have diagnoses in memory"
    print(f"\n[OK] Memory inheritance working - Total memory keys: {list(profiler.global_memory.keys())}")
    
    # Simulate state 3: Biomarkers
    current = profiler.get_current_state()
    assert current.name == "extract_biomarkers", "Should transition to biomarkers"
    print(f"\n[OK] Step 3: {current.name}")
    
    biomarker_data = {
        "EGFR": "Exon 19 deletion",
        "PD-L1": "50%",
        "ALK": "Negative"
    }
    result3 = profiler.execute_current_state(biomarker_data)
    print(f"[OK] Biomarkers extracted: {result3['biomarkers']}")
    
    # Simulate state 4: Treatment history
    current = profiler.get_current_state()
    assert current.name == "extract_treatment_history", "Should transition to treatment history"
    print(f"\n[OK] Step 4: {current.name}")
    
    treatment_data = {
        "current": "None (newly diagnosed)",
        "prior": "None",
        "surgeries": "Biopsy 2 weeks ago"
    }
    result4 = profiler.execute_current_state(treatment_data)
    print(f"[OK] Treatment history extracted: {result4['treatment_history']}")
    
    # Simulate state 5: Generate search terms
    current = profiler.get_current_state()
    assert current.name == "generate_search_terms", "Should transition to search terms"
    print(f"\n[OK] Step 5: {current.name}")
    
    # The instruction should now have access to all previous memory
    instruction = current.get_instruction(profiler.global_memory)
    assert "Demographics:" in instruction, "Should include demographics in context"
    assert "Diagnoses:" in instruction, "Should include diagnoses in context"
    print(f"[OK] Search term generation has full context")
    
    search_terms = [
        "EGFR positive non-small cell lung cancer",
        "NSCLC EGFR exon 19 deletion",
        "lung adenocarcinoma EGFR",
        "stage III lung cancer"
    ]
    result5 = profiler.execute_current_state(search_terms)
    print(f"[OK] Search terms generated: {result5['search_terms'][:2]}...")
    
    # Verify completion
    assert profiler.is_complete(), "Workflow should be complete"
    print(f"\n[OK] Workflow complete!")
    
    # Show execution history
    print(f"\n[LIST] Execution History:")
    for i, step in enumerate(profiler.execution_history, 1):
        print(f"   {i}. {step['state']}")
    
    # Show final memory
    print(f"\n[DISK] Final Global Memory Keys: {list(profiler.global_memory.keys())}")
    print(f"   - Contains {len(profiler.global_memory)} pieces of information")
    
    print("\n" + "=" * 60)
    print("[OK] ALL PATIENT PROFILER TESTS PASSED!")


if __name__ == "__main__":
    test_patient_profiler_workflow()