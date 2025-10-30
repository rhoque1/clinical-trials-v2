"""
System configuration for Clinical Trial Matching v2.0
Defines architecture modes and core settings
"""

class SystemConfig:
    """Central configuration for the enhanced system"""
    
    # API Configuration
    CLINICALTRIALS_API_BASE = "https://clinicaltrials.gov/api/v2/studies"
    API_TIMEOUT = 30
    MAX_STUDIES_PER_SEARCH = 100
    
    # System Mode
    MODE = "wizard"  # Options: "wizard", "express", "research"
    
    # Architecture version
    VERSION = "2.0"
    
    # Model Configuration
    DEFAULT_MODEL = "gpt-4o"
    FAST_MODEL = "gpt-3.5-turbo"
    
    # Feature Flags (we'll enable these incrementally)
    FEATURES = {
        "state_machines": False,      # Step 1: Will implement first
        "fine_tuned_model": False,    # Step 2: Later
        "rag_system": False,          # Step 3: Later
        "multi_agent_v2": False,      # Step 4: Enhanced agents
        "safety_guardrails": False,   # Step 5: Safety layer
    }