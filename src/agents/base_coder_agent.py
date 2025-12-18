import json
import re
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 
from src.core.llm_client import QuotaExceededError, LLMConnectionError


class BaseCoderAgent(BaseArchitectAgent):
    """
    Base class for specialized coder agents (ModelCoder, ViewCoder, ControllerCoder).
    Contains shared functionality for code generation.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        # Project root
        project_root = Path(__file__).resolve().parents[2]
        
        # Scaffold root (READ-ONLY template)
        self.scaffold_root = project_root / "scaffolds" / "mvc_skeleton"
        
        # Generated source root (OUTPUT directory)
        self.generated_root = project_root / "generated_src"
        
        # Create directory structure with proper error handling
        try:
            self.generated_root.mkdir(parents=True, exist_ok=True)
            
            # Create category directories
            (self.generated_root / "models").mkdir(parents=True, exist_ok=True)
            (self.generated_root / "views").mkdir(parents=True, exist_ok=True)
            (self.generated_root / "controllers").mkdir(parents=True, exist_ok=True)
            (self.generated_root / "config").mkdir(parents=True, exist_ok=True)
            
        except PermissionError as pe:
            error_msg = (
                f"\n{'='*60}\n"
                f"[FATAL ERROR] Permission denied when creating directories!\n"
                f"{'='*60}\n"
                f"Target directory: {self.generated_root}\n"
                f"Error: {pe}\n\n"
                f"Solutions:\n"
                f"  1. Run VS Code/terminal as Administrator (Windows)\n"
                f"  2. Check folder permissions: chmod 755 {project_root}\n"
                f"  3. Check if folder is locked by another process\n"
                f"  4. Try closing VS Code and reopening\n"
                f"{'='*60}\n"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(f"Failed to create output directories: {pe}")
            
        except OSError as oe:
            error_msg = (
                f"\n{'='*60}\n"
                f"[FATAL ERROR] Failed to create output directories!\n"
                f"{'='*60}\n"
                f"Target directory: {self.generated_root}\n"
                f"Error: {oe}\n\n"
                f"Possible causes:\n"
                f"  - Disk full\n"
                f"  - Invalid path characters\n"
                f"  - Path too long (Windows: max 260 chars)\n"
                f"  - Drive not accessible\n\n"
                f"Current path length: {len(str(self.generated_root))} chars\n"
                f"{'='*60}\n"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(f"Failed to create output directories: {oe}")
            
        except Exception as e:
            error_msg = (
                f"\n{'='*60}\n"
                f"[FATAL ERROR] Unexpected error creating directories!\n"
                f"{'='*60}\n"
                f"Target directory: {self.generated_root}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error: {e}\n"
                f"{'='*60}\n"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(f"Failed to initialize Coder Agent: {e}")

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
    
    def _extract_class_name_from_code(self, code: str) -> Optional[str]:
        """Extracts the class name from generated code."""
        match = re.search(r'class\s+(\w+)', code)
        return match.group(1) if match else None
    
    def _validate_generated_code(self, code: str, expected_class_name: str, expected_file_name: str, category: str) -> tuple[bool, str]:
        """
        Validates generated code for hallucinations and naming consistency.
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: Extract actual class name from code
        actual_class_name = self._extract_class_name_from_code(code)
        
        if not actual_class_name:
            return False, "❌ VALIDATION FAILED: No class definition found in generated code"
        
        # Check 2: Class name must match architecture specification EXACTLY
        if actual_class_name != expected_class_name:
            return False, f"❌ HALLUCINATION DETECTED: Expected class '{expected_class_name}' but got '{actual_class_name}'"
        
        # Check 3: Code must not be too short (likely placeholder)
        if len(code) < 200:
            return False, f"❌ VALIDATION FAILED: Generated code too short ({len(code)} chars), likely placeholder"
        
        # Check 4: Must contain 'def __init__' or meaningful methods
        if 'def __init__' not in code and 'def ' not in code:
            return False, "❌ VALIDATION FAILED: No methods found, code incomplete"
        
        # Check 5: Must not contain obvious hallucinated suffixes
        hallucinated_suffixes = ['Model', 'Entity', 'DTO', 'Schema', 'Info', 'Data']
        for suffix in hallucinated_suffixes:
            if actual_class_name.endswith(suffix) and not expected_class_name.endswith(suffix):
                return False, f"❌ HALLUCINATION: Class name has unexpected suffix '{suffix}'"
        
        # All checks passed
        return True, f"✅ VALIDATION PASSED: {actual_class_name} in {expected_file_name}"

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
        LIMITED to keep prompts short and fast.
        """
        if not self.rag or not hasattr(self.rag, 'search'):
            # Fallback: try to get limited SRS
            try:
                srs_path = self.data_dir / "srs_document.txt"
                if srs_path.exists():
                    return srs_path.read_text(encoding="utf-8")[:500]  # Reduced from 3000 to 500
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
            result = self.rag.search(query, k=2)
            documents = result.get("documents", [])
            if documents and documents[0]:
                # Combine relevant chunks - LIMITED
                chunks = documents[0][:2]  # Reduced from 3 to 2
                combined = "\n\n".join(chunks)
                return combined[:500] if len(combined) > 500 else combined  # Limit total to 500 chars
        except Exception as e:
            print(f"[WARN] RAG search failed for {class_name}: {e}")
        
        # Fallback to limited SRS
        try:
            srs_path = self.data_dir / "srs_document.txt"
            if srs_path.exists():
                return srs_path.read_text(encoding="utf-8")[:500]  # Reduced from 3000 to 500
        except:
            pass
        
        return "SRS content not available."

    def _generate_code_with_llm(self, prompt: str, filename: str) -> Optional[str]:
        """Generates code using LLM with error handling and rate limit retry."""
        import time
        
        max_retries = 3
        base_delay = 2  # Base delay between requests (rate limiting)
        
        for attempt in range(max_retries):
            try:
                # Add delay between requests to avoid rate limits (except first request)
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                    print(f"[LLM] Waiting {delay}s before retry...", flush=True)
                    time.sleep(delay)
                elif attempt == 0 and hasattr(self, '_last_request_time'):
                    # Add small delay between consecutive requests
                    elapsed = time.time() - self._last_request_time
                    if elapsed < 1.0:  # If less than 1 second since last request
                        wait_time = 1.0 - elapsed
                        time.sleep(wait_time)
                
                # Use LLMClient's generate_content method
                response_text = self.llm.generate_content(prompt)
                
                # Track request time for rate limiting
                self._last_request_time = time.time()
                
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
                    
            except QuotaExceededError as qe:
                # Daily quota doldu - re-raise to stop entire pipeline
                print(f"[Coder Agent] Quota exceeded while processing {filename}")
                raise  # Stop pipeline (caught in _process_category)
                
            except LLMConnectionError as lce:
                # Rate limit or connection error - retry with delay
                error_msg = str(lce)
                if "rate limit" in error_msg.lower() and attempt < max_retries - 1:
                    # Extract retry delay from error message
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)\s*seconds?', error_msg, re.IGNORECASE)
                    if match:
                        retry_delay = float(match.group(1))
                        retry_delay = min(retry_delay, 30)  # Max 30 seconds
                    else:
                        retry_delay = 5  # Default 5 seconds
                    
                    print(f"[LLM] Rate limit hit, waiting {retry_delay:.0f}s before retry ({attempt+1}/{max_retries})...", flush=True)
                    time.sleep(retry_delay)
                    continue  # Retry
                else:
                    # Connection error or max retries reached
                    if attempt < max_retries - 1:
                        print(f"[LLM] Connection error, retrying ({attempt+1}/{max_retries})...", flush=True)
                        continue
                    else:
                        print(f"[ERROR] LLM connection failed for {filename} after {max_retries} attempts: {lce}")
                        raise  # Stop pipeline after max retries
                
            except Exception as e:
                # Other errors - retry once, then return None
                if attempt < max_retries - 1:
                    print(f"[LLM] Error occurred, retrying ({attempt+1}/{max_retries}): {e}", flush=True)
                    time.sleep(2)
                    continue
                else:
                    print(f"[ERROR] LLM generation failed for {filename} after {max_retries} attempts: {e}")
                    return None
        
        return None  # All retries exhausted

    def _build_workflow_prompt(self, skeleton: str, category: str, class_name: str, 
                              arch_item: Optional[Dict[str, Any]], srs_context: str, 
                              architecture: Dict[str, Any]) -> str:
        """
        Builds prompt using the new workflow prompt template.
        Falls back to simple prompt if template not found.
        """
        # Load workflow prompt template
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "coder_agent_workflow.prompt.md"
        
        if not prompt_path.exists():
            # Use simple, basic prompt instead of complex legacy prompt
            return self._build_simple_prompt(skeleton, category, class_name, arch_item, srs_context, architecture)
        
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        # Prepare variables - LIMIT context to keep it short
        arch_spec = json.dumps(arch_item, indent=2) if arch_item else "No specification found"
        if len(arch_spec) > 500:
            arch_spec = arch_spec[:500] + "..."
        
        # Limit SRS context
        srs_limited = srs_context[:500] if len(srs_context) > 500 else srs_context
        
        file_name = class_name.lower() + ".py"
        
        # Build prompt by replacing variables
        prompt = prompt_template.replace("{{category}}", category)
        prompt = prompt.replace("{{class_name}}", class_name)
        prompt = prompt.replace("{{file_name}}", file_name)
        prompt = prompt.replace("{{skeleton}}", skeleton)
        prompt = prompt.replace("{{arch_spec}}", arch_spec)
        prompt = prompt.replace("{{srs_context}}", srs_limited)
        
        # Add SIMPLE directive at the end
        prompt += "\n\n⚠️ IMPORTANT: Keep code SIMPLE and SHORT. Use basic implementations only. 20-40 lines per method max."
        
        # Add related models/views for controllers (limited)
        if category == "controller":
            related_models = json.dumps(architecture.get("model", [])[:2], indent=2)  # Reduced from 3 to 2
            related_views = json.dumps(architecture.get("view", [])[:2], indent=2)
            prompt = prompt.replace("{{related_models}}", related_models)
            prompt = prompt.replace("{{related_views}}", related_views)
        else:
            # Remove conditional blocks for non-controllers
            prompt = re.sub(r'\{\{#if related_models\}\}.*?\{\{/if\}\}', '', prompt, flags=re.DOTALL)
            prompt = re.sub(r'\{\{#if related_views\}\}.*?\{\{/if\}\}', '', prompt, flags=re.DOTALL)
        
        return prompt
    
    def _build_simple_prompt(self, skeleton: str, category: str, class_name: str,
                            arch_item: Optional[Dict[str, Any]], srs_context: str,
                            architecture: Dict[str, Any]) -> str:
        """
        Builds a SIMPLE, BASIC prompt for code generation.
        Focuses on speed and simplicity.
        """
        # Limit context to keep prompt short
        arch_info = json.dumps(arch_item, indent=2) if arch_item else "No specification"
        if len(arch_info) > 300:
            arch_info = arch_info[:300] + "..."
        
        srs_limited = srs_context[:300] if len(srs_context) > 300 else srs_context
        
        if category == "controller":
            return f"""Write SIMPLE code for {class_name} controller.

⚠️ CLASS NAME MUST BE: {class_name} (use exactly: class {class_name}:)

Skeleton:
{skeleton}

Requirements:
- Return ONLY Python code
- Keep it SHORT (20-40 lines per method)
- Use BASIC implementations
- Brief docstrings only
- NO complex features

Context (brief):
{arch_info[:200]}
{srs_limited[:200]}

Return SIMPLE code:"""
        else:
            return f"""Write SIMPLE code for {class_name} {category}.

⚠️ CLASS NAME MUST BE: {class_name} (use exactly: class {class_name}:)

Skeleton:
{skeleton}

Requirements:
- Return ONLY Python code
- Keep it SHORT (20-40 lines per method)
- Use BASIC implementations
- Brief docstrings only

Context (brief):
{arch_info[:200]}
{srs_limited[:200]}

Return SIMPLE code:"""
    
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
        # Limit context to keep prompt short
        arch_limited = arch_info[:300] if len(arch_info) > 300 else arch_info
        srs_limited = srs_context[:300] if len(srs_context) > 300 else srs_context
        
        # Load prompt from external file if exists
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "generate_model_code.prompt.md"
        
        if prompt_path.exists():
            prompt_template = prompt_path.read_text(encoding="utf-8")
            # Replace variables in template
            prompt = prompt_template.replace("{{class_name}}", class_name)
            prompt = prompt.replace("{{arch_info}}", arch_limited)
            prompt = prompt.replace("{{srs_context}}", srs_limited)
            prompt = prompt.replace("{{skeleton}}", skeleton)
            # Add simple directive
            prompt += "\n\n⚠️ IMPORTANT: Keep code SIMPLE and SHORT. Use basic implementations only."
        else:
            # Use simple fallback - try to parse arch_info if it's JSON
            try:
                arch_dict = json.loads(arch_info) if arch_info.startswith("{") else None
            except:
                arch_dict = None
            prompt = self._build_simple_prompt(skeleton, "model", class_name, arch_dict, srs_limited, {})
        
        return prompt

    def _build_view_prompt(self, skeleton: str, class_name: str, arch_info: str, srs_context: str) -> str:
        # Limit context to keep prompt short
        arch_limited = arch_info[:300] if len(arch_info) > 300 else arch_info
        srs_limited = srs_context[:300] if len(srs_context) > 300 else srs_context
        
        # Load prompt from external file if exists
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "generate_view_code.prompt.md"
        
        if prompt_path.exists():
            prompt_template = prompt_path.read_text(encoding="utf-8")
            # Replace variables in template
            prompt = prompt_template.replace("{{class_name}}", class_name)
            prompt = prompt.replace("{{arch_info}}", arch_limited)
            prompt = prompt.replace("{{srs_context}}", srs_limited)
            prompt = prompt.replace("{{skeleton}}", skeleton)
            # Add simple directive
            prompt += "\n\n⚠️ IMPORTANT: Keep code SIMPLE and SHORT. Use basic implementations only."
        else:
            # Use simple fallback - try to parse arch_info if it's JSON
            try:
                arch_dict = json.loads(arch_info) if arch_info.startswith("{") else None
            except:
                arch_dict = None
            prompt = self._build_simple_prompt(skeleton, "view", class_name, arch_dict, srs_limited, {})
        
        return prompt

    def _build_controller_prompt(self, skeleton: str, class_name: str, arch_info: str, 
                                srs_context: str, architecture: Dict[str, Any]) -> str:
        # Limit context to keep prompt short
        arch_limited = arch_info[:300] if len(arch_info) > 300 else arch_info
        srs_limited = srs_context[:300] if len(srs_context) > 300 else srs_context
        
        # Get related models and views for context (reduced)
        related_models = json.dumps(architecture.get("model", [])[:2], indent=2)  # Reduced from 3 to 2
        related_views = json.dumps(architecture.get("view", [])[:2], indent=2)
        
        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "generate_controller_code.prompt.md"
        
        if prompt_path.exists():
            prompt_template = prompt_path.read_text(encoding="utf-8")
            # Replace variables in template
            prompt = prompt_template.replace("{{class_name}}", class_name)
            prompt = prompt.replace("{{arch_info}}", arch_limited)
            prompt = prompt.replace("{{srs_context}}", srs_limited)
            prompt = prompt.replace("{{skeleton}}", skeleton)
            prompt = prompt.replace("{{related_models}}", related_models)
            prompt = prompt.replace("{{related_views}}", related_views)
            # Add simple directive
            prompt += "\n\n⚠️ IMPORTANT: Keep code SIMPLE and SHORT. Use basic implementations only. 20-40 lines per method max."
        else:
            # Use simple fallback - try to parse arch_info if it's JSON
            try:
                arch_dict = json.loads(arch_info) if arch_info.startswith("{") else None
            except:
                arch_dict = None
            prompt = self._build_simple_prompt(skeleton, "controller", class_name, arch_dict, srs_limited, architecture)
        
        return prompt

    def _build_generic_prompt(self, skeleton: str, category: str, class_name: str, 
                            arch_info: str, srs_context: str) -> str:
        return f"""You are a Python developer. Write SIMPLE, BASIC code for the {class_name} {category} class.

### ⚠️ CRITICAL CLASS NAME:
The class MUST be named exactly '{class_name}'. Use: class {class_name}:

### TASK:
Fill the skeleton with SIMPLE, BASIC implementations. Keep it SHORT.

### CURRENT SKELETON:
{skeleton}

### SIMPLE REQUIREMENTS:
- Return ONLY Python code, no explanations
- Class name MUST be: {class_name}
- Keep code SHORT (20-40 lines max per method)
- Use BASIC implementations - simple logic only
- Add brief docstrings (1 line)
- NO complex features, keep it simple

### CONTEXT (for reference only):
Architecture: {arch_info[:500]}
SRS: {srs_context[:500]}

Return SIMPLE Python code:"""

