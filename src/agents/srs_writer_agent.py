# src/agents/srs_writer_agent.py

from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Agent'ın miras aldığı Base Agent'ı import edin. 
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent

class SRSWriterAgent(BaseArchitectAgent):
    """
    Generates the Software Requirements Specification (SRS) document based on the user's high-level idea.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        # BaseArchitectAgent'ın __init__ metodunu çağırır. 
        super().__init__(rag_pipeline, llm_client)
        # RAG nesnesine erişimi Orchestrator için kolaylaştırır.
        self.rag_pipeline = rag_pipeline 

    
    def generate_srs(self, user_idea: str) -> Path:
        """
        Instructs the LLM to generate the SRS document, saves the output to the data/ folder, 
        and returns the file path.
        """
        
        prompt = f"""
        You are an expert Software Requirements Analyst. Based on the user's high-level idea, 
        you must generate a detailed, technical SRS (Software Requirements Specification) document.

        The SRS document MUST include the following sections:
        1. Introduction and Purpose
        2. Functional Requirements (Including user stories)
        3. Non-Functional Requirements (Security, Performance, Usability)
        4. Data Model and Entities (Crucial for Model architecture)

        User Idea: "{user_idea}"

        Return ONLY the requirements text, including the sections and their content. Do not add any introductory or concluding remarks.
        """
        
        # KODLAMA HATASINI ÖNLEMEK İÇİN LOG MESAJI SADELEŞTİRİLDİ (İngilizce ve Emojisiz)
        print("[SRS Writer] Generating SRS text...") 
        
        try:
            srs_text = self.llm.generate_content(prompt) 

        except Exception as e:
            # Hata mesajı İngilizce ve sadeleştirildi
            print(f"[SRS Writer ERROR] Failed to get response from LLM: {e}")
            sys.exit(1)


        # Dosya yolu oluşturma
        srs_filename = "srs_document.txt"
        srs_path = self.data_dir / srs_filename
        
        # KRİTİK DÜZELTME: encoding="utf-8" ile yazma işlemi zorunlu kılındı
        srs_path.write_text(srs_text, encoding="utf-8")
        
        # KODLAMA HATASINI ÖNLEMEK İÇİN LOG MESAJI SADELEŞTİRİLDİ
        print(f"[SRS Writer] SRS successfully created: {srs_path.name}")
        
        return srs_path