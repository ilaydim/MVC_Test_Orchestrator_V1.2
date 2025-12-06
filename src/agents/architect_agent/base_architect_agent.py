# src/agents/architect_agent/base_architect_agent.py

from pathlib import Path
from typing import List, Optional

from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient


class BaseArchitectAgent:
    """
    Base class providing shared functionality for all architect agents.
    This class does NOT perform any architecture extraction by itself.
    It only provides tools that specialized agents (model/view/controller)
    will use to do the actual domain-specific work.

    Responsibilities:
    - Manage access to RAGPipeline (document search, chunk retrieval)
    - Manage access to LLMClient (prompting + model calls)
    - Provide shared helper methods (e.g., retrieving context, saving outputs)
    """

    # Tüm architect-agent’larda ortak olacak RAG ve LLM bağlantısını kuruyor.Her agent, yeni bir pipeline/LLM yaratmak zorunda kalmıyor
    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None
    ):
        # RAGPipeline instance shared by all architect agents
        self.rag = rag_pipeline or RAGPipeline()

        # LLMClient instance shared by all architect agents
        self.llm = llm_client or LLMClient()

        # Tracks which document is currently indexed
        self.current_document: Optional[str] = None

        # Output directory for agents that want to save results
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    # ----------------------------------------------------------------------
    # PDF Indexing
    # ----------------------------------------------------------------------
    def index_pdf(self, file, chunk_size: Optional[int] = None, overlap: Optional[int] = None):
        """
        Indexes a PDF file into the RAG pipeline.
        Sub-agents inherit this method without duplicating logic.
        """
        info = self.rag.index_pdf(file, chunk_size=chunk_size, overlap=overlap)
        self.current_document = info["document_name"]
        return info

    # ----------------------------------------------------------------------
    # Chunk Retrieval Helper (simplified for single-document RAG pipeline)
    # ----------------------------------------------------------------------
    def retrieve_chunks(self, query: str, k: int = 6):
        """
        Retrieves top-k relevant chunks using the RAG pipeline.

        This simplified version assumes:
        - The UI indexes exactly one SRS PDF
        - All chunks live in a single Chroma collection
        - No explicit document filter is required
        """

        if self.rag is None:
            raise ValueError("RAG pipeline is not initialized.")

        result = self.rag.search(query, k=k)

        documents = result.get("documents") or []
        if not documents or not documents[0]:
            raise ValueError(
                f"RAG could not find relevant chunks for query: {query}"
            )

        # Chroma outputs as list-of-lists → return the first list.
        return documents[0]

    # ----------------------------------------------------------------------
    # Save JSON Outputs
    # ----------------------------------------------------------------------
    def save_output(self, data: dict, filename: str):
        """
        Saves JSON outputs into the /data directory.
        Every architect agent (model/view/controller/orchestrator)
        can use this to persist results.
        """
        output_path = self.data_dir / filename

        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return output_path

    # ----------------------------------------------------------------------
    # LLM Call Helper (Optional)
    # ----------------------------------------------------------------------
    def run_llm(self, prompt: str) -> str:
        """
        Sends a raw prompt to the LLM.
        Sub-agents typically build structured prompts before using this.
        """
        response = self.llm.model.generate_content(prompt)
        return response.text.strip()
    
    # ----------------------------------------------------------------------
    # JSON Parsing Helper
    # ----------------------------------------------------------------------
    def parse_json(self, text: str) -> dict:
        """
        Cleans LLM output by removing code fences and parses JSON safely.
        Used by all architect agents (model, view, controller).
        """
        cleaned = text.strip()

        # Remove code fences
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "").strip()

        import json
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON.\nError: {e}\nRaw snippet:\n{cleaned[:300]}"
            )

    # ----------------------------------------------------------------------
    # LLM JSON Wrapper (High-Level)
    # ----------------------------------------------------------------------
    def llm_json(self, prompt: str) -> dict:
        """
        Sends a prompt to LLM and parses the returned JSON using parse_json().
        """
        response = self.llm.model.generate_content(prompt)
        text = response.text.strip()
        return self.parse_json(text)