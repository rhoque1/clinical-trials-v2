"""
Test the Orchestrator's workflow planning
"""
import sys
sys.path.append('..')

from agents.orchestrator import Orchestrator, WorkflowMode


def test_orchestrator_planning():
    """Test workflow planning for different scenarios"""
    print("Testing Orchestrator Workflow Planning...")
    print("=" * 60)
    
    orchestrator = Orchestrator(mode=WorkflowMode.WIZARD)
    
    # Test Case 1: Full workflow - analyze report and find trials
    print("\n[LIST] Test Case 1: Analyze PDF and find trials")
    request1 = "Please analyze my medical report PDF and find relevant clinical trials"
    workflow1 = orchestrator.plan_workflow(request1)
    print(f"   Request: {request1}")
    print(f"   Planned workflow: {workflow1}")
    assert "patient_profiler" in workflow1, "Should include patient profiler"
    assert "trial_discovery" in workflow1, "Should include trial discovery"
    assert "clinical_advisor" in workflow1, "Should include advisor"
    print("   [OK] Correct workflow planned")
    
    # Test Case 2: Just find trials (no PDF)
    print("\n[LIST] Test Case 2: Direct trial search")
    orchestrator2 = Orchestrator(mode=WorkflowMode.EXPRESS)
    request2 = "Find lung cancer clinical trials in California"
    workflow2 = orchestrator2.plan_workflow(request2)
    print(f"   Request: {request2}")
    print(f"   Planned workflow: {workflow2}")
    assert "trial_discovery" in workflow2, "Should include trial discovery"
    print("   [OK] Correct workflow planned")
    
    # Test Case 3: Eligibility check
    print("\n[LIST] Test Case 3: Check eligibility")
    orchestrator3 = Orchestrator()
    request3 = "Check if I'm eligible for NCT12345678"
    workflow3 = orchestrator3.plan_workflow(request3)
    print(f"   Request: {request3}")
    print(f"   Planned workflow: {workflow3}")
    assert "eligibility_analyzer" in workflow3, "Should include eligibility analyzer"
    print("   [OK] Correct workflow planned")
    
    # Test workflow progression
    print("\n[LIST] Test Case 4: Workflow progression")
    orchestrator4 = Orchestrator()
    workflow4 = orchestrator4.plan_workflow("Analyze report and find trials")
    
    print(f"   Total machines: {len(workflow4)}")
    print(f"   Initial summary: {orchestrator4.get_workflow_summary()}")
    
    # Simulate progression through workflow
    step = 1
    while not orchestrator4.is_workflow_complete():
        current = orchestrator4.get_current_machine()
        print(f"   Step {step}: Executing {current}")
        orchestrator4.advance_to_next_machine()
        step += 1
    
    print(f"   Final summary: {orchestrator4.get_workflow_summary()}")
    assert orchestrator4.is_workflow_complete(), "Workflow should be complete"
    print("   [OK] Workflow progression working correctly")
    
    print("\n" + "=" * 60)
    print("[OK] ALL ORCHESTRATOR TESTS PASSED!")


if __name__ == "__main__":
    test_orchestrator_planning()