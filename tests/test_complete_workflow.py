"""
Test complete workflow end-to-end
This is a critical integration test
"""
import sys
import asyncio
sys.path.append('..')

from agents.workflow_engine import WorkflowEngine, WorkflowMode


async def test_workflow_with_pdf():
    """Test the complete workflow with a real PDF"""
    print("Testing Complete Workflow Integration...")
    print("="*70)
    
    # You'll need to provide a real PDF path
    # For now, let's use a path variable
    pdf_path = input("\nEnter path to a medical report PDF (or press Enter to skip): ").strip().strip('"')
    
    if not pdf_path:
        print("\n[!]  No PDF provided. Skipping integration test.")
        print("   To test, run again with a medical report PDF.")
        return False
    
    # Create workflow engine in wizard mode
    engine = WorkflowEngine(mode=WorkflowMode.WIZARD)
    
    try:
        # Run complete workflow
        result = await engine.run_complete_workflow(pdf_path)
        
        if result["success"]:
            print("\n" + "="*70)
            print("[OK] COMPLETE WORKFLOW TEST PASSED!")
            print("="*70)
            
            profile = result["patient_profile"]
            print("\n[LIST] Final Patient Profile:")
            print(f"   Demographics: {profile.get('demographics', {})}")
            print(f"   Primary Diagnosis: {profile.get('diagnoses', {})}")
            print(f"   Key Biomarkers: {profile.get('biomarkers', {})}")
            print(f"   Search Terms Generated: {len(profile.get('search_terms', []))}")
            
            return True
        else:
            print(f"\n[X] Workflow failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n[X] Error during workflow: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_workflow_with_pdf())
    
    if success:
        print("\n🎉 The new architecture is working!")
        print("   Next: Add trial discovery and matching")
    else:
        print("\n[!]  Review errors and try again")