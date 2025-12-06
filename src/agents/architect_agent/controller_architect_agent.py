# src/agents/architect_agent/controller_architect_agent.py

from typing import List, Dict, Any
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent


class ControllerArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the CONTROLLER layer
    from an SRS document.

    Focuses on:
    - user actions / events
    - system behavior / workflows
    - controller responsibilities
    - interactions with models and views
    - validation and processing rules
    """

    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_controllers(self, k: int = 6) -> Dict[str, Any]:
        """
        Extracts CONTROLLER-level logic from SRS:
        user actions, workflows, input/output, system responses.
        """

        query = (
            "Identify all system actions, workflows, user interactions, and controller "
            "responsibilities described in this software requirements specification."
        )

        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for controller extraction.")

        # Build controller-specific prompt
        prompt = self._build_controller_prompt(chunks)

        # Use BaseArchitectAgent's llm_json() for structured output
        controller_json = self.llm_json(prompt)

        # Save final result
        self.save_output(controller_json, "controller_architecture.json")

        return controller_json

    # ----------------------------------------------------------------------
    # Prompt Engineering
    # ----------------------------------------------------------------------
    def _build_controller_prompt(self, chunks: List[str]) -> str:
        """
        Builds clean and minimal prompt for extracting CONTROLLER layer.
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        return f"""
    You are a backend software architect.
    Extract ONLY the CONTROLLERS and their ACTIONS.

    ### VERY IMPORTANT RULES:
    - Each controller has:
        - name  (e.g., "UserController")
        - actions (list of strings, e.g. ["login", "register"])
    - DO NOT include inputs, outputs, parameters.
    - DO NOT include descriptions of actions.
    - DO NOT include next views.
    - DO NOT include model operations.
    - DO NOT infer CRUD automatically unless SRS clearly defines it.
    - KEEP THE OUTPUT MINIMAL.
    - NO repetition of controller names.

    ### STRICT JSON FORMAT (NO COMMENTS, NO EXTRA TEXT):
    {{
      "controller": [
        {{
          "name": "SomeController",
          "actions": ["actionOne", "actionTwo"]
        }}
      ]
    }}

    ### SRS CONTEXT:
    {context}

    Return ONLY the JSON. No explanation.
    """

