import json
from typing import Dict, Any, List
from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class CoderAgent(BaseArchitectAgent):
    """
    Fills the skeleton files created by the Scaffolder with actual Python code
    based on the extracted architecture map and the original SRS document.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        # Assuming Scaffolder's root path is known or configured
        self.scaffold_root = Path(__file__).resolve().parents[3] / "scaffolds" / "mvc_skeleton"


    def _load_files(self) -> Dict[str, Any]:
        """Loads the architecture map and SRS document content."""
        
        # Load Architecture Map
        arch_path = self.data_dir / "architecture_map.json"
        with open(arch_path, "r", encoding="utf-8") as f:
            architecture = json.load(f)

        # Load SRS Content (for business logic context)
        srs_path = self.data_dir / "srs_document.txt"
        srs_content = srs_path.read_text(encoding="utf-8")
        
        return {"architecture": architecture, "srs": srs_content}


    def generate_code(self) -> Dict[str, List[Path]]:
        """
        Main entry point for code generation. Iterates through scaffold files
        and calls the LLM for code completion.
        """
        
        data = self._load_files()
        
        completed_files: List[Path] = []

        # 1. Model Dosyalarını Kodla
        models_dir = self.scaffold_root / "models"
        completed_files.extend(self._process_model_files(models_dir, data))
        
        # 2. Controller Dosyalarını Kodla
        controllers_dir = self.scaffold_root / "controllers"
        completed_files.extend(self._process_controller_files(controllers_dir, data))
        
        # NOTE: View dosyalarını kodlama (HTML/JS/vb.) daha karmaşık olabilir. 
        # Şimdilik sadece Model ve Controller'a odaklanalım.

        return {"completed_files": completed_files}


    def _process_model_files(self, directory: Path, data: Dict[str, Any]) -> List[Path]:
        """Fills model skeleton files with attributes and basic methods."""
        
        completed: List[Path] = []
        for file_path in directory.rglob("*.py"):
            print(f"Coding Model: {file_path.name}")
            skeleton_content = file_path.read_text(encoding="utf-8")
            
            prompt = self._build_model_code_prompt(skeleton_content, data)
            
            # LLM'den kodu direkt string olarak alıyoruz (JSON değil)
            new_code = self.llm.model.generate_content(prompt).text.strip()
            
            # Kod etiketlerini temizle ve dosyayı yeni kodla overwrite et
            cleaned_code = new_code.strip("`").replace("python", "").replace("py", "").strip()
            file_path.write_text(cleaned_code, encoding="utf-8")
            completed.append(file_path)
            
        return completed


    def _build_model_code_prompt(self, skeleton: str, data: Dict[str, Any]) -> str:
        """
        Prompts the LLM to complete the Model class by adding __init__ attributes 
        based on the SRS and defined architecture.
        """
        srs = data['srs']
        
        return f"""
You are a Python Senior Developer. Your task is to complete the provided Python Model 
class skeleton based on the SRS and the high-level architecture.

### GOAL:
1.  Complete the class definition (e.g., add attributes in __init__).
2.  Add necessary getter/setter methods, or simple CRUD methods (e.g., save(), find_by_id()).
3.  The final code MUST be valid, clean Python code.

### ARCHITECTURE CONTEXT (for class name/purpose):
{data['architecture']['model']}

### SRS CONTENT (for detailed business logic/attributes):
{srs[:2000]} 

### SKELETON TO COMPLETE:
{skeleton}

Return ONLY the complete, final Python code block. NO explanation, NO JSON.
"""
# ... _process_controller_files metodu benzer şekilde yazılacaktır.