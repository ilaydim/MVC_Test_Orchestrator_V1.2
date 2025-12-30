import json
from typing import List, Dict, Any
from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K


class ModelArchitectAgent(BaseArchitectAgent):
    """
    Specialized architect agent responsible for extracting the MODEL layer
    from an SRS document.
    
    It first reads the structured entities from the Requirements Agent's 
    output to perform a more targeted RAG search.
    """

    def _load_analysis(self, filename: str = "requirements_analysis.json") -> Dict[str, Any]:
        """Loads structured JSON output from a previous agent (Requirements Agent)."""
        analysis_path = self.data_dir / filename
        if not analysis_path.exists():
            raise FileNotFoundError(
                f"Required analysis file not found: {filename}. "
                "Ensure RequirementsAgent has run successfully."
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
    def extract_models(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        High-level method for extracting model architecture using targeted RAG.
        """

        analysis_data = self._load_analysis()
        entities = [e['name'] for e in analysis_data.get('domain_entities', [])]
        
        if not entities:
            entities_list = "core domain entities"
        else:
            entities_list = ", ".join(entities)
        query = (
            f"For the specific domain entities: [{entities_list}], identify their concrete "
            "attributes, required fields, and relationships described in the SRS. "
            "Focus strictly on data structure definition."
        )

        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for model extraction.")

        prompt = self._build_model_prompt(chunks)
        model_json = self.llm_json(prompt)
        self.save_output(model_json, "model_architecture.json")

        return model_json

    def _build_model_prompt(self, chunks: List[str]) -> str:
        """
        Builds the prompt for extracting the MODEL layer.
        """

        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[3] / ".github" / "prompts" / "extract_model_architecture.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Replace variables in template
        prompt = prompt_template.replace("{{context}}", context)
        
        return prompt