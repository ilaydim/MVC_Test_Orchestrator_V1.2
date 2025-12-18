import ast
import json
from typing import Dict, Any, List
from pathlib import Path
import re 

class RulesAgent:
    """
    Deterministically detects specific MVC violations and structural inconsistencies 
    using the Python AST library and file system checks.
    """
    
    def __init__(self, rag_pipeline=None, llm_client=None):
        """Initialize RulesAgent. Parameters kept for compatibility but not used."""
        # Only need data_dir, no need for BaseArchitectAgent inheritance
        project_root = Path(__file__).resolve().parents[2]
        self.data_dir = project_root / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_architecture(self) -> Dict[str, Any]:
            """
            Loads the final unified architecture map from the data directory.
            """
            arch_path = self.data_dir / "architecture_map.json"
            if not arch_path.exists():
                # Eğer Mimari dosyası yoksa denetim yapılamaz
                return {} 
            with open(arch_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _normalize_name(self, raw_name: str) -> str:
        """Utility to convert SRS entity names into the expected PascalCase class name."""
        if not raw_name: return "Unnamed"
        cleaned = raw_name.replace("/", " ").replace("-", " ")
        cleaned = " ".join(cleaned.split())
        return "".join(word[0].upper() + word[1:] for word in cleaned.split())
    
    def _get_expected_names(self, architecture: Dict[str, Any], layer: str) -> List[str]:
        """Mimari haritasından beklenen sınıf/modül isimlerini alır."""
        entities = architecture.get(layer, [])
        if layer == 'controller':
            # Controller Agent'ınızın BookController, OrderController gibi PascalCase isimler ürettiğini varsayıyoruz.
            return [self._normalize_name(e.get('name', '')) + "Controller" for e in entities if e.get('name')]
        if layer == 'view':
            # View Agent'ınızın BookDetailsView gibi PascalCase isimler ürettiğini varsayıyoruz.
            return [self._normalize_name(e.get('name', '')) + "View" for e in entities if e.get('name')]
        # Model'ler için (Book, Order, vb.)
        return [self._normalize_name(e.get('name', '')) for e in entities if e.get('name')]

    def detect_violations(self, scaffold_root: Path) -> List[Dict[str, str]]:
        """
        Main entry point for deterministic rules checking. 
        Directly scans files using regex - does not require architecture_map.json.
        """
        violations = []
        
        # Direct file scanning - no architecture map needed
        violations.extend(self._check_mvc_dependency_violations_direct(scaffold_root))
        
        return violations

    # PEP 8 İsimlendirme kontrol metotları (_check_naming_conventions) tamamen kaldırıldı.

    def _check_mvc_dependency_violations_direct(self, root: Path) -> List[Dict[str, str]]:
        """
        Directly scans files using regex to detect MVC violations.
        Does not require architecture_map.json.
        """
        violations = []
        
        # Regex patterns for detecting layer violations
        models_pattern = re.compile(r'from\s+.*\.views\.|import\s+.*\.views\.|from\s+.*views\.|import\s+.*views\.', re.IGNORECASE)
        models_pattern_controller = re.compile(r'from\s+.*\.controllers\.|import\s+.*\.controllers\.|from\s+.*controllers\.|import\s+.*controllers\.', re.IGNORECASE)
        views_pattern_model = re.compile(r'from\s+.*\.models\.|import\s+.*\.models\.|from\s+.*models\.|import\s+.*models\.', re.IGNORECASE)
        
        for file_path in root.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Determine layer from file path
                file_str = str(file_path).replace('\\', '/')
                layer = None
                if '/models/' in file_str or '\\models\\' in file_str:
                    layer = 'Model'
                elif '/controllers/' in file_str or '\\controllers\\' in file_str:
                    layer = 'Controller'
                elif '/views/' in file_str or '\\views\\' in file_str:
                    layer = 'View'
                
                if not layer:
                    continue
                
                # Check for violations using regex
                if layer == 'Model':
                    # Model importing View
                    if models_pattern.search(content):
                        violations.append({
                            "type": "MVC_M_V_VIOLATION",
                            "file": str(file_path),
                            "message": f"CRITICAL: Model imports View. Found import statement containing 'views' in {file_path.name}",
                        })
                    # Model importing Controller
                    if models_pattern_controller.search(content):
                        violations.append({
                            "type": "MVC_M_C_VIOLATION",
                            "file": str(file_path),
                            "message": f"CRITICAL: Model imports Controller. Found import statement containing 'controllers' in {file_path.name}",
                        })
                
                elif layer == 'View':
                    # View importing Model directly
                    if views_pattern_model.search(content):
                        violations.append({
                            "type": "MVC_V_M_VIOLATION",
                            "file": str(file_path),
                            "message": f"WARNING: View imports Model directly. Found import statement containing 'models' in {file_path.name}",
                        })
                
            except SyntaxError as se:
                violations.append({
                    "type": "SYNTAX_ERROR",
                    "file": str(file_path),
                    "message": f"CRITICAL: Syntax error in file (line {se.lineno}): {se.msg}",
                })
                continue
            except Exception as e:
                violations.append({
                    "type": "PARSE_ERROR",
                    "file": str(file_path),
                    "message": f"WARNING: Failed to parse file: {str(e)}",
                })
                continue
        
        return violations

    def _check_mvc_dependency_violations(self, root: Path, architecture: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Tüm kritik MVC katmanlar arası import kurallarını denetler.
        """
        violations = []
        
        # Mimari haritasından beklenen sınıf isimlerini alıyoruz
        expected_controllers = [name + "Controller" for name in self._get_expected_names(architecture, 'controller')]
        expected_views = [name + "View" for name in self._get_expected_names(architecture, 'view')]
        expected_models = self._get_expected_names(architecture, 'model')
        
        # Klasör adları
        models_dir_name = (root / "models").name
        controllers_dir_name = (root / "controllers").name
        views_dir_name = (root / "views").name
        
        for file_path in root.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                layer = None
                if models_dir_name in str(file_path):
                    layer = 'Model'
                elif controllers_dir_name in str(file_path):
                    layer = 'Controller'
                elif views_dir_name in str(file_path):
                    layer = 'View'
                
                if not layer: continue # MVC katmanı değilse atla
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) or isinstance(node, ast.Import):
                        # Get import target
                        if isinstance(node, ast.ImportFrom):
                            import_target = node.module or ''
                            imported_names = [n.name for n in node.names]
                        else:  # ast.Import
                            import_target = ', '.join([n.name for n in node.names])
                            imported_names = [n.name for n in node.names]
                        
                        # --- 1. Model Katmanı İhlalleri (MVC-M-00x) ---
                        if layer == 'Model':
                            # Kural M-001: Model, Controller import edemez
                            if (controllers_dir_name in import_target.lower() or 
                                any(ctrl_name.lower() in import_target.lower() for ctrl_name in expected_controllers) or
                                any(ctrl_name.lower() in name.lower() for ctrl_name in expected_controllers for name in imported_names)):
                                violations.append({
                                    "type": "MVC_M_C_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"CRITICAL: Model imports Controller logic/class ({import_target}). Models must be independent of higher layers (MVC-M-001).",
                                })
                            # Kural M-002: Model, View import edemez
                            if (views_dir_name in import_target.lower() or 
                                any(view_name.lower() in import_target.lower() for view_name in expected_views) or
                                any(view_name.lower() in name.lower() for view_name in expected_views for name in imported_names)):
                                violations.append({
                                    "type": "MVC_M_V_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"CRITICAL: Model imports View logic/class ({import_target}). Models must be independent of higher layers (MVC-M-002).",
                                })

                        # --- 2. Controller Katmanı İhlalleri (MVC-C-00x) ---
                        elif layer == 'Controller':
                            # Kural C-001: Controller, başka Controller import edemez (Genellikle servis katmanı yerine geçer)
                            if 'controller' in import_target.lower() and import_target.lower() != str(file_path.name).lower():
                                violations.append({
                                    "type": "MVC_C_C_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"WARNING: Controller imports another Controller or Controller logic ({import_target}). Business logic should reside in Models or Service Layers (MVC-C-001).",
                                })
                            # Kural C-002: Controller, View import edebilir (View'ı tetiklemek için)
                            # Bu kuralı eklemeye gerek yok, bu bir ihlal değildir.

                        # --- 3. View Katmanı İhlalleri (MVC-V-00x) ---
                        elif layer == 'View':
                            # Kural V-001: View, Controller import edebilir (Kullanıcı etkileşimlerini Controller'a yönlendirmek için)
                            # Bu kuralı eklemeye gerek yok, bu bir ihlal değildir.
                            
                            # Kural V-002: View, doğrudan Model import etmemelidir (Controller üzerinden dolaylı olmalıdır).
                            # Basit MVC'de bu bazen hoş görülür ama ideal değildir.
                            if (models_dir_name in import_target.lower() or 
                                any(model_name.lower() in import_target.lower() for model_name in expected_models) or
                                any(model_name.lower() in name.lower() for model_name in expected_models for name in imported_names)):
                                violations.append({
                                    "type": "MVC_V_M_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"WARNING: View imports Model directly ({import_target}). Data flow should ideally be orchestrated by the Controller (MVC-V-002).",
                                })
                                
            except SyntaxError as se:
                # Syntax errors should be reported as violations
                violations.append({
                    "type": "SYNTAX_ERROR",
                    "file": str(file_path),
                    "message": f"CRITICAL: Syntax error in file (line {se.lineno}): {se.msg}. File may be corrupted or contain invalid Python code.",
                })
                print(f"[AST ERROR] Failed to parse file {file_path}: {se}")
                continue
            except Exception as e:
                # Other parsing errors
                violations.append({
                    "type": "PARSE_ERROR",
                    "file": str(file_path),
                    "message": f"WARNING: Failed to parse file: {str(e)}. File may be corrupted.",
                })
                print(f"[AST ERROR] Failed to parse file {file_path}: {e}")
                continue

        return violations