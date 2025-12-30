import json
from typing import List, Dict, Any
from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K


class ViewArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the VIEW layer
    from an SRS document.
    
    It reads structured outputs from Model and Controller agents to design
    UI components (Views) that are consistent with the application's data
    (Models) and business logic (Controllers).
    """

    def _load_analysis(self, filename: str) -> Dict[str, Any]:
        """Loads structured JSON output from a previous agent."""
        analysis_path = self.data_dir / filename
        if not analysis_path.exists():
            raise FileNotFoundError(
                f"Required analysis file not found: {filename}. "
                "Ensure preceding agents have run successfully."
            )
        try:
            with open(analysis_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Could not decode JSON in {filename}. "
                f"LLM produced malformed JSON. Error: {e}"
            )

    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_views(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Extracts VIEW-layer architecture using targeted RAG based on 
        extracted Models and Controllers.
        """

        model_data = self._load_analysis("model_architecture.json")
        controller_data = self._load_analysis("controller_architecture.json")

        entities = [m['name'] for m in model_data.get('model', [])]
        
        controller_actions = []
        for ctrl in controller_data.get('controller', []):
            ctrl_name = ctrl.get('name', 'UnnamedController')
            actions = ctrl.get('actions', [])
            controller_actions.extend([f"{ctrl_name}.{a}" for a in actions])

        entities_list = ", ".join(entities) if entities else "core data models"
        actions_list = ", ".join(controller_actions) if controller_actions else "system actions"

        query = (
            f"For the data models: [{entities_list}] and the actions: [{actions_list}], "
            "identify all user interfaces, screens, components, and "
            "navigation flows described in the SRS. Focus on data presentation and action triggering."
        )

        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for view-layer extraction.")

        prompt = self._build_view_prompt(chunks)
        view_json = self.llm_json(prompt)

        # Save output into /data folder
        self.save_output(view_json, "view_architecture.json")

        return view_json

    def _build_view_prompt(self, chunks: List[str]) -> str:
        """
        Builds clean and minimal prompt for extracting VIEW layer.
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[3] / ".github" / "prompts" / "extract_view_architecture.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Replace variables in template
        prompt = prompt_template.replace("{{context}}", context)
        
        return prompt