"""
Test LLM integration with state machines
This verifies the LLM can execute state instructions
"""
import sys
import asyncio
sys.path.append('..')

from agents.state_machine_agent import StateMachineAgent
from state_machines.patient_profiler import PatientProfilerMachine


async def test_llm_state_execution():
    """Test that LLM can execute a state"""
    print("Testing LLM-Powered State Execution...")
    print("=" * 60)
    
    # Create patient profiler
    profiler = PatientProfilerMachine()
    
    # Wrap with LLM agent
    agent = StateMachineAgent(profiler, model="gpt-4o")
    
    print(f"\n📋 Current State: {profiler.get_current_state().name}")
    print(f"📝 Instruction Preview:")
    instruction = agent.get_current_instruction()
    print(f"   {instruction[:150]}...")
    
    # Test with sample medical text
    sample_input = """
    Patient is a 58-year-old female presenting with stage IIIB non-small cell lung cancer.
    ECOG performance status is 1. No mention of pregnancy.
    """
    
    print(f"\n🤖 Asking LLM to extract demographics from:")
    print(f"   {sample_input.strip()}")
    
    try:
        result = await agent.execute_state(sample_input)
        
        print(f"\n✅ State Executed Successfully!")
        print(f"   State: {result['state']}")
        print(f"   LLM Response: {result['llm_response'][:200]}...")
        print(f"   Next State: {result['next_state']}")
        
        # Check that memory was updated
        if 'demographics' in profiler.global_memory:
            print(f"\n✅ Global Memory Updated!")
            print(f"   Memory keys: {list(profiler.global_memory.keys())}")
        
        # Check state transition
        current = profiler.get_current_state()
        if current and current.name == 'extract_diagnoses':
            print(f"\n✅ State Transition Successful!")
            print(f"   Now at: {current.name}")
        
        print("\n" + "=" * 60)
        print("✅ LLM STATE INTEGRATION TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_llm_state_execution())
    if not success:
        print("\n⚠️  Test failed - check your API key and connection")