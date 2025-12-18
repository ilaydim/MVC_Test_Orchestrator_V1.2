import json
from typing import List, Dict, Any
from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K


class ControllerArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the CONTROLLER layer
    from an SRS document.
    
    It reads structured entities and functions from previous agents (Requirements/Model)
    to perform a targeted RAG search on user interactions and workflows.
    """
    
    def _load_analysis(self, filename: str) -> Dict[str, Any]:
            """Loads structured JSON output from a previous agent."""
            analysis_path = self.data_dir / filename
            
            # Dosya Var mı Kontrolü
            if not analysis_path.exists():
                raise FileNotFoundError(
                    f"FATAL ERROR: ControllerAgent could not find dependency file: {filename}. "
                    "Ensure preceding agent ran successfully and saved the file to /data."
                )
            
            # JSON Formatı Kontrolü
            try:
                with open(analysis_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                # LLM'den gelen JSON'un bozuk olduğunu gösterir.
                raise ValueError(
                    f"FATAL ERROR: Could not decode JSON in {filename}. "
                    f"LLM produced malformed JSON. Error: {e}"
                )
    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_controllers(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Extracts CONTROLLER-level logic from SRS using targeted RAG based on 
        extracted functions and models.
        """
        
        # 1. Load data from preceding agents
        requirements_data = self._load_analysis("requirements_analysis.json")
        model_data = self._load_analysis("model_architecture.json")
        
        # Extract function list from Requirements Agent
        functions = [f['name'] for f in requirements_data.get('system_functions', [])]
        
        # Extract entity list from Model Agent's output (which should be more refined)
        entities = [m['name'] for m in model_data.get('model', [])]
        
        # Determine RAG query focus
        functions_list = ", ".join(functions) if functions else "system actions"
        entities_list = ", ".join(entities) if entities else "core data models"

        # 2. Refine RAG Query using extracted structure (Targeted RAG)
        query = (
            f"For the high-level functions: [{functions_list}] and the data models: [{entities_list}], "
            "identify all user interactions, workflows, and specific controller "
            "responsibilities (actions) described in the SRS. Focus on the flow."
        )

        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for controller extraction.")

        # Build controller-specific prompt
        prompt = self._build_controller_prompt(chunks)

        controller_json = self.llm_json(prompt)

        self.save_output(controller_json, "controller_architecture.json")

        return controller_json


    def _build_controller_prompt(self, chunks: List[str]) -> str:
        """
        Builds clean and minimal prompt for extracting CONTROLLER layer.
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[3] / ".github" / "prompts" / "extract_controller_architecture.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Replace variables in template
        prompt = prompt_template.replace("{{context}}", context)
        
        return prompt