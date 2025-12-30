# src/agents/architect_agent/base_architect_agent.py
import time

from pathlib import Path
from typing import List, Optional
from google.api_core import exceptions as google_exceptions

from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient
from src.core.config import DEFAULT_TOP_K


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

    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.rag = rag_pipeline or RAGPipeline()
        self.llm = llm_client or LLMClient()
        self.current_document: Optional[str] = None

        project_root = Path(__file__).resolve().parents[3] 
        self.data_dir = project_root / "data" 
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
    # Chunk Retrieval Helper 
    # ----------------------------------------------------------------------
    def retrieve_chunks(self, query: str, k: int = DEFAULT_TOP_K) -> List[str]:
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

        return documents[0]

    # ----------------------------------------------------------------------
    # Save JSON Outputs
    # ----------------------------------------------------------------------
    def save_output(self, data: dict, filename: str):
        """
        Saves JSON outputs into the /data directory.
        Every architect agent (model/view/controller/orchestrator) can use this to persist results.
        Also creates a corresponding .md file.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.data_dir / filename

        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Also create a markdown file
        if filename.endswith('.json'):
            md_filename = filename.replace('.json', '.md')
            md_path = self.data_dir / md_filename
            md_content = self._json_to_markdown(data, filename)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

        return output_path
    
    def _json_to_markdown(self, data: dict, filename: str) -> str:
        """
        Converts JSON data to a readable markdown format.
        """
        lines = []
        
        # Add title based on filename
        title = filename.replace('.json', '').replace('_', ' ').title()
        lines.append(f"# {title}\n\n")
        
        # Helper function to recursively convert JSON to markdown
        def process_value(key, value, level=0):
            key_title = key.replace('_', ' ').title() if key else ""
            
            if isinstance(value, dict):
                if key:
                    lines.append(f"{'#' * (level + 2)} {key_title}\n\n")
                for sub_key, sub_value in value.items():
                    process_value(sub_key, sub_value, level + 1)
                if key:
                    lines.append("\n")
                    
            elif isinstance(value, list):
                # Check if list contains only simple types (no dicts)
                has_dicts = any(isinstance(item, dict) for item in value)
                
                if has_dicts:
                    # List of objects - create header and process each object
                    if key:
                        lines.append(f"{'#' * (level + 2)} {key_title}\n\n")
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            # For list of objects, create a subsection
                            if 'name' in item:
                                item_name = item.get('name', f'Item {idx + 1}')
                                lines.append(f"{'#' * (level + 3)} {item_name}\n\n")
                            else:
                                lines.append(f"{'#' * (level + 3)} Item {idx + 1}\n\n")
                            # Add all key-value pairs from the object
                            for sub_key, sub_value in item.items():
                                process_value(sub_key, sub_value, level + 1)
                            lines.append("\n")
                    if key:
                        lines.append("\n")
                else:
                    # List of simple values - print as bullet points
                    if key:
                        lines.append(f"**{key_title}:**\n")
                    for item in value:
                        lines.append(f"- {item}\n")
                    lines.append("\n")
            else:
                if value is not None and value != "":
                    lines.append(f"- **{key_title}**: {value}\n")
        
        # Process top-level dictionary
        for key, value in data.items():
            process_value(key, value, level=0)
        
        return "".join(lines)
    
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
    def llm_json(self, prompt: str, max_retries: int = 3) -> dict:
        """
        Sends a prompt to LLM and parses the returned JSON using parse_json().
        Automatically retries on 429 quota errors with API-suggested delay.
        """
        time.sleep(12)
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.model.generate_content(prompt)
                text = response.text.strip()
                return self.parse_json(text)
                
            except google_exceptions.ResourceExhausted as e:
                last_exception = e
                retry_delay = 30
                
                if hasattr(e, 'retry_delay') and e.retry_delay:
                    if hasattr(e.retry_delay, 'total_seconds'):
                        retry_delay = e.retry_delay.total_seconds()
                    elif hasattr(e.retry_delay, 'seconds'):
                        retry_delay = float(e.retry_delay.seconds)
                
                if retry_delay == 30:
                    import re
                    error_str = str(e)
                    match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str, re.IGNORECASE)
                    if match:
                        retry_delay = float(match.group(1))
                    else:
                        match = re.search(r'retry_delay.*?seconds.*?(\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
                        if match:
                            retry_delay = float(match.group(1))
                
                if attempt < max_retries - 1:
                    print(f"[BaseArchitectAgent] Quota exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s before retry...")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(
                        f"Gemini API quota exceeded after {max_retries} attempts. "
                        f"Please wait and try again later. Last error: {e}"
                    )
                    
            except Exception as e:
                if "JSON" in str(e) or "parse" in str(e).lower():
                    raise
                raise ConnectionError(f"LLM API call failed: {e}")
        
        if last_exception:
            raise ConnectionError(f"LLM API call failed after {max_retries} attempts: {last_exception}")
        raise ConnectionError("Unexpected error in llm_json")