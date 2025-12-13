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
        with open(analysis_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_views(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Extracts VIEW-layer architecture using targeted RAG based on 
        extracted Models and Controllers.
        """

        # 1. Load data from preceding agents
        model_data = self._load_analysis("model_architecture.json")
        controller_data = self._load_analysis("controller_architecture.json")

        # Extract required lists
        entities = [m['name'] for m in model_data.get('model', [])]
        
        # Extract actions and merge them for a clearer prompt
        controller_actions = []
        for ctrl in controller_data.get('controller', []):
            ctrl_name = ctrl.get('name', 'UnnamedController')
            actions = ctrl.get('actions', [])
            controller_actions.extend([f"{ctrl_name}.{a}" for a in actions])

        # Determine RAG query focus
        entities_list = ", ".join(entities) if entities else "core data models"
        actions_list = ", ".join(controller_actions) if controller_actions else "system actions"

        # 2. Refine RAG Query using extracted structure (Targeted RAG)
        query = (
            f"For the data models: [{entities_list}] and the actions: [{actions_list}], "
            "identify all user interfaces, screens, components, and "
            "navigation flows described in the SRS. Focus on data presentation and action triggering."
        )

        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for view-layer extraction.")

        # Build domain-specific prompt
        prompt = self._build_view_prompt(chunks)

        # Run LLM → parse JSON automatically using BaseArchitectAgent
        view_json = self.llm_json(prompt)

        # Save output into /data folder
        self.save_output(view_json, "view_architecture.json")

        return view_json

    def _build_view_prompt(self, chunks: List[str]) -> str:
        """
        Builds clean and minimal prompt for extracting VIEW layer.
        (Mevcut prompt yapısı korunmuştur.)
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        return f"""
You are a senior UI/UX architect.
Extract ONLY the names of SCREENS / PAGES described in the SRS.

### VERY IMPORTANT RULES:
- Each view has ONLY:
    - name
    - short description
- DO NOT include UI widgets.
- DO NOT include buttons, sliders, forms, inputs.
- DO NOT include navigation information.
- DO NOT include user roles.
- DO NOT include components.
- KEEP THE OUTPUT MINIMAL.

### STRICT JSON FORMAT (NO COMMENTS, NO EXTRA TEXT):
{{
  "view": [
    {{"name": "ScreenName", "description": "Short description."}}
  ]
}}

### SRS CONTEXT:
{context}

Return ONLY the JSON. No explanation.
"""