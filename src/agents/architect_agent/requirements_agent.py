import json
from typing import Dict, Any, List

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.config import DEFAULT_TOP_K 


class RequirementsAgent(BaseArchitectAgent):
    """
    Analyzes the retrieved chunks from the SRS document to extract a structured 
    list of core domain entities and high-level system functions.
    
    This structured output is saved to 'requirements_analysis.json' and is used 
    by subsequent specialized agents (Model/Controller) to perform highly 
    targeted RAG queries, mitigating information loss.
    """

    def _get_json_schema_definition(self) -> Dict[str, Any]:
        """Defines the structured output format expected from the LLM."""
        return {
            "project_name": "Short, single-word project identifier (e.g., ECommerce)",
            "domain_entities": [
                {
                    "name": "Core Entity Name (e.g., User, Product, Order)",
                    "purpose": "The primary role of the entity and data it represents (1 sentence)",
                }
            ],
            "system_functions": [
                {
                    "name": "High-Level Function Name (e.g., placeOrder, loginUser)",
                    "description": "The high-level business workflow performed by this function (1 sentence)",
                }
            ]
        }
        
    def extract_analysis(self, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Extracts structured requirements by performing a general RAG query and 
        asking the LLM to structure the content.
        """
        
        query = (
            "Analyze the entire document and extract the core domain entities and "
            "all high-level system functions/workflows described. Focus on the 'what' and 'who'."
        )
        
        chunks = self.retrieve_chunks(query, k=k)

        if not chunks:
            raise ValueError("No relevant chunks found for requirements analysis.")

        prompt = self._build_requirements_prompt(chunks)

        analysis_json = self.llm_json(prompt)

        self.save_output(analysis_json, "requirements_analysis.json")

        return analysis_json


    def _build_requirements_prompt(self, chunks: List[str]) -> str:
        """
        Builds the detailed LLM prompt for extracting structured requirements.
        """
        from pathlib import Path
        
        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[3] / ".github" / "prompts" / "extract_requirements.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Replace variables in template
        prompt = prompt_template.replace("{{context}}", context)
        
        return prompt