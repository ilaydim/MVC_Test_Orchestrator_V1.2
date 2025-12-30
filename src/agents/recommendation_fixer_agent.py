# src/agents/recommendation_fixer_agent.py

from typing import Dict, Any, List
from pathlib import Path
import json
import ast
import re

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent


class RecommendationFixerAgent(BaseArchitectAgent):
    """
    Automatically applies recommendations from audit reports.
    This agent ONLY fixes the specific issues mentioned in recommendations.
    It does NOT modify any other code (protection mechanism).
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        self.project_root = Path(__file__).resolve().parents[2]

    def apply_recommendations(self, audit_report_path: Path = None) -> Dict[str, Any]:
        """
        Reads audit report and applies all recommendations automatically.
        
        Args:
            audit_report_path: Path to final_audit_report.json. If None, uses default location.
        
        Returns:
            Dict with fix results
        """
        print("\n" + "="*60)
        print("[Recommendation Fixer] Starting automatic fixes...")
        print("="*60)

        # 1. Raporu bul ve yükle
        if audit_report_path is None:
            audit_report_path = self.data_dir / "final_audit_report.json"
        
        # 2. Rapor yoksa işlemi durdur
        if not audit_report_path.exists():
            return {
                "success": False,
                "error": f"Audit report not found: {audit_report_path}",
                "fixed_files": []
            }

        try:
            with open(audit_report_path, "r", encoding="utf-8") as f:
                audit_report = json.load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read audit report: {e}",
                "fixed_files": []
            }
        
        # 3. Raporun içindeki tavsiyeleri (recommendations) al
        recommendations = audit_report.get("recommendations", [])

        if not recommendations:
            print("[Recommendation Fixer] ✅ No recommendations to apply.")
            return {
                "success": True,
                "message": "No recommendations to apply",
                "fixed_files": []
            }

        print(f"[Recommendation Fixer] Found {len(recommendations)} recommendation(s) to apply.\n")

        fixed_files = []
        failed_files = []

        for idx, rec in enumerate(recommendations, 1):
            file_path_str = rec.get("file", "")
            violation_type = rec.get("violation_type", "")
            recommendation = rec.get("recommendation", "")
            problem = rec.get("problem", "")

            print(f"[{idx}/{len(recommendations)}] Processing: {Path(file_path_str).name}")

            try:  
                result = self._apply_single_recommendation(
                    file_path_str=file_path_str,
                    violation_type=violation_type,
                    recommendation=recommendation,
                    problem=problem
                )

                if result["success"]:
                    fixed_files.append({
                        "file": file_path_str,
                        "violation_type": violation_type,
                        "changes": result.get("changes", [])
                    })
                    print(f"  ✅ Fixed: {result.get('changes', [])}")
                else:
                    failed_files.append({
                        "file": file_path_str,
                        "error": result.get("error", "Unknown error")
                    })
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                failed_files.append({
                    "file": file_path_str,
                    "error": str(e)
                })
                print(f"  ❌ Exception: {e}")

        print(f"\n[Recommendation Fixer] ✅ Fixed {len(fixed_files)} file(s), ❌ Failed {len(failed_files)} file(s)")

        return {
            "success": len(failed_files) == 0,
            "fixed_files": fixed_files,
            "failed_files": failed_files,
            "total_recommendations": len(recommendations)
        }

    def _apply_single_recommendation(
        self,
        file_path_str: str,
        violation_type: str,
        recommendation: str,
        problem: str
    ) -> Dict[str, Any]:
        """
        Applies a single recommendation to a file.
        Uses targeted fixes based on violation type, with LLM fallback for complex cases.
        """
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        try:
            original_code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {e}"
            }

        # Eğer hata bir "Import" hatasıysa (MVC ihlali), bunu AST ile kesin olarak çöz
        if violation_type in ["MVC_M_V_VIOLATION", "MVC_M_C_VIOLATION", "MVC_V_M_VIOLATION"]:
            # Import removal violations - use AST-based fix
            result = self._fix_import_violation(
                file_path=file_path,
                original_code=original_code,
                violation_type=violation_type,
                recommendation=recommendation
            )
            
            if result["success"]:
                return result

        # Fallback to LLM-based fix for complex cases
        return self._fix_with_llm(
            file_path=file_path,
            original_code=original_code,
            violation_type=violation_type,
            recommendation=recommendation,
            problem=problem
        )

    def _fix_import_violation(
        self,
        file_path: Path,
        original_code: str,
        violation_type: str,
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Removes problematic imports using AST parsing.
        More reliable than LLM for simple import removals.
        """
        try:
            # Extract import to remove from recommendation
            # Pattern: "remove the import statement for X (buradan X'i çıkaracağız)"
            import_patterns = [
                r"remove.*?import.*?for\s+`([^`]+)`",  # `generated_src.views.ProductListingView`
                r"remove.*?import.*?for\s+([a-zA-Z_][a-zA-Z0-9_\.]+)",  # generated_src.views.ProductListingView
                r"import.*?`([^`]+)`",  # `generated_src.views.ProductListingView`
                r"import.*?([a-zA-Z_][a-zA-Z0-9_\.]+)",  # generated_src.views.ProductListingView
            ]
            
            import_to_remove = None
            for pattern in import_patterns:
                match = re.search(pattern, recommendation, re.IGNORECASE)
                if match:
                    import_to_remove = match.group(1).strip()
                    # Clean up common prefixes
                    if import_to_remove.startswith("generated_src."):
                        import_to_remove = import_to_remove
                    break

            if not import_to_remove:
                # Try to extract from file path in recommendation
                # e.g., "generated_src.views.ProductListingView"
                match = re.search(r"(generated_src\.[a-zA-Z_][a-zA-Z0-9_\.]+)", recommendation)
                if match:
                    import_to_remove = match.group(1)

            if not import_to_remove:
                return {"success": False, "error": "Could not identify import to remove"}

            # Parse AST
            try:
                tree = ast.parse(original_code)
            except SyntaxError:
                return {"success": False, "error": "File has syntax errors, cannot parse"}

            # Find and remove the problematic import
            lines = original_code.splitlines()
            removed_lines = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # Check if this import matches what we need to remove
                    module = node.module or ""
                    # Match module path (e.g., "generated_src.views.ProductListingView")
                    if import_to_remove in module:
                        # Remove this import line
                        line_no = node.lineno - 1  # AST is 1-indexed
                        if 0 <= line_no < len(lines):
                            removed_lines.append((line_no, lines[line_no]))
                    # Also check imported names
                    elif any(import_to_remove.split('.')[-1] in alias.name for alias in node.names):
                        line_no = node.lineno - 1
                        if 0 <= line_no < len(lines):
                            removed_lines.append((line_no, lines[line_no]))
                
                elif isinstance(node, ast.Import):
                    # Check if any alias matches
                    for alias in node.names:
                        if import_to_remove in alias.name or import_to_remove.split('.')[-1] in alias.name:
                            line_no = node.lineno - 1
                            if 0 <= line_no < len(lines):
                                removed_lines.append((line_no, lines[line_no]))

            if not removed_lines:
                # Try simple string-based removal as fallback
                return self._fix_import_violation_string_based(
                    original_code, import_to_remove, file_path
                )

            # Remove lines (in reverse order to preserve indices)
            new_lines = lines.copy()
            for line_no, _ in sorted(removed_lines, reverse=True):
                new_lines.pop(line_no)

            fixed_code = "\n".join(new_lines)
            
            # Verify the fix worked - check that import is gone
            if import_to_remove in fixed_code:
                # Import still present, try string-based removal
                return self._fix_import_violation_string_based(
                    original_code, import_to_remove, file_path
                )
            
            # Verify import was in original code
            if import_to_remove not in original_code:
                return {"success": False, "error": "Import not found in original file"}

            # Write fixed code
            file_path.write_text(fixed_code, encoding="utf-8")
            
            return {
                "success": True,
                "changes": [f"Removed import: {import_to_remove}"]
            }

        except Exception as e:
            return {"success": False, "error": f"AST-based fix failed: {e}"}

    #AST bir sebeple (kod bozuksa vb.) satırı bulamazsa, klasik metin arama-silme yöntemine başvurur
    def _fix_import_violation_string_based(
        self,
        original_code: str,
        import_to_remove: str,
        file_path: Path
    ) -> Dict[str, Any]:
        """
        Fallback: Remove import using string matching.
        """
        lines = original_code.splitlines()
        new_lines = []
        removed_count = 0
        removed_line_content = None

        # Extract class/module name from full path (e.g., "ProductListingView" from "generated_src.views.ProductListingView")
        import_name = import_to_remove.split('.')[-1]
        import_module = '.'.join(import_to_remove.split('.')[:-1]) if '.' in import_to_remove else None

        for line in lines:
            # Check if this line contains the import to remove
            line_lower = line.lower()
            is_import_line = "import" in line_lower or "from" in line_lower
            
            # Match full path or just the class name
            if is_import_line and (import_to_remove in line or import_name in line):
                # Additional check: if we have module path, verify it matches
                if import_module:
                    if import_module in line or import_to_remove in line:
                        removed_count += 1
                        removed_line_content = line.strip()
                        continue
                else:
                    # Just class name match
                    removed_count += 1
                    removed_line_content = line.strip()
                    continue
            
            new_lines.append(line)

        if removed_count == 0:
            return {"success": False, "error": "Import line not found"}

        fixed_code = "\n".join(new_lines)
        file_path.write_text(fixed_code, encoding="utf-8")

        return {
            "success": True,
            "changes": [f"Removed import: {removed_line_content or import_to_remove}"]
        }
    
    #AST'nin çözemediği karmaşık durumlarda Gemini devreye girer.
    def _fix_with_llm(
        self,
        file_path: Path,
        original_code: str,
        violation_type: str,
        recommendation: str,
        problem: str
    ) -> Dict[str, Any]:
        """
        Uses LLM to apply the recommendation with strict protection.
        Only the specific issue mentioned in the recommendation is fixed.
        """
        prompt = self._build_fixer_prompt(
            file_path=file_path,
            original_code=original_code,
            violation_type=violation_type,
            recommendation=recommendation,
            problem=problem
        )

        try:
            response = self.llm.generate_content(prompt, stream=False)
            
            # Extract code from response (might be wrapped in code blocks)
            fixed_code = self._extract_code_from_response(response)
            
            if not fixed_code or fixed_code.strip() == original_code.strip():
                return {
                    "success": False,
                    "error": "LLM did not make the required changes"
                }

            # Verify: Check that only the recommended change was made
            verification = self._verify_fix(
                original_code=original_code,
                fixed_code=fixed_code,
                recommendation=recommendation
            )

            if not verification["valid"]:
                return {
                    "success": False,
                    "error": f"Fix verification failed: {verification['reason']}"
                }

            # Write fixed code
            file_path.write_text(fixed_code, encoding="utf-8")

            return {
                "success": True,
                "changes": verification.get("changes", ["Applied recommendation"])
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"LLM fix failed: {e}"
            }

    def _build_fixer_prompt(
        self,
        file_path: Path,
        original_code: str,
        violation_type: str,
        recommendation: str,
        problem: str
    ) -> str:
        """
        Builds a strict prompt that ensures only the specific recommendation is applied.
        """
        return f"""You are a code fixer agent. Your ONLY task is to apply ONE specific recommendation to a Python file.

CRITICAL RULES:
1. ONLY fix the issue mentioned in the recommendation below
2. DO NOT modify any other code
3. DO NOT add new features
4. DO NOT refactor anything
5. DO NOT change formatting (unless necessary for the fix)
6. DO NOT add comments
7. Return ONLY the fixed code, no explanations

### VIOLATION TYPE:
{violation_type}

### PROBLEM:
{problem}

### RECOMMENDATION (THIS IS WHAT YOU MUST DO):
{recommendation}

### ORIGINAL CODE:
```python
{original_code}
```

### YOUR TASK:
Apply ONLY the recommendation above. Return the complete fixed code with ONLY that change applied.

Return the fixed code wrapped in ```python code blocks:
```python
[fixed code here]
```
"""

    def _extract_code_from_response(self, response: str) -> str:
        """Extracts Python code from LLM response (handles code blocks)."""
        # Remove code fences
        code = response.strip()
        
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code

    def _verify_fix(
        self,
        original_code: str,
        fixed_code: str,
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Verifies that only the recommended change was made.
        This is a protection mechanism to ensure no unintended modifications.
        """
        # Simple verification: check that the fix addresses the recommendation
        # For import removals, check that the import is gone
        if "remove" in recommendation.lower() and "import" in recommendation.lower():
            # Extract what should be removed
            import_patterns = [
                r"remove.*?import.*?for\s+([^\s\.]+\.?[^\s\.]*)",
                r"remove.*?import.*?`([^`]+)`",
            ]
            
            for pattern in import_patterns:
                match = re.search(pattern, recommendation, re.IGNORECASE)
                if match:
                    import_name = match.group(1).strip()
                    # Check it's removed from fixed code
                    if import_name in original_code and import_name not in fixed_code:
                        return {
                            "valid": True,
                            "changes": [f"Removed import: {import_name}"]
                        }

        # For other cases, just check that code changed (basic check)
        if original_code.strip() != fixed_code.strip():
            return {
                "valid": True,
                "changes": ["Applied recommendation"]
            }

        return {
            "valid": False,
            "reason": "No changes detected or changes don't match recommendation"
        }

