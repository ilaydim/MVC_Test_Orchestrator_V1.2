import ast
from typing import Dict, Any, List
from pathlib import Path
import re # Import the regular expression module

# BaseArchitectAgent'tan data_dir özelliğini miras alıyoruz
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class RulesAgent(BaseArchitectAgent):
    """
    Deterministically detects specific MVC violations, naming convention issues, 
    and structural inconsistencies using the Python AST library and file system checks.
    
    This agent does NOT use the LLM (Gemini API).
    """

    # NOTE: _load_architecture metodu BaseArchitectAgent'tan miras alınırsa daha temiz olur, 
    # ancak burada yeniden tanımlayalım veya Base'e taşıyalım.
    # Şimdilik, AuditorAgent'taki _load_architecture metodunun buraya taşındığını varsayalım.
    
    def _load_architecture(self) -> Dict[str, Any]:
        """Loads the final unified architecture map."""
        # ... (implementation from AuditorAgent)
        arch_path = self.data_dir / "architecture_map.json"
        if not arch_path.exists():
            raise FileNotFoundError(f"Architecture map not found at {arch_path}")
        with open(arch_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def detect_violations(self, scaffold_root: Path) -> List[Dict[str, str]]:
        """
        Main entry point for deterministic rules checking.
        """
        architecture = self._load_architecture()
        violations = []
        
        # Check 1: Naming Conventions (PEP 8 for files/classes)
        violations.extend(self._check_naming_conventions(scaffold_root))
        
        # Check 2: MVC Structure Violation (e.g., Model files importing Controller logic)
        violations.extend(self._check_mvc_imports(scaffold_root, architecture))
        
        # Check 3: Completeness (AuditorAgent'tan gelen kontrol)
        # violations.extend(self._check_completeness(architecture, scaffold_root))
        
        return violations

    def _check_naming_conventions(self, root: Path) -> List[Dict[str, str]]:
        """Checks files/classes against PEP 8 (PascalCase for classes, snake_case for files)."""
        violations = []
        
        for file_path in root.rglob("*.py"):
            file_name = file_path.stem
            
            # File Naming: Check if file name is snake_case
            if not re.match(r"^[a-z_]+$", file_name):
                 violations.append({
                    "type": "NAMING_CONVENTION_VIOLATION",
                    "file": str(file_path),
                    "message": f"File name '{file_name}.py' should be snake_case (PEP 8).",
                })
            
            # Class Naming: Check if classes inside are PascalCase
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", class_name):
                             violations.append({
                                "type": "NAMING_CONVENTION_VIOLATION",
                                "file": str(file_path),
                                "message": f"Class '{class_name}' should be PascalCase (PEP 8).",
                            })
            except Exception as e:
                violations.append({"type": "AST_PARSE_ERROR", "file": str(file_path), "message": f"Failed to parse file: {e}"})

        return violations

    def _check_mvc_imports(self, root: Path, architecture: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detects high-level MVC violations (e.g., Model importing Controller)."""
        violations = []
        
        # Basitlik için: Model klasöründeki bir dosya, Controller klasöründeki herhangi bir şeyi import ediyorsa, kural ihlalidir.
        controllers = [self._normalize_name(c['name']) + "Controller" for c in architecture.get("controller", [])]
        models_dir = root / "models"
        
        for model_file in models_dir.rglob("*.py"):
            try:
                content = model_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) or isinstance(node, ast.Import):
                        import_target = node.module or ', '.join([n.name for n in node.names])
                        
                        # Kontrol: Herhangi bir Controller sınıfı adı veya Controller modül adı import edilmiş mi?
                        if any(ctrl_name in import_target for ctrl_name in controllers):
                            violations.append({
                                "type": "MVC_VIOLATION",
                                "file": str(model_file),
                                "message": f"Model file is importing Controller logic or class ({import_target}). Models must be decoupled from Controllers.",
                            })
                            
            except Exception:
                # Parsing hatalarını görmezden gelelim
                continue

        return violations
        
    def _normalize_name(self, raw_name: str) -> str:
        """Utility to match MVCScaffolder's naming convention."""
        # MVCScaffolder'daki _safe_class_name ile aynı olmalı
        if not raw_name: return "Unnamed"
        cleaned = raw_name.replace("/", " ").replace("-", " ")
        cleaned = " ".join(cleaned.split())
        return "".join(word[0].upper() + word[1:] for word in cleaned.split())