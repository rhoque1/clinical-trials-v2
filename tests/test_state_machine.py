"""
Test the base state machine implementation
"""
import sys
sys.path.append('..')

from state_machines.base_state_machine import State, StateMachine, StateStatus


class SimpleState(State):
    """A simple test state that just echoes input"""
    
    def get_instruction(self, context):
        return f"Please provide input for {self.name}"
    
    def process_input(self, user_input, context):
        return {
            "processed": True,
            "input_received": user_input,
            "state_name": self.name
        }
    
    def get_next_state(self):
        # For testing, we'll manually control transitions
        return None


def test_state_machine():
    """Test basic state machine functionality"""
    print("Testing State Machine...")
    
    # Create a state machine
    sm = StateMachine("test_machine")
    
    # Add a state
    state1 = SimpleState("state_1", "First test state")
    sm.add_state(state1, is_entry=True)
    
    # Check initial state
    current = sm.get_current_state()
    assert current.name == "state_1", "Initial state should be state_1"
    print(f"[OK] Initial state set correctly: {current.name}")
    
    # Execute state with input
    result = sm.execute_current_state("test_input")
    assert result["processed"] == True, "State should process input"
    assert result["input_received"] == "test_input", "Should receive correct input"
    print(f"[OK] State execution successful: {result}")
    
    # Check memory inheritance
    assert "processed" in sm.global_memory, "Global memory should be updated"
    print(f"[OK] Global memory updated: {sm.global_memory}")
    
    # Check execution history
    assert len(sm.execution_history) == 1, "Should have 1 history entry"
    print(f"[OK] Execution history tracked: {sm.execution_history}")
    
    print("\n[OK] All state machine tests passed!")


if __name__ == "__main__":
    test_state_machine()