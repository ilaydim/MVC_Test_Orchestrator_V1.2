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
        context = ""
        for i, c in enumerate(chunks):
            context += f"\n\n--- SRS Chunk {i+1} ---\n{c}\n"

        json_schema = self._get_json_schema_definition()
        json_schema_str = json.dumps(json_schema, indent=2)

        return f"""
You are a Requirements Engineer AI. Your task is to analyze the provided SRS context
and extract the high-level domain structure required for an MVC application.
        
### GOAL:
Extract ALL fundamental domain entities (Model layer) and ALL high-level
system functionalities/workflows (Controller layer).
        
### VERY IMPORTANT RULES:
- The output MUST strictly adhere to the provided JSON Schema.
- Entities should focus on *data* that needs to be stored or managed (e.g., User, Product).
- System Functions should focus on *actions* the system performs (e.g., registerUser, updateStock).
- DO NOT invent entities or functions. Extract ONLY what is clearly mentioned or implied in the context.
        
### STRICT JSON FORMAT (NO COMMENTS, NO EXTRA TEXT, NO CODE FENCES):
{json_schema_str}
        
### SRS CONTEXT:
{context}

Return ONLY the JSON. No explanation, no introduction.
"""