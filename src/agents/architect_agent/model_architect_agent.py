# src/agents/architect_agent/model_architect_agent.py

from typing import List, Dict, Any
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K


class ModelArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the MODEL layer
    from an SRS document.
    Focuses on:
    - entities (data models)
    - attributes (fields)
    - relationships (1-to-1, 1-to-many, many-to-many)
    """

    # ----------------------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------------------
    def extract_models(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        High-level method for extracting model architecture.
        """

        # Retrieve SRS chunks relevant to model extraction
        query = (
            "Identify all data entities, their attributes, and relationships "
            "described in this software requirements specification."
        )

        chunks = self.retrieve_chunks(query, k=k) #The query is converted to embedding, the nearest k chunks are taken

        if not chunks:
            raise ValueError("No relevant chunks found for model extraction.")

        # Build domain-specific prompt
        prompt = self._build_model_prompt(chunks)

        # Call LLM and automatically parse JSON using base agent
        model_json = self.llm_json(prompt)

        # Save output to /data for reuse by scaffolder
        self.save_output(model_json, "model_architecture.json")

        return model_json

    def _build_model_prompt(self, chunks: List[str]) -> str:
        """
        Builds clean and minimal prompt for extracting MODEL layer.
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        return f"""
    You are a senior software architect specialized in high-level domain modeling.
    Extract ONLY the *domain entities* from the SRS.

    ### VERY IMPORTANT RULES:
    - ONLY output entity names and a short description.
    - DO NOT include attributes.
    - DO NOT include fields.
    - DO NOT include database schemas.
    - DO NOT include relationships.
    - DO NOT infer extra fields.
    - DO NOT include UI, controller, or workflow descriptions.
    - KEEP THE OUTPUT MINIMAL.

    ### STRICT JSON FORMAT (NO COMMENTS, NO EXTRA TEXT):
    {{
      "model": [
        {{"name": "EntityName", "description": "Short description."}}
      ]
    }}

    ### SRS CONTEXT:
    {context}

    Return ONLY the JSON. No explanation.
    """

