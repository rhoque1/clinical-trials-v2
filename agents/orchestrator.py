"""
Orchestrator Agent - The LLM Planner
Decides which state machines to use and manages the workflow
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class WorkflowMode(Enum):
    """User interaction modes"""
    WIZARD = "wizard"      # Step-by-step for beginners
    EXPRESS = "express"    # Automated for professionals
    RESEARCH = "research"  # Advanced analysis mode


class Orchestrator:
    """
    Main coordinator that decides the workflow based on user request
    Similar to CRISPR-GPT's LLM Planner
    """
    
    def __init__(self, mode: WorkflowMode = WorkflowMode.WIZARD):
        self.mode = mode
        self.available_machines = {
            "patient_profiler": "Extract patient information from medical reports",
            "trial_discovery": "Search and filter clinical trials",
            "eligibility_analyzer": "Detailed eligibility matching",
            "clinical_advisor": "Generate recommendations and guidance"
        }
        self.workflow_plan: List[str] = []
        self.current_machine_index = 0
    
    def plan_workflow(self, user_request: str) -> List[str]:
        """
        Analyze user request and determine which state machines to use
        In v2, this will use LLM reasoning. For now, use rules.
        """
        workflow = []
        
        # Simple rule-based planning (will be LLM-powered later)
        request_lower = user_request.lower()
        
        # Always start with patient profiling if PDF mentioned
        if "pdf" in request_lower or "report" in request_lower or "analyze" in request_lower:
            workflow.append("patient_profiler")
        
        # Add trial discovery if searching for trials
        if "trial" in request_lower or "study" in request_lower or "find" in request_lower:
            workflow.append("trial_discovery")
        
        # Add eligibility if detailed matching requested
        if "eligib" in request_lower or "qualify" in request_lower or "match" in request_lower:
            workflow.append("eligibility_analyzer")
        
        # Always end with advisor for recommendations
        workflow.append("clinical_advisor")
        
        self.workflow_plan = workflow
        return workflow
    
    def get_current_machine(self) -> Optional[str]:
        """Get the current state machine to execute"""
        if self.current_machine_index < len(self.workflow_plan):
            return self.workflow_plan[self.current_machine_index]
        return None
    
    def advance_to_next_machine(self):
        """Move to the next state machine in the workflow"""
        self.current_machine_index += 1
    
    def is_workflow_complete(self) -> bool:
        """Check if all state machines have been executed"""
        return self.current_machine_index >= len(self.workflow_plan)
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of planned workflow"""
        return {
            "mode": self.mode.value,
            "total_machines": len(self.workflow_plan),
            "current_step": self.current_machine_index + 1,
            "machines": self.workflow_plan,
            "current_machine": self.get_current_machine(),
            "complete": self.is_workflow_complete()
        }