import json
from typing import Dict, Any, List
from pathlib import Path

# BaseArchitectAgent'tan miras alıyoruz
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class CoderAgent(BaseArchitectAgent):
    """
    Fills the skeleton files created by the Scaffolder with actual Python code
    based on the extracted architecture map and the original SRS document.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        # KRİTİK DÜZELTME: Scaffold kök yolu Path yapısıyla güvenli hale getirildi
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
        
        data = self._load_files()
        completed_files: List[Path] = []

        # 1. Model Dosyalarını Kodla
        models_dir = self.scaffold_root / "models"
        completed_files.extend(self._process_model_files(models_dir, data))
        
        # 2. Controller Dosyalarını Kodla
        controllers_dir = self.scaffold_root / "controllers"
        completed_files.extend(self._process_controller_files(controllers_dir, data))
        
        return {"completed_files": completed_files}


    def _process_model_files(self, directory: Path, data: Dict[str, Any]) -> List[Path]:
        """Fills model skeleton files with attributes and basic methods."""
        
        completed: List[Path] = []
        for file_path in directory.rglob("*.py"):
            print(f"Coding Model: {file_path.name}")
            skeleton_content = file_path.read_text(encoding="utf-8")
            prompt = self._build_model_code_prompt(skeleton_content, data)
            
            new_code = skeleton_content
            try:
                # KRİTİK DÜZELTME 1: Timeout eklendi (60 saniye)
                response = self.llm.model.generate_content(
                    prompt, 
                    request_options={"timeout": 60} 
                )
                new_code = response.text.strip()
            except Exception as e:
                print(f"[ERROR] LLM Code Generation Timeout/Error for {file_path.name}: {e}")
            
            
            # GÜÇLENDİRİLMİŞ TEMİZLEME MANTIĞI: Sadece Markdown etiketlerini kaldır.
            final_code = new_code.strip()
            # Önce en yaygın Python etiketlerini kaldırma
            final_code = final_code.replace("```python", "").replace("```py", "").replace("```", "").strip()
            
            # KRİTİK KONTROL: Kodun uzunluğu 50 karakterden büyükse VE iskeletten farklıysa yaz.
            is_valid_code = len(final_code) > 50 and ('class' in final_code or 'def' in final_code)
            is_different = final_code != skeleton_content.strip()

            if is_valid_code and is_different:
                try:
                    file_path.write_text(final_code, encoding="utf-8")
                    completed.append(file_path)
                    print(f"[SUCCESS] Wrote code to {file_path.name}")
                except Exception as write_error:
                    print(f"[FATAL WRITE ERROR] Could not write to {file_path.name}: {write_error}")
            else:
                print(f"[WARNING] Skipping write for {file_path.name}: LLM returned empty/identical code. Valid Check: {is_valid_code}, Different Check: {is_different}")
            
        return completed


    def _build_model_code_prompt(self, skeleton: str, data: Dict[str, Any]) -> str:
        
        srs = data['srs']
        return f"""
You are a Python Senior Developer. Your task is to complete the provided Python Model 
class skeleton based on the SRS and the high-level architecture.

### GOAL:
1. Complete the class definition (e.g., add attributes in __init__).
2. Add necessary getter/setter methods, or simple CRUD methods (e.g., save(), find_by_id()).
3. The final code MUST be valid, clean Python code.

### ARCHITECTURE CONTEXT (for class name/purpose):
{data['architecture']['model']}

### SRS CONTENT (for detailed business logic/attributes):
{srs[:2000]} 

### SKELETON TO COMPLETE:
{skeleton}

Return ONLY the complete, final Python code block. NO explanation, NO JSON.
"""

    def _process_controller_files(self, directory: Path, data: Dict[str, Any]) -> List[Path]:
        
        completed: List[Path] = []
        for file_path in directory.rglob("*.py"):
            print(f"Coding Controller: {file_path.name}")
            skeleton_content = file_path.read_text(encoding="utf-8")
            prompt = self._build_controller_code_prompt(skeleton_content, data)
            
            new_code = skeleton_content
            try:
                # KRİTİK DÜZELTME 1: Timeout eklendi (60 saniye)
                response = self.llm.model.generate_content(
                    prompt, 
                    request_options={"timeout": 60} 
                )
                new_code = response.text.strip()
            except Exception as e:
                print(f"[ERROR] LLM Code Generation Timeout/Error for {file_path.name}: {e}")
            
            # GÜÇLENDİRİLMİŞ TEMİZLEME MANTIĞI: Sadece Markdown etiketlerini kaldır.
            final_code = new_code.strip()
            # Önce en yaygın Python etiketlerini kaldırma
            final_code = final_code.replace("```python", "").replace("```py", "").replace("```", "").strip()

            # KRİTİK KONTROL: Kodun uzunluğu 50 karakterden büyükse VE iskeletten farklıysa yaz.
            is_valid_code = len(final_code) > 50 and ('class' in final_code or 'def' in final_code)
            is_different = final_code != skeleton_content.strip()

            if is_valid_code and is_different:
                try:
                    file_path.write_text(final_code, encoding="utf-8")
                    completed.append(file_path)
                    print(f"[SUCCESS] Wrote code to {file_path.name}")
                except Exception as write_error:
                    print(f"[FATAL WRITE ERROR] Could not write to {file_path.name}: {write_error}")
            else:
                print(f"[WARNING] Skipping write for {file_path.name}: LLM returned empty/identical code. Valid Check: {is_valid_code}, Different Check: {is_different}")
            
        return completed


    def _build_controller_code_prompt(self, skeleton: str, data: Dict[str, Any]) -> str:
        
        srs = data['srs']
        return f"""
You are a Python Senior Developer specialized in API/web framework Controllers. Your task is to complete the provided Controller class skeleton.

### GOAL:
1. Define API/routing endpoints (e.g., using Flask/Django decorators or simple methods).
2. Implement methods to handle requests (e.g., GET /products, POST /users).
3. Use the business logic defined in the architecture map.
4. The final code MUST be valid, clean Python code.

### ARCHITECTURE CONTEXT (for class name/purpose):
{data['architecture']['controller']}

### SRS CONTENT (for detailed business logic/flows):
{srs[:2000]} 

### SKELETON TO COMPLETE:
{skeleton}

Return ONLY the complete, final Python code block. NO explanation, NO JSON.
"""