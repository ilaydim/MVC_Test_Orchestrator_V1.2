import sys
from typing import Dict, Any, List
from pathlib import Path

from src.agents.base_coder_agent import BaseCoderAgent
from src.core.llm_client import QuotaExceededError, LLMConnectionError


class ControllerCoderAgent(BaseCoderAgent):
    """
    Specialized agent for generating Controller classes.
    Processes ALL controller files in the scaffold directory.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)
        self.category = "controller"
        print(f"[Controller Coder] Initialized - will process ALL controller files")

    def generate_code(self) -> Dict[str, Any]:
        """
        Generate code for ALL controller files.
        No limits - processes everything in the controllers directory.
        
        Returns:
            Dict with completed/failed/hallucinated files
        """
        import time
        
        print(f"\n{'='*60}")
        print(f"[CONTROLLER CODER] Processing ALL controller files")
        print(f"{'='*60}\n")
        
        architecture = self._load_architecture_data()
        
        scaffold_dir = self.scaffold_root / "controllers"
        
        if not scaffold_dir.exists():
            print(f"[ERROR] Controllers directory NOT FOUND at: {scaffold_dir}")
            return {"completed": [], "failed": [], "hallucinated": []}

        result = self._process_all_files(scaffold_dir, self.category, architecture)
        
        print(f"\n{'='*60}")
        print(f"[CONTROLLER CODER] Complete!")
        print(f"✅ Completed: {len(result['completed'])} files")
        if result['failed']:
            print(f"❌ Failed: {len(result['failed'])} files")
        if result['hallucinated']:
            print(f"🚫 Hallucinated: {len(result['hallucinated'])} files")
        print(f"{'='*60}\n")
        
        return {
            "completed": result['completed'],
            "failed": result['failed'],
            "hallucinated": result['hallucinated'],
            "output_directory": str(self.generated_root / "controllers")
        }

    def _process_all_files(self, scaffold_dir: Path, category: str, architecture: Dict[str, Any]) -> Dict[str, List]:
        """
        Process ALL files in the category directory.
        No limits - processes everything.
        
        Returns:
            Dict with 'completed', 'failed', 'hallucinated' lists
        """
        completed: List[Path] = []
        failed: List[tuple[Path, str]] = []
        hallucinated: List[tuple[Path, str]] = []
        
        skeleton_files = sorted(scaffold_dir.glob("*.py"))
        
        if not skeleton_files:
            print(f"[WARN] No controller files found in {scaffold_dir}")
            return {'completed': completed, 'failed': failed, 'hallucinated': hallucinated}
        
        print(f"[CONTROLLERS] Processing {len(skeleton_files)} files...\n")
        
        for idx, skeleton_file in enumerate(skeleton_files, 1):
            if not skeleton_file.is_file():
                continue
            
            try:
                # Step 1: Start generating
                print(f"\n[Controller Coder] 🔄 Generating: {skeleton_file.name} ({idx}/{len(skeleton_files)})...", flush=True)
                
                # Extract expected class name from skeleton
                expected_class_name = self._extract_class_name_from_file(skeleton_file)
                
                # Find matching architecture item
                arch_item = self._find_matching_architecture_item(expected_class_name, category, architecture)
                
                if not arch_item:
                    error = f"No architecture specification found for {expected_class_name}"
                    print(f"[Controller Coder] ❌ [WARN] {error}", flush=True)
                    failed.append((skeleton_file, error))
                    continue  # Continue to next file
                
                # Get relevant SRS context via RAG
                srs_context = self._get_relevant_srs_context(expected_class_name, category, arch_item)
                
                # Read skeleton (template)
                skeleton_content = skeleton_file.read_text(encoding="utf-8")
                
                # Build prompt using workflow prompt
                prompt = self._build_workflow_prompt(skeleton_content, category, expected_class_name, arch_item, srs_context, architecture)
                
                # Generate code with retry mechanism for class name validation
                max_retries = 2
                new_code = None
                is_valid = False
                validation_msg = ""
                
                for attempt in range(max_retries):
                    try:
                        # Generate code using LLM (has built-in rate limit retry)
                        new_code = self._generate_code_with_llm(prompt, skeleton_file.name)
                    except LLMConnectionError as lce:
                        # Rate limit or connection error - skip this file and continue
                        error = f"LLM connection/rate limit error: {lce}"
                        print(f"[Controller Coder] ❌ [ERROR] {error}", flush=True)
                        print(f"[Controller Coder] ⚠️ Skipping {skeleton_file.name}, continuing with next file...", flush=True)
                        failed.append((skeleton_file, error))
                        new_code = None
                        break
                    except QuotaExceededError as qe:
                        # Daily quota exceeded - re-raise to stop pipeline
                        raise
                    
                    if not new_code:
                        if attempt < max_retries - 1:
                            continue  # Retry
                        error = "LLM returned empty code"
                        print(f"[Controller Coder] ❌ [ERROR] {error}", flush=True)
                        failed.append((skeleton_file, error))
                        break
                    
                    # HALLUCINATION CHECK
                    is_valid, validation_msg = self._validate_generated_code(
                        new_code, 
                        expected_class_name, 
                        skeleton_file.name, 
                        category
                    )
                    
                    if is_valid:
                        break  # Success!
                    
                    # If validation failed and we have retries left, enhance prompt
                    if attempt < max_retries - 1:
                        # Add stricter class name requirement to prompt
                        enhanced_prompt = prompt + f"\n\n⚠️ CRITICAL: The class name MUST be exactly '{expected_class_name}'. Do NOT use '{expected_class_name.replace('Controller', '')}' or any other variation. The class definition must be: class {expected_class_name}:"
                        prompt = enhanced_prompt
                        continue
                
                # If still invalid after retries, mark as hallucinated and continue
                if not is_valid or not new_code:
                    print(f"[Controller Coder] ❌ FAILED: {validation_msg.split(':')[-1].strip()}", flush=True)
                    hallucinated.append((skeleton_file, validation_msg))
                    continue  # Continue to next file
                
                # Write to generated_src/controllers/
                output_dir = self.generated_root / "controllers"
                output_file = output_dir / skeleton_file.name
                
                output_file.write_text(new_code, encoding="utf-8")
                completed.append(output_file)
                print(f"[Controller Coder] ✅ Successfully generated and verified: {skeleton_file.name}", flush=True)
                    
            except QuotaExceededError as qe:
                # Kota doldu - stop entire pipeline gracefully
                print(f"\n{'='*60}", file=sys.stderr)
                print(f"[QUOTA EXCEEDED] Pipeline stopped!", file=sys.stderr)
                print(f"{'='*60}", file=sys.stderr)
                print(f"{str(qe)}", file=sys.stderr)
                print(f"\n[Controller Coder] Stopped at: {skeleton_file.name}", file=sys.stderr)
                print(f"[Controller Coder] Completed so far: {len(completed)} files", file=sys.stderr)
                print(f"[Controller Coder] Remaining: {len(skeleton_files) - idx} files", file=sys.stderr)
                print(f"\n💡 Solution: Wait for quota reset or use new API key", file=sys.stderr)
                print(f"{'='*60}\n", file=sys.stderr)
                break  # Exit loop, return what we have
                
            except LLMConnectionError as lce:
                # Connection error - log and skip this file, continue to next
                error = f"LLM connection failed: {lce}"
                print(f"[Controller Coder] ❌ [ERROR] {error}", flush=True)
                print(f"[Controller Coder] ⚠️ Skipping {skeleton_file.name}, continuing with next file...", flush=True)
                failed.append((skeleton_file, error))
                continue  # Continue to next file
                
            except Exception as e:
                # Unexpected error - log with debug info and skip, continue to next file
                error = f"Unexpected error: {str(e)}"
                print(f"[Controller Coder] ❌ [ERROR] {error}", flush=True)
                print(f"[Controller Coder] DEBUG ERROR: {type(e).__name__}: {str(e)}", flush=True)
                print(f"[Controller Coder] ⚠️ Skipping {skeleton_file.name}, continuing with next file...", flush=True)
                failed.append((skeleton_file, error))
                continue  # Continue to next file
        
        return {
            'completed': completed,
            'failed': failed,
            'hallucinated': hallucinated
        }

