import os
import sys
from typing import Dict, Any 
from pathlib import Path 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


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
    SRS Writing -> Architecture Extraction -> Scaffolding -> Coding -> Auditing.
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

    
    def run_full_pipeline(self, user_idea: str = None, srs_path: Path = None, 
                          skip_scaffold: bool = False, 
                          k: int = DEFAULT_TOP_K) -> Dict[str, Any]: 
        """
        Executes the full chain of operations. Can start from user_idea or an existing srs_path.
        """
        
        current_srs_path = srs_path 
        
        # --- PHASE 0: GENERATE OR LOAD SRS DOCUMENT ---
        
        if user_idea and not current_srs_path:
            print("PHASE 0: Generating SRS document from user idea...")
            current_srs_path = self.srs_writer_agent.generate_srs(user_idea)
        
        elif current_srs_path and not user_idea:
            print(f"PHASE 0: Using existing SRS document: {current_srs_path.name}")
            if not current_srs_path.exists():
                return {"status": "FAILED", "reason": f"Existing SRS file not found at {current_srs_path}"}
            
        else:
            return {"status": "FAILED", "reason": "Pipeline requires either 'user_idea' OR 'srs_path'."}
        
        
        # PHASE 0.5: INDEXING (RAG Pipeline) - CRITICAL FOR RAG SUCCESS
        print(f"PHASE 0.5: Indexing generated SRS file: {current_srs_path.name} for RAG...")
        try:
            rag_instance = self.srs_writer_agent.rag_pipeline
            
            if rag_instance is None:
                raise ValueError("RAGPipeline instance is None. Check Orchestrator initialization in CLI.")

            rag_instance.index_srs(current_srs_path)
            
            print("Indexing successful.")
        except Exception as e:
            print(f"FATAL RAG INDEXING ERROR: {e}")
            return {"status": "FAILED", "reason": f"RAG Indexing Failed: {e}"}

        # PHASE 1 & 2: ARCHITECTURE EXTRACTION (MVCArchitectOrchestrator)
        print("PHASE 1-2: Extracting sequential MVC Architecture...")
        architecture_map = self.architect_orchestrator.extract_full_architecture(k=k)
        
        
        # PHASE 3: SCAFFOLD GENERATION (MVCScaffolder)
        if not skip_scaffold:
            print("PHASE 3: Generating skeleton files (Scaffolding)...")
            scaffold_result = self.scaffolder.scaffold_all(architecture_map)
        else:
            print("PHASE 3: Scaffolding skipped by request.")
            scaffold_result = {"skipped": True}
        
        
        # PHASE 4: CODE GENERATION (Coder Agent) - YENİ SIRA
        print("PHASE 4: Generating functional code logic (Coder Agent)...")
        try:
            self.coder_agent.generate_code()
        except Exception as e:
            print(f"[FATAL ERROR] Code Generation Failed: {e}")
            return {"status": "FAILED", "reason": f"Code Generation Failed: {e}"}
        
        
        # PHASE 5: AUDIT AND QUALITY CHECK (Rules & Reviewer Agents) - YENİ SIRA
        print("PHASE 5: Running Quality Audit (Rules & Reviewer)...")
        # Scaffold kök yolu (Scaffolder'dan alındı)
        scaffold_root = self.scaffolder.scaffold_root 
        
        # 5a. Rules Agent: Teknik ihlalleri tespit eder.
        technical_violations = self.rules_agent.detect_violations(scaffold_root)
        
        # 5b. Reviewer Agent: İhlalleri doğal dil önerilerine çevirir.
        final_audit_report = self.reviewer_agent.generate_audit_report(technical_violations)
        
        
        # Nihai çıktı raporu ve başarı durumunu döndürelim
        return {
            "status": "COMPLETED",
            "audit_result": final_audit_report,
            "architecture": architecture_map,
            "scaffold_path": str(scaffold_result)
        }