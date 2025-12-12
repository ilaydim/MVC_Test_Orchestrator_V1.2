# src/agents/architect_agent/view_architect_agent.py

from typing import List, Dict, Any
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K


class ViewArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the VIEW layer
    from an SRS document.

    Focuses on:
    - user interfaces
    - screens / pages
    - components (forms, tables, lists, modals)
    - navigation structure
    - role-based visibility rules
    """

    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_views(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Extracts VIEW-layer architecture:
        screens, components, navigation, and UI behavior.
        """

        query = (
            "Identify all user interfaces, screens, pages, components, and "
            "navigation flows described in the software requirements specification."
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
