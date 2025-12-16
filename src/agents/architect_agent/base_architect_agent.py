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

        #It splits the PDF into chunks and extracts the embeddings. It puts them in the embedding store.
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
        429 quota hatalarında otomatik retry yapar (API'nin önerdiği delay ile).
        """
        # Rate limiting için kısa bir delay (her çağrı arasında)
        time.sleep(12)
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.model.generate_content(prompt)
                text = response.text.strip()
                return self.parse_json(text)
                
            except google_exceptions.ResourceExhausted as e:
                # 429 quota hatası - API'nin önerdiği delay'i kullan
                last_exception = e
                
                # Retry delay'i exception'dan al (eğer varsa)
                retry_delay = 30  # varsayılan 30 saniye
                
                # Önce exception'un retry_delay attribute'unu kontrol et
                if hasattr(e, 'retry_delay') and e.retry_delay:
                    if hasattr(e.retry_delay, 'total_seconds'):
                        retry_delay = e.retry_delay.total_seconds()
                    elif hasattr(e.retry_delay, 'seconds'):
                        retry_delay = float(e.retry_delay.seconds)
                
                # Eğer bulamadıysak, exception mesajından parse etmeye çalış
                if retry_delay == 30:
                    import re
                    error_str = str(e)
                    # "Please retry in 46.96s" formatını yakala
                    match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str, re.IGNORECASE)
                    if match:
                        retry_delay = float(match.group(1))
                    else:
                        # "retry_delay { seconds: 46 }" formatını yakala
                        match = re.search(r'retry_delay.*?seconds.*?(\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
                        if match:
                            retry_delay = float(match.group(1))
                
                if attempt < max_retries - 1:
                    print(f"[BaseArchitectAgent] Quota exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s before retry...")
                    time.sleep(retry_delay)
                else:
                    # Son deneme de başarısız oldu
                    raise ConnectionError(
                        f"Gemini API quota exceeded after {max_retries} attempts. "
                        f"Please wait and try again later. Last error: {e}"
                    )
                    
            except Exception as e:
                # JSON parse hatası veya diğer hatalar için retry yapma
                if "JSON" in str(e) or "parse" in str(e).lower():
                    raise  # JSON parse hatası için direkt fırlat
                # Diğer hatalar için de direkt fırlat
                raise ConnectionError(f"LLM API call failed: {e}")
        
        # Buraya gelmemeli ama güvenlik için
        if last_exception:
            raise ConnectionError(f"LLM API call failed after {max_retries} attempts: {last_exception}")
        raise ConnectionError("Unexpected error in llm_json")