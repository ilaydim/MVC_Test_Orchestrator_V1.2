# src/agents/srs_writer_agent.py

from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Agent'ın miras aldığı Base Agent'ı import edin. 
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.llm_client import QuotaExceededError, LLMConnectionError

class SRSWriterAgent(BaseArchitectAgent):
    """
    Generates the Software Requirements Specification (SRS) document based on the user's high-level idea.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        # BaseArchitectAgent'ın __init__ metodunu çağırır. 
        super().__init__(rag_pipeline, llm_client)
        # self.rag already exists from BaseArchitectAgent, no need for duplicate 

    
    def generate_srs(self, user_idea: str) -> Path:
        """
        Instructs the LLM to generate the SRS document, saves the output to the data/ folder, 
        and returns the file path.
        """
        import time
        
        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "create_srs.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Replace variables in template
        prompt = prompt_template.replace("{{user_idea}}", user_idea)
        
        # KODLAMA HATASINI ÖNLEMEK İÇİN LOG MESAJI SADELEŞTİRİLDİ (İngilizce ve Emojisiz)
        print("[SRS Writer] Generating SRS text...")
        print(f"⏱️  Estimated time: ~15-30 seconds")
        
        start_time = time.time()
        
        try:
            srs_text = self.llm.generate_content(prompt, stream=False)  # stream=False for faster response
            elapsed = time.time() - start_time
            print(f"✓ Generated in {elapsed:.1f}s") 

        except QuotaExceededError as qe:
            # Kota doldu - pipeline'ı çökertme, kullanıcıya net mesaj ver
            print(f"\n{str(qe)}")
            print("[SRS Writer] Pipeline stopped gracefully. Please try again later.")
            raise  # Exception'ı yukarı fırlat (CLI catch etsin)
            
        except LLMConnectionError as lce:
            # Bağlantı hatası
            print(f"\n[SRS Writer ERROR] LLM connection failed: {lce}")
            print("[SRS Writer] Pipeline stopped. Check your network/API key.")
            raise
            
        except Exception as e:
            # Diğer beklenmeyen hatalar
            print(f"[SRS Writer ERROR] Unexpected error: {e}")
            raise


        # Dosya yolu oluşturma
        srs_filename = "srs_document.txt"
        srs_path = self.data_dir / srs_filename
        
        # KRİTİK DÜZELTME: encoding="utf-8" ile yazma işlemi zorunlu kılındı
        srs_path.write_text(srs_text, encoding="utf-8")
        
        # KODLAMA HATASINI ÖNLEMEK İÇİN LOG MESAJI SADELEŞTİRİLDİ
        print(f"[SRS Writer] SRS successfully created: {srs_path.name}")
        
        return srs_path