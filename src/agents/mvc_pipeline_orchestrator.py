import os
import sys
import json
from typing import Dict, Any, List
from pathlib import Path 

# Ana dizin ayarları
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.agents.srs_writer_agent import SRSWriterAgent 
from src.agents.rules_agent import RulesAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.coder_agent import CoderAgent
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder 
from src.agents.architect_agent.mvc_architect_orchestrator import MVCArchitectOrchestrator
from src.core.config import DEFAULT_TOP_K 

class MVCPipelineOrchestrator:
    def __init__(self, rag_pipeline=None, llm_client=None):
        self.srs_writer_agent = SRSWriterAgent(rag_pipeline, llm_client)
        self.scaffolder = MVCScaffolder() 
        self.rules_agent = RulesAgent(rag_pipeline, llm_client)
        self.reviewer_agent = ReviewerAgent(rag_pipeline, llm_client)
        self.coder_agent = CoderAgent(rag_pipeline, llm_client)
        self.architect_orchestrator = MVCArchitectOrchestrator(rag_pipeline, llm_client)

    # --- KOMUT 1a & 1b: SADECE MİMARİ ÇIKARMA ---
    def run_extraction_only(self, srs_path: Path, output_path: str) -> Dict[str, Any]:
        """Sadece mimariyi çıkarır ve JSON yazar. Klasör oluşturmaz."""
        print(f"PHASE 0.5: Indexing SRS file: {srs_path.name}")
        self.srs_writer_agent.rag_pipeline.index_srs(srs_path)
        
        print("PHASE 1-2: Extracting MVC Architecture (Extraction Only)...")
        architecture_map = self.architect_orchestrator.extract_full_architecture()
        
        # SRS içeriğini RAG'dan güvenli bir şekilde al
        try:
            srs_context = self.srs_writer_agent.rag_pipeline.get_full_context()
        except AttributeError:
            srs_context = "SRS context extraction failed."

        full_data = {
            "srs": srs_context,
            "architecture": architecture_map
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=4, ensure_ascii=False)
        
        print(f"[SUCCESS] Extraction complete. JSON written to: {output_path}")
        return full_data

    # --- KOMUT 4: SADECE KALİTE DENETİMİ ---
    def run_audit_only(self, architecture_path: Path):
        """Sadece kodları tarar ve rapor üretir."""
        print("PHASE 5: Running Quality Audit (Independent)...")
        scaffold_root = self.scaffolder.scaffold_root 
        
        if not any(scaffold_root.iterdir()):
            print("[ERROR] Scaffold directory is empty. Run Step 2 & 3 first.")
            return None

        technical_violations = self.rules_agent.detect_violations(scaffold_root)
        final_report = self.reviewer_agent.generate_audit_report(technical_violations)
        
        output_file = architecture_path.parent / "final_audit_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=4)
            
        print(f"[SUCCESS] Audit report created: {output_file}")
        return final_report

    # --- ESKİ METOT (Gerektiğinde tam akış için saklanabilir veya silinebilir) ---
    def run_full_pipeline(self, user_idea: str = None, srs_path: Path = None, 
                          skip_scaffold: bool = False, 
                          k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        # Bu metodun içini tamamen boşaltıp yukarıdaki modüler metotları 
        # sırayla çağıracak şekilde güncelleyebilirsiniz.
        pass