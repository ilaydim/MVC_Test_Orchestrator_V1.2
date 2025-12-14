import ast
import json
from typing import Dict, Any, List
from pathlib import Path
import re 

# BaseArchitectAgent'tan miras alıyoruz (data_dir özelliği için)
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class RulesAgent(BaseArchitectAgent):
    """
    Deterministically detects specific MVC violations and structural inconsistencies 
    using the Python AST library and file system checks.
    """
    
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
        SADECE MİMARİ İHLALLERİNE ODAKLANILIR.
        """
        architecture = self._load_architecture()
        violations = []
        
        # KRİTİK CHECK: Tüm temel MVC bağımlılık kurallarını denetle
        violations.extend(self._check_mvc_dependency_violations(scaffold_root, architecture))
        
        # Naming Convention (Dosya adı ihlalleri) kontrolü kaldırılmıştır.
        
        return violations

    # PEP 8 İsimlendirme kontrol metotları (_check_naming_conventions) tamamen kaldırıldı.

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
                
                # Dosyanın hangi katmana ait olduğunu belirle
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
                        import_target = node.module or ', '.join([n.name for n in node.names])
                        
                        # --- 1. Model Katmanı İhlalleri (MVC-M-00x) ---
                        if layer == 'Model':
                            # Kural M-001: Model, Controller import edemez
                            if controllers_dir_name in import_target.lower() or any(ctrl_name in import_target for ctrl_name in expected_controllers):
                                violations.append({
                                    "type": "MVC_M_C_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"CRITICAL: Model imports Controller logic/class ({import_target}). Models must be independent of higher layers (MVC-M-001).",
                                })
                            # Kural M-002: Model, View import edemez
                            if views_dir_name in import_target.lower() or any(view_name in import_target for view_name in expected_views):
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
                            # Ancak basit MVC'de bu bazen hoş görülür, kuralı sıkı tutalım.
                            if models_dir_name in import_target.lower() and not any(model_name in import_target for model_name in expected_models):
                                # Sadece klasör adını import etmeyi yakala
                                violations.append({
                                    "type": "MVC_V_M_VIOLATION",
                                    "file": str(file_path),
                                    "message": f"WARNING: View imports Model directly ({import_target}). Data flow should ideally be orchestrated by the Controller (MVC-V-002).",
                                })
                                
            except Exception as e:
                print(f"[AST ERROR] Failed to parse file {file_path}: {e}")
                continue

        return violations