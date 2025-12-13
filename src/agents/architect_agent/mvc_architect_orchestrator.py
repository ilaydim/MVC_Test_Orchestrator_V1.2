# src/agents/architect_agent/mvc_architect_orchestrator.py

from typing import Dict, Any

from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.core.config import DEFAULT_TOP_K


class MVCArchitectOrchestrator:
    """
    Unified orchestrator used by both UI and CLI layers.
    Produces consistent architecture JSON in the format:

    {
        "model": [...],
        "view": [...],
        "controller": [...]
    }
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        self.requirements_agent = RequirementsAgent(rag_pipeline, llm_client)
        self.model_agent = ModelArchitectAgent(rag_pipeline, llm_client)
        self.controller_agent = ControllerArchitectAgent(rag_pipeline, llm_client)
        self.view_agent = ViewArchitectAgent(rag_pipeline, llm_client)

    # ----------------------------------------------------------------------
    # Unified Architecture Extraction
    # ----------------------------------------------------------------------
    def extract_full_architecture(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Runs all architect agents and merges outputs into a unified JSON map.
        """
        requirements_analysis = self.requirements_agent.extract_analysis(k=k)      
        model_json = self.model_agent.extract_models(k=k)
        controller_json = self.controller_agent.extract_controllers(k=k)
        view_json = self.view_agent.extract_views(k=k)

        architecture_map = {
            "model": model_json.get("model", []),
            "view": view_json.get("view", []),
            "controller": controller_json.get("controller", []),
        }

        # Save output for CLI calls
        self.model_agent.save_output(architecture_map, "architecture_map.json")

        return architecture_map
