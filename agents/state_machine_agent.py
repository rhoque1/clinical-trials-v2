"""
LLM-Powered State Machine Agent
Bridges state machines with LLM reasoning (autogen)
"""
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from state_machines.base_state_machine import StateMachine, State

load_dotenv()


class StateMachineAgent:
    """
    Wraps a state machine with an LLM agent
    The LLM executes each state's instructions
    """
    
    def __init__(self, state_machine: StateMachine, model: str = "gpt-4o"):
        self.state_machine = state_machine
        self.model = model
        
        # Create the LLM client
        api_key = os.getenv("open_ai")
        self.model_client = OpenAIChatCompletionClient(
            model=model,
            api_key=api_key
        )
        
        # We'll create agent per state as needed
        self.current_agent: Optional[AssistantAgent] = None
    
    def _create_agent_for_state(self, state: State) -> AssistantAgent:
        """Create an LLM agent configured for the current state"""
        
        # Get the instruction with current memory context
        instruction = state.get_instruction(self.state_machine.global_memory)
        
        # Special handling for search terms generation
        if state.name == "generate_search_terms":
            system_message = f"""
You are a medical information specialist generating clinical trial search terms.

{instruction}

CRITICAL RULES:
1. Return ONLY search terms related to the medical condition
2. DO NOT return patient demographics (age, gender, etc.)
3. Focus on: disease names, biomarkers, cancer stages, treatment types
4. One term per line
5. No formatting, bullets, or numbers

Example OUTPUT FORMAT:
cervical squamous cell carcinoma PIK3CA
stage IIIB cervical cancer
HPV-positive cervical cancer
cervical carcinoma PD-L1
gynecologic malignancy

Now generate search terms based on the context provided.
"""
        else:
            system_message = f"""
You are executing state: {state.name}

{instruction}

CRITICAL: Extract the requested information in a structured format.
Be concise and accurate. Focus only on what's asked.
"""
        
        agent = AssistantAgent(
            name=f"agent_{state.name}",
            model_client=self.model_client,
            system_message=system_message
        )
        
        return agent
    
    async def execute_state(self, input_data: str) -> Dict[str, Any]:
        """
        Execute current state with LLM reasoning
        
        Args:
            input_data: User input or context for this state
            
        Returns:
            Result from state execution
        """
        current_state = self.state_machine.get_current_state()
        if not current_state:
            return {"error": "No current state"}
        
        # DEBUG: Show what we're passing to the LLM
        if current_state.name == "generate_search_terms":
            print(f"\n[SEARCH] DEBUG - Search Terms State:")
            print(f"   Task input: {input_data[:200]}...")
            print(f"   Memory keys: {list(self.state_machine.global_memory.keys())}")
            print(f"   Diagnoses: {str(self.state_machine.global_memory.get('diagnoses', ''))[:100]}...")
            print(f"   Biomarkers: {str(self.state_machine.global_memory.get('biomarkers', ''))[:100]}...")
        
        # Create agent for this state
        agent = self._create_agent_for_state(current_state)
        
        # Get LLM response
        response = await agent.run(task=input_data)
        
        # Extract the response content
        if hasattr(response, 'messages') and response.messages:
            last_message = response.messages[-1]
            llm_output = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            llm_output = str(response)
        
        # DEBUG: Show what LLM returned
        if current_state.name == "generate_search_terms":
            print(f"   LLM Output: {llm_output[:200]}...")
        
        # Execute the state with LLM's output
        result = self.state_machine.execute_current_state(llm_output)
        
        return {
            "state": current_state.name,
            "llm_response": llm_output,
            "state_result": result,
            "next_state": self.state_machine.get_current_state().name if self.state_machine.get_current_state() else None
        }
    def get_current_instruction(self) -> Optional[str]:
        """Get instruction for current state"""
        state = self.state_machine.get_current_state()
        if state:
            return state.get_instruction(self.state_machine.global_memory)
        return None
    
    def is_complete(self) -> bool:
        """Check if state machine is complete"""
        return self.state_machine.is_complete()