import ast
import json
from typing import Dict, List
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
    
    def detect_violations(self, scaffold_root: Path) -> List[Dict[str, str]]:
        """
        Main entry point for deterministic rules checking. 
        Directly scans files using regex - does not require architecture_map.json.
        Saves violations to violations.json (Structured Output).
        """
        violations = []
        
        # Direct file scanning - no architecture map needed
        violations.extend(self._check_mvc_dependency_violations_direct(scaffold_root))
        
        # Save violations to violations.json (Structured Output)
        violations_output = {
            "violations": violations,
            "total_count": len(violations)
        }
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        violations_file = self.data_dir / "violations.json"
        try:
            with open(violations_file, "w", encoding="utf-8") as f:
                json.dump(violations_output, f, indent=4, ensure_ascii=False)
            print(f"[RulesAgent] Violations saved to: {violations_file}")
        except Exception as e:
            print(f"[RulesAgent] Warning: Could not save violations.json: {e}")
        
        return violations

    def _check_mvc_dependency_violations_direct(self, root: Path) -> List[Dict[str, str]]:
        """
        Directly scans files using BOTH regex and AST parsing to detect MVC violations.
        Does not require architecture_map.json.
        Uses dual approach (regex + AST) for maximum reliability.
        """
        violations = []
        
        python_files = list(root.rglob("*.py"))
        print(f"[RulesAgent] Scanning {len(python_files)} Python file(s) in {root}")
        
        # Regex patterns as backup (more permissive, catches edge cases)
        pattern_model_views = re.compile(r'from\s+.*\.views\.|import\s+.*\.views\.|from\s+.*views\.|import\s+.*views\.', re.IGNORECASE)
        pattern_model_controllers = re.compile(r'from\s+.*\.controllers\.|import\s+.*\.controllers\.|from\s+.*controllers\.|import\s+.*controllers\.', re.IGNORECASE)
        pattern_view_models = re.compile(r'from\s+.*\.models\.|import\s+.*\.models\.|from\s+.*models\.|import\s+.*models\.', re.IGNORECASE)
        pattern_controller_controllers = re.compile(r'from\s+.*\.controllers\.|import\s+.*\.controllers\.|from\s+\..*Controller|import\s+.*Controller', re.IGNORECASE)
        
        # Her dosyayı tek tek açar ve yoluna (path) bakar. Eğer dosya models klasöründeyse, ona "Sen bir Modelsin" damgasını vurur.
        for file_path in python_files:
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
                
                # METHOD 1: Quick regex check (fast, catches most cases)
                if layer == 'Model':
                    if pattern_model_views.search(content):
                        violations.append({
                            "type": "MVC_M_V_VIOLATION",
                            "file": str(file_path),
                            "message": f"CRITICAL: Model imports View. Found import statement containing 'views' in {file_path.name}",
                        })
                    if pattern_model_controllers.search(content):
                        violations.append({
                            "type": "MVC_M_C_VIOLATION",
                            "file": str(file_path),
                            "message": f"CRITICAL: Model imports Controller. Found import statement containing 'controllers' in {file_path.name}",
                        })
                
                elif layer == 'View':
                    if pattern_view_models.search(content):
                        violations.append({
                            "type": "MVC_V_M_VIOLATION",
                            "file": str(file_path),
                            "message": f"WARNING: View imports Model directly. Found import statement containing 'models' in {file_path.name}",
                        })
                
                elif layer == 'Controller':
                    # Check for relative imports with Controller in name
                    relative_controller_pattern = re.compile(r'from\s+\.[^\s]*Controller|import\s+[^\s]*Controller', re.IGNORECASE)
                    if pattern_controller_controllers.search(content) or relative_controller_pattern.search(content):
                        # Parse to check if it's self-import
                        current_file_name = file_path.stem
                        # Quick check: if file name matches imported name, skip
                        if not re.search(rf'from\s+.*{re.escape(current_file_name)}|import\s+{re.escape(current_file_name)}', content, re.IGNORECASE):
                            violations.append({
                                "type": "MVC_C_C_VIOLATION",
                                "file": str(file_path),
                                "message": f"WARNING: Controller imports another Controller. Found import statement containing 'Controller' or 'controllers' in {file_path.name}",
                            })
                
                # METHOD 2: AST parsing for precise detection (catches edge cases regex might miss)
                try:
                    tree = ast.parse(content, filename=str(file_path))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            module = node.module or ''
                            imported_names = [n.name for n in node.names]
                            module_lower = module.lower() if module else ''
                            
                            if layer == 'Model':
                                if 'views' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_M_V_VIOLATION" for v in violations):
                                    violations.append({
                                        "type": "MVC_M_V_VIOLATION",
                                        "file": str(file_path),
                                        "message": f"CRITICAL: Model imports View. Found: from {module} import {', '.join(imported_names)}",
                                    })
                                if 'controllers' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_M_C_VIOLATION" for v in violations):
                                    violations.append({
                                        "type": "MVC_M_C_VIOLATION",
                                        "file": str(file_path),
                                        "message": f"CRITICAL: Model imports Controller. Found: from {module} import {', '.join(imported_names)}",
                                    })
                            
                            elif layer == 'View':
                                if 'models' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_V_M_VIOLATION" for v in violations):
                                    violations.append({
                                        "type": "MVC_V_M_VIOLATION",
                                        "file": str(file_path),
                                        "message": f"WARNING: View imports Model directly. Found: from {module} import {', '.join(imported_names)}",
                                    })
                            
                            elif layer == 'Controller':
                                current_file_name = file_path.stem
                                has_controllers_in_module = 'controllers' in module_lower
                                is_relative_import = module and module.startswith('.')
                                has_controller_in_names = any('controller' in name.lower() for name in imported_names)
                                is_relative_controller_import = is_relative_import and has_controller_in_names
                                is_self_import = any(current_file_name.lower() == name.lower() for name in imported_names)
                                
                                if (has_controllers_in_module or is_relative_controller_import) and not is_self_import:
                                    # Check if we already added this violation
                                    if not any(v.get("file") == str(file_path) and v.get("type") == "MVC_C_C_VIOLATION" for v in violations):
                                        violations.append({
                                            "type": "MVC_C_C_VIOLATION",
                                            "file": str(file_path),
                                            "message": f"WARNING: Controller imports another Controller. Found: from {module or '(relative)'} import {', '.join(imported_names)}",
                                        })
                        
                        elif isinstance(node, ast.Import):
                            imported_modules = [n.name for n in node.names]
                            for module in imported_modules:
                                module_lower = module.lower()
                                if layer == 'Model':
                                    if 'views' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_M_V_VIOLATION" for v in violations):
                                        violations.append({
                                            "type": "MVC_M_V_VIOLATION",
                                            "file": str(file_path),
                                            "message": f"CRITICAL: Model imports View. Found: import {module}",
                                        })
                                    if 'controllers' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_M_C_VIOLATION" for v in violations):
                                        violations.append({
                                            "type": "MVC_M_C_VIOLATION",
                                            "file": str(file_path),
                                            "message": f"CRITICAL: Model imports Controller. Found: import {module}",
                                        })
                                elif layer == 'View':
                                    if 'models' in module_lower and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_V_M_VIOLATION" for v in violations):
                                        violations.append({
                                            "type": "MVC_V_M_VIOLATION",
                                            "file": str(file_path),
                                            "message": f"WARNING: View imports Model directly. Found: import {module}",
                                        })
                                elif layer == 'Controller':
                                    if 'controllers' in module_lower and module != file_path.stem and not any(v.get("file") == str(file_path) and v.get("type") == "MVC_C_C_VIOLATION" for v in violations):
                                        violations.append({
                                            "type": "MVC_C_C_VIOLATION",
                                            "file": str(file_path),
                                            "message": f"WARNING: Controller imports another Controller. Found: import {module}",
                                        })
                
                except SyntaxError as se:
                    # Syntax errors already handled by regex, but add if not already present
                    if not any(v.get("file") == str(file_path) and v.get("type") == "SYNTAX_ERROR" for v in violations):
                        violations.append({
                            "type": "SYNTAX_ERROR",
                            "file": str(file_path),
                            "message": f"CRITICAL: Syntax error in file (line {se.lineno}): {se.msg}",
                        })
                    continue
                
            except Exception as e:
                print(f"[RulesAgent] Error processing {file_path.name}: {e}")
                if not any(v.get("file") == str(file_path) and v.get("type") == "PARSE_ERROR" for v in violations):
                    violations.append({
                        "type": "PARSE_ERROR",
                        "file": str(file_path),
                        "message": f"WARNING: Failed to parse file: {str(e)}",
                    })
                continue
        
        print(f"[RulesAgent] Found {len(violations)} violation(s)")
        return violations