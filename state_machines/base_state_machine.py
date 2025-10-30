"""
Base State Machine implementation
Inspired by CRISPR-GPT's state machine architecture
"""
from typing import Dict, Any, Optional, List
from enum import Enum


class StateStatus(Enum):
    """Status of state execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"


class State:
    """Represents a single state in the workflow"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = StateStatus.PENDING
        self.output = None
        self.memory = {}  # Stores data from this state
    
    def get_instruction(self, context: Dict[str, Any]) -> str:
        """Generate instruction for this state - override in subclasses"""
        raise NotImplementedError
    
    def process_input(self, user_input: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result - override in subclasses"""
        raise NotImplementedError
    
    def get_next_state(self) -> Optional[str]:
        """Determine next state - override in subclasses"""
        return None


class StateMachine:
    """
    Base state machine for managing workflow
    Each task is broken into states with memory inheritance
    """
    
    def __init__(self, name: str):
        self.name = name
        self.states: Dict[str, State] = {}
        self.current_state: Optional[str] = None
        self.global_memory: Dict[str, Any] = {}  # Shared across all states
        self.execution_history: List[Dict[str, Any]] = []
    
    def add_state(self, state: State, is_entry: bool = False):
        """Add a state to the machine"""
        self.states[state.name] = state
        if is_entry and self.current_state is None:
            self.current_state = state.name
            # Record initial state in history
            self.execution_history.append({
                "state": state.name,
                "timestamp": "now"
            })
    
    def get_current_state(self) -> Optional[State]:
        """Get current state object"""
        if self.current_state:
            return self.states.get(self.current_state)
        return None
    
    def transition_to(self, state_name: str):
        """Transition to a new state"""
        if state_name in self.states:
            self.current_state = state_name
            self.execution_history.append({
                "state": state_name,
                "timestamp": "now"  # We'll add proper timestamps later
            })
        else:
            raise ValueError(f"State '{state_name}' not found in machine '{self.name}'")
    
    def execute_current_state(self, user_input: Any) -> Dict[str, Any]:
        """Execute the current state with user input"""
        state = self.get_current_state()
        if not state:
            return {"error": "No current state"}
        
        # Process the state
        result = state.process_input(user_input, self.global_memory)
        
        # Update state memory
        state.memory.update(result)
        state.status = StateStatus.COMPLETED
        
        # Update global memory (inheritance)
        self.global_memory.update(result)
        
        # Determine next state
        next_state = state.get_next_state()
        if next_state:
            self.transition_to(next_state)
        else:
            # No next state - mark as complete by clearing current
            self.current_state = None
        
        return result
    
    def is_complete(self) -> bool:
        """Check if state machine has completed all states"""
        current = self.get_current_state()
        # Only complete if there's no current state at all
        # (meaning we've transitioned past the last state)
        return current is None