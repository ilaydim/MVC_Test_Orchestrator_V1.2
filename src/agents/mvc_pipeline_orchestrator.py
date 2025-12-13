import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from typing import Dict, Any

# Pipeline Başlangıç/Bitiş Agent'ları
from src.agents.srs_writer_agent import SRSWriterAgent 
from src.agents.rules_agent import RulesAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.coder_agent import CoderAgent

# Mimari Yönetici ve İskele
from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.agents.architect_agent.mvc_architect_orchestrator import MVCArchitectOrchestrator

from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder 
from src.core.config import DEFAULT_TOP_K # Varsayıyoruz


class MVCPipelineOrchestrator:
    """
    Manages the entire end-to-end pipeline:
    SRS Writing -> Architecture Extraction -> Scaffolding -> Auditing -> Coding.
    This acts as the main entry point for the VSC extension command.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        # 1. Initialization of all agents/components
        self.srs_writer_agent = SRSWriterAgent(rag_pipeline, llm_client)
        self.scaffolder = MVCScaffolder() 
        self.rules_agent = RulesAgent(rag_pipeline, llm_client)
        self.reviewer_agent = ReviewerAgent(rag_pipeline, llm_client)
        self.coder_agent = CoderAgent(rag_pipeline, llm_client)
        
        # 2. Architecture Sub-Orchestrator (handles sequential M->C->V extraction)
        self.architect_orchestrator = MVCArchitectOrchestrator(rag_pipeline, llm_client)

    
    def run_full_pipeline(self, user_idea: str, k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Executes the full chain of operations from user idea to completed code.
        """
        
        # PHASE 0: GENERATE SRS DOCUMENT (SRS Writer)
        print("PHASE 0: Generating SRS document...")
        srs_path = self.srs_writer_agent.generate_srs(user_idea)
        
        # PHASE 0.5: INDEXING (RAG Pipeline) - CRITICAL FOR RAG SUCCESS
        print(f"PHASE 0.5: Indexing generated SRS file: {srs_path.name} for RAG...")
        try:
            # KRİTİK DÜZELTME: index_text_file yerine index_srs kullanıldı. 
            # Bu metot, RAGPipeline sınıfında (SRS'i .txt olarak işleyen) doğru metot adıdır.
            rag_instance = self.srs_writer_agent.rag_pipeline
            
            if rag_instance is None:
                 raise ValueError("RAGPipeline instance is None. Check Orchestrator initialization in CLI.")

            rag_instance.index_srs(srs_path) # <-- Düzeltildi
            
            print("Indexing successful.")
        except Exception as e:
            # RAG Indexleme hatasını burada yakalamalıyız.
            print(f"FATAL RAG INDEXING ERROR: {e}")
            # Hata oluşursa mimariyi çıkarmaya devam etmenin anlamı yoktur.
            return {"status": "FAILED", "reason": f"RAG Indexing Failed: {e}"}

        # PHASE 1 & 2: ARCHITECTURE EXTRACTION (MVCArchitectOrchestrator)
        print("PHASE 1-2: Extracting sequential MVC Architecture...")
        # Mimariyi çıkarır (çıktıyı architecture_map.json'a kaydeder)
        architecture_map = self.architect_orchestrator.extract_full_architecture(k=k)
        
        # PHASE 3: SCAFFOLD GENERATION (MVCScaffolder)
        print("PHASE 3: Generating skeleton files (Scaffolding)...")
        scaffold_result = self.scaffolder.scaffold_all(architecture_map)
        
        # PHASE 4: AUDIT AND QUALITY CHECK (Rules & Reviewer Agents)
        print("PHASE 4: Running Quality Audit...")
        scaffold_root = self.scaffolder.scaffold_root
        
        # 4a. Rules Agent: Teknik ihlalleri tespit eder.
        technical_violations = self.rules_agent.detect_violations(scaffold_root)
        
        # 4b. Reviewer Agent: İhlalleri doğal dil önerilerine çevirir.
        final_audit_report = self.reviewer_agent.generate_audit_report(technical_violations)
        
        # PHASE 5: CODE GENERATION (Coder Agent)
        print("PHASE 5: Generating functional code logic...")
        self.coder_agent.generate_code()
        
        # Nihai çıktı raporu ve başarı durumunu döndürelim
        return {
            "status": "COMPLETED",
            "audit_result": final_audit_report,
            "scaffold_path": str(scaffold_result)
        }