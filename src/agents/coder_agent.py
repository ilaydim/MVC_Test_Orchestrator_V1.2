import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

# BaseArchitectAgent'tan miras alıyoruz
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 
from src.core.config import DEFAULT_TOP_K


class CoderAgent(BaseArchitectAgent):
    """
    Fills ALL skeleton files (models, views, controllers) created by the Scaffolder 
    with actual Python code based on the extracted architecture map and SRS document.
    Uses RAG to retrieve relevant SRS sections for each class.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        # Scaffold kök yolu
        self.scaffold_root = Path(__file__).resolve().parents[3] / "scaffolds" / "mvc_skeleton"

    def _load_architecture_data(self) -> Dict[str, Any]:
        """Loads architecture map from JSON file (handles both old and new formats)."""
        arch_path = self.data_dir / "architecture_map.json"
        
        if not arch_path.exists():
            raise FileNotFoundError(f"Architecture map not found: {arch_path}")
        
        with open(arch_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        
        # Yeni format: {"srs": "...", "architecture": {...}}
        # Eski format: direkt architecture map
        if "architecture" in full_data:
            architecture = full_data["architecture"]
        else:
            architecture = full_data
        
        return architecture

    def _extract_class_name_from_file(self, file_path: Path) -> str:
        """Extracts the class name from a Python file."""
        content = file_path.read_text(encoding="utf-8")
        match = re.search(r'class\s+(\w+)', content)
        if match:
            return match.group(1)
        # Fallback: filename without extension
        return file_path.stem

    def _find_matching_architecture_item(self, class_name: str, category: str, architecture: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Finds the matching architecture item for a given class name.
        Tries to match by class name or by description.
        """
        items = architecture.get(category, [])
        
        # Normalize class name for matching (remove common suffixes)
        normalized_class = class_name.replace("View", "").replace("Controller", "").lower()
        
        for item in items:
            item_name = item.get("name", "").lower()
            item_desc = item.get("description", "").lower()
            
            # Try exact match or partial match
            if normalized_class in item_name or item_name in normalized_class:
                return item
            
            # Try matching by description keywords
            if normalized_class in item_desc:
                return item
        
        # If no match found, return first item as fallback (if exists)
        return items[0] if items else None

    def _get_relevant_srs_context(self, class_name: str, category: str, architecture_item: Optional[Dict[str, Any]]) -> str:
        """
        Uses RAG to retrieve relevant SRS chunks for a specific class.
        Falls back to full SRS if RAG is not available.
        """
        if not self.rag or not hasattr(self.rag, 'search'):
            # Fallback: try to get full SRS
            try:
                srs_path = self.data_dir / "srs_document.txt"
                if srs_path.exists():
                    return srs_path.read_text(encoding="utf-8")[:3000]  # Limit to 3000 chars
            except:
                pass
            return "SRS content not available."
        
        # Build RAG query based on class and architecture info
        query_parts = [f"{category}: {class_name}"]
        if architecture_item:
            query_parts.append(architecture_item.get("name", ""))
            query_parts.append(architecture_item.get("description", ""))
        
        query = " ".join(filter(None, query_parts))
        
        try:
            result = self.rag.search(query, k=DEFAULT_TOP_K)
            documents = result.get("documents", [])
            if documents and documents[0]:
                # Combine relevant chunks
                return "\n\n".join(documents[0][:3])  # Top 3 chunks
        except Exception as e:
            print(f"[WARN] RAG search failed for {class_name}: {e}")
        
        # Fallback to full SRS
        try:
            srs_path = self.data_dir / "srs_document.txt"
            if srs_path.exists():
                return srs_path.read_text(encoding="utf-8")[:3000]
        except:
            pass
        
        return "SRS content not available."

    def generate_code(self) -> Dict[str, List[Path]]:
            """
            Geliştirilmiş generate_code: Klasör yollarını doğrular ve 
            dosya bulunamadığında tam olarak nereye baktığını loglar.
            """
            print("[Coder Agent] Loading architecture data...")
            architecture = self._load_architecture_data()
            
            # PROJE KÖK DİZİNİNİ DAHA GÜVENLİ HALE GETİRELİM
            # src/agents/coder_agent.py -> src -> agents -> (parents[2] kök dizindir)
            # Eğer bu dosya derin bir klasördeyse ayarı kontrol etmeliyiz.
            project_root = Path(__file__).resolve().parents[2] 
            self.scaffold_root = project_root / "scaffolds" / "mvc_skeleton"
            
            print(f"[DEBUG] Search path: {self.scaffold_root.absolute()}")
            
            if not self.scaffold_root.exists():
                print(f"[ERROR] Scaffold directory NOT FOUND at: {self.scaffold_root}")
                return {"completed_files": []}

            completed_files: List[Path] = []
            
            # Kategorileri ve karşılık gelen klasörleri tara
            categories = {
                "model": self.scaffold_root / "models",
                "view": self.scaffold_root / "views",
                "controller": self.scaffold_root / "controllers"
            }

            for category, target_dir in categories.items():
                print(f"[Coder Agent] Checking directory: {target_dir.name}...")
                
                if target_dir.exists():
                    # Klasör içindeki .py dosyalarını sayalım
                    files_to_process = list(target_dir.glob("*.py"))
                    print(f"[INFO] Found {len(files_to_process)} skeleton files in {category}.")
                    
                    if files_to_process:
                        processed = self._process_files(target_dir, category, architecture)
                        completed_files.extend(processed)
                else:
                    print(f"[WARN] Directory missing: {target_dir}")

            print(f"[Coder Agent] Total Completed: {len(completed_files)} files.")
            return {"completed_files": completed_files}

    def _process_files(self, directory: Path, category: str, architecture: Dict[str, Any]) -> List[Path]:
        """
        Generic method to process all Python files in a directory.
        Works for models, views, and controllers.
        """
        completed: List[Path] = []
        
        for file_path in sorted(directory.glob("*.py")):
            if not file_path.is_file():
                continue
            
            class_name = self._extract_class_name_from_file(file_path)
            print(f"[Coder Agent] Processing {category}: {class_name} ({file_path.name})")
            
            # Find matching architecture item
            arch_item = self._find_matching_architecture_item(class_name, category, architecture)
            
            # Get relevant SRS context via RAG
            srs_context = self._get_relevant_srs_context(class_name, category, arch_item)
            
            # Read skeleton
            skeleton_content = file_path.read_text(encoding="utf-8")
            
            # Build prompt and generate code
            prompt = self._build_code_prompt(skeleton_content, category, class_name, arch_item, srs_context, architecture)
            
            # Generate code using LLM (with retry mechanism)
            new_code = self._generate_code_with_llm(prompt, file_path.name)
            
            if new_code and new_code != skeleton_content:
                try:
                    file_path.write_text(new_code, encoding="utf-8")
                    completed.append(file_path)
                    print(f"[SUCCESS] Code written to {file_path.name}")
                except Exception as e:
                    print(f"[ERROR] Failed to write {file_path.name}: {e}")
            else:
                print(f"[WARN] No valid code generated for {file_path.name}")
        
        return completed

    def _generate_code_with_llm(self, prompt: str, filename: str) -> Optional[str]:
        """Generates code using LLM with error handling."""
        try:
            # Use LLMClient's generate_content method (has retry mechanism)
            response_text = self.llm.generate_content(prompt)
            
            # Clean up response (remove markdown code blocks)
            cleaned = response_text.strip()
            cleaned = re.sub(r'```python\s*', '', cleaned)
            cleaned = re.sub(r'```py\s*', '', cleaned)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            # Validate: must contain class definition
            if 'class' in cleaned and len(cleaned) > 100:
                return cleaned
            else:
                print(f"[WARN] Generated code for {filename} seems invalid (too short or no class).")
                return None
                
        except Exception as e:
            print(f"[ERROR] LLM generation failed for {filename}: {e}")
            return None

    def _build_code_prompt(self, skeleton: str, category: str, class_name: str, 
                          arch_item: Optional[Dict[str, Any]], srs_context: str, 
                          architecture: Dict[str, Any]) -> str:
        """
        Builds a comprehensive prompt for code generation based on category.
        """
        arch_info = json.dumps(arch_item, indent=2) if arch_item else "No specific architecture info found."
        
        if category == "model":
            return self._build_model_prompt(skeleton, class_name, arch_info, srs_context)
        elif category == "view":
            return self._build_view_prompt(skeleton, class_name, arch_info, srs_context)
        elif category == "controller":
            return self._build_controller_prompt(skeleton, class_name, arch_info, srs_context, architecture)
        else:
            return self._build_generic_prompt(skeleton, category, class_name, arch_info, srs_context)

    def _build_model_prompt(self, skeleton: str, class_name: str, arch_info: str, srs_context: str) -> str:
        return f"""You are an expert Python developer. Complete the Model class skeleton based on the SRS requirements.

### TASK:
Fill in the {class_name} class with:
1. **Attributes**: Add all fields/properties mentioned in the SRS for this entity
2. **__init__ method**: Initialize all attributes with appropriate default values
3. **Getter/Setter methods**: Add property methods if needed
4. **Business logic methods**: Add methods for entity operations (save, validate, etc.)
5. **Type hints**: Use proper Python type hints (str, int, float, bool, Optional, List, Dict, etc.)

### ARCHITECTURE INFORMATION:
{arch_info}

### RELEVANT SRS CONTENT:
{srs_context}

### CURRENT SKELETON:
{skeleton}

### REQUIREMENTS:
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: {class_name}
- Add comprehensive docstrings for the class and methods
- Use proper Python conventions (PEP 8)
- Include type hints for all methods
- Make the code production-ready and complete

Return the complete, final Python code:"""

    def _build_view_prompt(self, skeleton: str, class_name: str, arch_info: str, srs_context: str) -> str:
        return f"""You are an expert Python developer. Complete the View class skeleton based on the SRS requirements.

### TASK:
Fill in the {class_name} class with:
1. **Render method**: Implement the main rendering logic
2. **UI components**: Add methods for rendering different UI elements (forms, lists, details, etc.)
3. **Data binding**: Add methods to bind data to UI elements
4. **Event handlers**: Add placeholder methods for user interactions
5. **Template/HTML structure**: If web-based, include structure for the view

### ARCHITECTURE INFORMATION:
{arch_info}

### RELEVANT SRS CONTENT:
{srs_context}

### CURRENT SKELETON:
{skeleton}

### REQUIREMENTS:
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: {class_name}
- Framework-agnostic (can be adapted to Flask, Django, React, etc.)
- Include comprehensive docstrings
- Use proper Python conventions (PEP 8)
- Make the code production-ready and complete

Return the complete, final Python code:"""

    def _build_controller_prompt(self, skeleton: str, class_name: str, arch_info: str, 
                                srs_context: str, architecture: Dict[str, Any]) -> str:
        # Get related models and views for context
        related_models = json.dumps(architecture.get("model", [])[:3], indent=2)
        related_views = json.dumps(architecture.get("view", [])[:3], indent=2)
        
        return f"""You are an expert Python developer. Complete the Controller class skeleton based on the SRS requirements.

### TASK:
Fill in the {class_name} class with:
1. **Action methods**: Implement all action methods from the skeleton with full business logic
2. **Request handling**: Add request validation and parameter extraction
3. **Business logic**: Implement the core business logic for each action based on SRS
4. **Model integration**: Use model classes to interact with data
5. **View integration**: Return appropriate responses/views
6. **Error handling**: Add try-except blocks and proper error responses
7. **Validation**: Add input validation for all methods

### ARCHITECTURE INFORMATION:
{arch_info}

### RELATED MODELS (for reference):
{related_models}

### RELATED VIEWS (for reference):
{related_views}

### RELEVANT SRS CONTENT:
{srs_context}

### CURRENT SKELETON:
{skeleton}

### REQUIREMENTS:
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: {class_name}
- Implement ALL methods from the skeleton
- Add comprehensive docstrings explaining what each method does
- Use proper Python conventions (PEP 8)
- Include type hints
- Add error handling
- Make the code production-ready and complete

Return the complete, final Python code:"""

    def _build_generic_prompt(self, skeleton: str, category: str, class_name: str, 
                            arch_info: str, srs_context: str) -> str:
        return f"""You are an expert Python developer. Complete the {category} class skeleton based on the SRS requirements.

### TASK:
Fill in the {class_name} class with complete, production-ready implementation based on the SRS.

### ARCHITECTURE INFORMATION:
{arch_info}

### RELEVANT SRS CONTENT:
{srs_context}

### CURRENT SKELETON:
{skeleton}

### REQUIREMENTS:
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: {class_name}
- Add comprehensive docstrings
- Use proper Python conventions (PEP 8)
- Include type hints
- Make the code production-ready and complete

Return the complete, final Python code:"""
