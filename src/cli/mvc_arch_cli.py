# Disable telemetry to prevent crashes
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import argparse
import json
import re
import sys
import time
import traceback
from pathlib import Path

from src.rag.rag_pipeline import RAGPipeline 
from src.core.llm_client import LLMClient, QuotaExceededError, LLMConnectionError 
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder
from src.agents.recommendation_fixer_agent import RecommendationFixerAgent
from src.agents.srs_writer_agent import SRSWriterAgent
from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.agents.rules_agent import RulesAgent
from src.agents.reviewer_agent import ReviewerAgent


def _run_extraction_pipeline(
    user_idea: str = None,
    srs_path: Path = None,
    output_path: Path = None,
):
    """Common architecture extraction logic. MODULAR: Only Architect Agent, writes to disk only."""

    print("[INFO] Initializing RAG and LLM Clients...")
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Client initialization failed: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    print("[INFO] Initializing SRS Writer and Architect Agents...")
    try:
        srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
        requirements_agent = RequirementsAgent(rag_pipeline, llm_client)
        model_agent = ModelArchitectAgent(rag_pipeline, llm_client)
        controller_agent = ControllerArchitectAgent(rag_pipeline, llm_client)
        view_agent = ViewArchitectAgent(rag_pipeline, llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Agent initialization failed: {e}")
        sys.exit(1)

    current_srs_path: Path | None = None

    if user_idea:
        print(f"[INFO] Generating SRS from user idea: '{user_idea[:40]}...'")
        try:
            current_srs_path = srs_writer.generate_srs(user_idea)
        except QuotaExceededError as qe:
            print(f"\n{str(qe)}")
            print("\n[CLI] Pipeline stopped. No files were modified.")
            sys.exit(0)
        except LLMConnectionError as lce:
            print(f"\n[FATAL ERROR] LLM connection failed: {lce}")
            sys.exit(1)
        except Exception as e:
            print(f"[FATAL ERROR] SRS generation failed: {e}")
            sys.exit(1)

    elif srs_path:
        current_srs_path = srs_path
        print(f"[INFO] Using existing SRS: {current_srs_path.name}")
        if not current_srs_path.exists():
            print(f"[FATAL ERROR] SRS file not found: {current_srs_path}")
            sys.exit(1)

    else:
        print("[FATAL ERROR] No user idea or SRS path provided for extraction/creation.")
        sys.exit(1)

    if output_path is None:
        print("[FATAL ERROR] No output path provided for architecture JSON.")
        sys.exit(1)

    print(f"PHASE 0.5: Indexing SRS file: {current_srs_path.name}")
    rag_pipeline.index_srs(current_srs_path)
    
    print("PHASE 1-2: Extracting MVC Architecture (Extraction Only)...")
    from src.core.config import DEFAULT_TOP_K
    
    requirements_analysis = requirements_agent.extract_analysis(k=DEFAULT_TOP_K)
    model_json = model_agent.extract_models(k=DEFAULT_TOP_K)
    controller_json = controller_agent.extract_controllers(k=DEFAULT_TOP_K)
    view_json = view_agent.extract_views(k=DEFAULT_TOP_K)
    
    architecture_map = {
        "model": model_json.get("model", []),
        "view": view_json.get("view", []),
        "controller": controller_json.get("controller", []),
    }
    
    model_agent.save_output(architecture_map, "architecture_map.json")
    
    try:
        srs_context = rag_pipeline.get_full_context()
    except AttributeError:
        srs_context = "SRS context extraction failed."

    full_data = {
        "srs": srs_context,
        "architecture": architecture_map
    }

    output_path_str = str(Path(str(output_path)).resolve())
    with open(output_path_str, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)
    
    print(f"[SUCCESS] Extraction complete. JSON written to: {output_path_str}")


def cmd_create_srs(args: argparse.Namespace) -> None:
    """Generate SRS from user idea."""
    try:
        output_path = Path(str(args.output)).resolve()
        user_idea = args.user_idea

        # 1) Bağımlılıkları Başlat (LLM için gerekli)
        print("[INFO] Initializing RAG and LLM Clients for SRS creation...")
        try:
            llm_client = LLMClient()
            rag_pipeline = RAGPipeline(llm_client=llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Client initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        print("[INFO] Initializing SRS Writer Agent...")
        try:
            srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Agent initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        try:
            srs_path = srs_writer.generate_srs(user_idea)
        except QuotaExceededError as qe:
            print(f"\n{str(qe)}")
            print("\n[CLI] SRS creation stopped. No files were created.")
            sys.exit(0)
        except LLMConnectionError as lce:
            print(f"\n[FATAL ERROR] LLM connection failed: {lce}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        except Exception as e:
            print(f"[FATAL ERROR] SRS generation failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            final_srs_path = srs_path.replace(output_path)
        except Exception:
            content = srs_path.read_text(encoding="utf-8")
            output_path.write_text(content, encoding="utf-8")
            final_srs_path = output_path

        print(f"[SUCCESS] SRS created successfully at: {final_srs_path}")
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Create-SRS command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


def cmd_extract(args: argparse.Namespace) -> None:
    """Extract architecture from SRS. Only runs Architect Agent."""
    try:
        # Normalize all paths to handle Windows backslashes
        output_path = Path(str(args.output)).resolve()
        srs_path = Path(str(args.srs_path)).resolve()
        
        if not srs_path.exists():
            print(f"[ERROR] SRS file not found: {srs_path}")
            sys.exit(1)

        _run_extraction_pipeline(srs_path=srs_path, output_path=str(output_path))
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Extract command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)

# Legacy alias for backward compatibility
def cmd_index_srs(args: argparse.Namespace) -> None:
    """Legacy alias for extract command."""
    cmd_extract(args)


def cmd_scaffold(args: argparse.Namespace) -> None:
    """Generate scaffold files. Only runs Scaffolder Agent (no LLM)."""
    try:
        arch_path = Path(str(args.arch_path)).resolve()

        if not arch_path.exists():
            print(f"[ERROR] Architecture JSON not found: {arch_path}")
            print(f"[ERROR] Please run 'extract' command first to generate architecture_map.json")
            sys.exit(1)

        # Validate JSON structure
        try:
            with arch_path.open("r", encoding="utf-8") as f:
                full_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON file: {arch_path}")
            print(f"[ERROR] JSON parse error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to read architecture file: {e}")
            sys.exit(1)

        # Extract architecture from JSON structure
        if "architecture" in full_data:
            architecture = full_data["architecture"]
            print(f"[INFO] Using 'architecture' key from JSON structure.")
        else:
            architecture = full_data
            print(f"[INFO] Using root-level architecture structure.")

        # Validate architecture structure
        if not isinstance(architecture, dict):
            print(f"[ERROR] Invalid architecture structure: expected dict, got {type(architecture)}")
            sys.exit(1)
        
        required_keys = ["model", "view", "controller"]
        missing_keys = [key for key in required_keys if key not in architecture]
        if missing_keys:
            print(f"[ERROR] Missing required architecture keys: {missing_keys}")
            print(f"[ERROR] Architecture file may be corrupted or incomplete.")
            sys.exit(1)

        # Check if architecture is empty
        total_items = sum(len(architecture.get(key, [])) for key in required_keys)
        if total_items == 0:
            print(f"[ERROR] Architecture is empty. No models, views, or controllers found.")
            print(f"[ERROR] Please run 'extract' command again to regenerate architecture.")
            sys.exit(1)

        # Run Scaffolder (no LLM, rule-based only)
        scaffolder = MVCScaffolder()
        print(
            f"[INFO] Generating scaffold under: "
            f"{scaffolder.scaffold_root} (models/views/controllers)"
        )

        result = scaffolder.scaffold_all(architecture)

        total_created = (
            len(result.get("models", []))
            + len(result.get("views", []))
            + len(result.get("controllers", []))
        )

        if total_created == 0:
            print("[WARN] No files were generated. Architecture may be empty.")
            return

        print("[SUCCESS] Scaffold created with the following files:")
        for key in ("models", "views", "controllers"):
            files = result.get(key, [])
            if not files:
                continue
            print(f"  - {key.capitalize()}:")
            for p in files:
                try:
                    rel = p.relative_to(scaffolder.project_root)
                except ValueError:
                    rel = p
                print(f"      * {rel}")
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Scaffold command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


def cmd_run_audit(args: argparse.Namespace) -> None:
    """Run quality audit. Only runs Rules & Reviewer Agents (scans generated_src/ for MVC violations)."""
    try:
        # arch_path is optional - audit works without it (direct file scanning)
        arch_path = None
        if hasattr(args, 'arch_path') and args.arch_path:
            arch_path = Path(str(args.arch_path)).resolve()
            if not arch_path.exists():
                print(f"[WARN] Architecture JSON not found: {arch_path}")
                print(f"[INFO] Continuing with direct file scanning (architecture_map.json not required).")
                arch_path = None
        
        # Get project root (CLI is in src/cli/, so parents[2] = project root)
        project_root = Path(__file__).resolve().parents[2]
        
        # Use default path if not provided
        if arch_path is None:
            arch_path = project_root / "data" / "architecture_map.json"
            if not arch_path.exists():
                print(f"[INFO] No architecture_map.json found. Using direct file scanning mode.")
                # Create data directory if it doesn't exist
                arch_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure data directory exists
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            llm_client = LLMClient()
            rag_pipeline = RAGPipeline(llm_client=llm_client) 
            rules_agent = RulesAgent(rag_pipeline, llm_client)
            reviewer_agent = ReviewerAgent(rag_pipeline, llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Agent initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        
        print("PHASE 5: Running Quality Audit (Independent)...")
        print("[INFO] Scanning generated code files for violations...")
        
        generated_root = project_root / "generated_src"
        
        if not generated_root.exists():
            print(f"[ERROR] Generated code directory not found: {generated_root}")
            print(f"[ERROR] Run '@mvc /generate_code' first to generate code.")
            sys.exit(1)
        
        python_files = list(generated_root.rglob("*.py"))
        if not python_files:
            print(f"[ERROR] No Python files found in: {generated_root}")
            print(f"[ERROR] Run '@mvc /generate_code' first to generate code.")
            sys.exit(1)
        
        audit_root = generated_root
        print(f"[INFO] Auditing generated code in: {generated_root}")
        
        # Check if previous report exists
        output_file = data_dir / "final_audit_report.json"
        previous_report_exists = output_file.exists()
        if previous_report_exists:
            print(f"[INFO] Previous audit report found. Will be updated with current code analysis.")
        
        python_files = list(audit_root.rglob("*.py"))
        file_count = len(python_files)
        print(f"[INFO] Analyzing {file_count} Python file(s) in current codebase...")
        
        print(f"[INFO] Step 1: Rules Agent detecting violations...")
        technical_violations = rules_agent.detect_violations(audit_root)
        print(f"[INFO] Found {len(technical_violations)} violation(s). Saved to violations.json")
        
        # Verify violations.json was created
        violations_file = data_dir / "violations.json"
        if violations_file.exists():
            try:
                with open(violations_file, "r", encoding="utf-8") as f:
                    violations_data = json.load(f)
                print(f"[INFO] Verified violations.json exists with {violations_data.get('total_count', 0)} violation(s)")
            except Exception as e:
                print(f"[WARN] Could not verify violations.json: {e}")
        else:
            print(f"[WARN] violations.json was not created at: {violations_file}")
        
        print(f"[INFO] Step 2: Reviewer Agent generating audit report from violations.json...")
        
        try:
            final_report = reviewer_agent.generate_audit_report(technical_violations=None)
        except QuotaExceededError as qe:
            print(f"\n{str(qe)}")
            print(f"\n[INFO] Audit report generation stopped due to quota limit.")
            print(f"[INFO] Violations detected: {len(technical_violations)}")
            print(f"[INFO] Check violations.json for details: {data_dir / 'violations.json'}")
            sys.exit(0)
        except LLMConnectionError as lce:
            print(f"\n[FATAL ERROR] LLM connection failed: {lce}")
            print(f"[INFO] Violations detected: {len(technical_violations)}")
            print(f"[INFO] Check violations.json for details: {data_dir / 'violations.json'}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] ReviewerAgent failed: {e}")
            print(f"[INFO] Violations detected: {len(technical_violations)}")
            print(f"[INFO] Check violations.json for details: {data_dir / 'violations.json'}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        
        # Verify report was generated
        if not final_report:
            print(f"[ERROR] ReviewerAgent returned empty report")
            print(f"[INFO] Violations detected: {len(technical_violations)}")
            print(f"[INFO] Check violations.json for details: {data_dir / 'violations.json'}")
            sys.exit(1)
        
        print(f"[INFO] Report generated. Content keys: {list(final_report.keys())}")
        print(f"[INFO] Report summary: {final_report.get('audit_summary', 'N/A')[:100]}")
        
        # Ensure data directory exists
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report to data directory (overwrites previous report if exists)
        try:
            print(f"[INFO] Saving audit report to: {output_file}")
            print(f"[INFO] Report content size: {len(json.dumps(final_report))} bytes")
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=4, ensure_ascii=False)
                f.flush()  # Force write to buffer
                try:
                    os.fsync(f.fileno())  # Force write to disk (Windows compatible)
                except (OSError, AttributeError):
                    # Some file systems don't support fsync
                    pass
            
            # Wait a moment for file system to sync (Windows)
            import time
            time.sleep(0.5)
            
            # Verify file was written
            if not output_file.exists():
                print(f"[ERROR] File was not created: {output_file}")
                sys.exit(1)
            
            file_size = output_file.stat().st_size
            print(f"[INFO] File written. Size: {file_size} bytes")
            
            if file_size == 0:
                print(f"[ERROR] File was written but is empty: {output_file}")
                sys.exit(1)
            
            # Read back and verify content
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    read_back = json.load(f)
                if not read_back or len(str(read_back)) == 0:
                    print(f"[ERROR] File content is empty after read-back")
                    sys.exit(1)
                print(f"[INFO] File content verified. Keys: {list(read_back.keys())}")
            except json.JSONDecodeError as je:
                print(f"[ERROR] File contains invalid JSON: {je}")
                sys.exit(1)
            except Exception as read_err:
                print(f"[WARN] Could not verify file content: {read_err}")
            
            if previous_report_exists:
                print(f"[SUCCESS] Audit report updated: {output_file}")
                print(f"[INFO] Previous report has been replaced with current code analysis.")
            else:
                print(f"[SUCCESS] Audit report created: {output_file}")
        except Exception as e:
            print(f"[ERROR] Failed to save audit report: {e}")
            print(f"[ERROR] Output file path: {output_file}")
            print(f"[ERROR] Data directory exists: {data_dir.exists()}")
            print(f"[ERROR] Data directory path: {data_dir}")
            print(f"[ERROR] Data directory writable: {os.access(data_dir, os.W_OK) if data_dir.exists() else 'N/A'}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        
        if final_report:
            print("[SUCCESS] Audit completed.")
            print(f"Audit Report saved to: {output_file}")
            print(f"[INFO] Report reflects current state of code. Re-run /audit after code changes to update.")
        else:
            print("[WARN] Audit completed but no report was generated.")
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Audit command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


# ---------------------------------------------------------
def cmd_generate_code(args: argparse.Namespace) -> None:
    """
    Generate complete code for scaffold files using LLM.
    Reads scaffold files, uses prompt templates, and generates real code.
    """
    try:
        category = args.category  # 'model', 'controller', or 'view'
        category_plural = f"{category}s"
        
        # 1) Initialize LLM and RAG
        print("[INFO] Initializing LLM Client...")
        try:
            llm_client = LLMClient()
            rag_pipeline = RAGPipeline(llm_client=llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Client initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        
        # 2) Get project root (CLI is in src/cli/, so parents[2] = project root)
        # Alternative: derive from arch_path (usually data/architecture_map.json)
        arch_path = Path(str(args.arch_path)).resolve()
        if not arch_path.exists():
            print(f"[ERROR] Architecture JSON not found: {arch_path}")
            sys.exit(1)
        
        # Try to get project root from arch_path first (more reliable)
        # arch_path is usually data/architecture_map.json, so parent.parent = project root
        if "data" in arch_path.parts:
            project_root = arch_path.parent.parent  # data/architecture_map.json -> project root
        else:
            # Fallback: calculate from CLI file location
            project_root = Path(__file__).resolve().parents[2]  # src/cli/mvc_arch_cli.py -> project root
        
        print(f"[INFO] Project root: {project_root}")
        
        # 3) Load architecture data
        
        with arch_path.open("r", encoding="utf-8") as f:
            full_data = json.load(f)
        
        if "architecture" in full_data:
            architecture = full_data["architecture"]
        else:
            architecture = full_data
        
        # 4) Load and index SRS for RAG (if not already indexed)
        srs_path = project_root / "data" / "srs_document.txt"
        srs_indexed = False
        if srs_path.exists():
            # Check if SRS is already indexed (collection has chunks)
            try:
                if rag_pipeline.vstore.count() == 0:
                    print("[INFO] Indexing SRS for RAG retrieval...")
                    rag_pipeline.index_srs(srs_path)
                    srs_indexed = True
                else:
                    print("[INFO] SRS already indexed, using existing RAG index.")
                    srs_indexed = True
            except Exception as e:
                print(f"[WARN] Could not index SRS: {e}")
                print(f"[WARN] Will use limited SRS context (first 5000 chars)")
                srs_indexed = False
        
        # 5) Get scaffold files
        scaffold_dir = project_root / "scaffolds" / "mvc_skeleton" / category_plural
        if not scaffold_dir.exists():
            print(f"[ERROR] Scaffold directory not found: {scaffold_dir}")
            print(f"[ERROR] Run 'scaffold' command first.")
            sys.exit(1)
        
        scaffold_files = sorted([f for f in scaffold_dir.glob("*.py")])
        if not scaffold_files:
            print(f"[ERROR] No scaffold files found in {scaffold_dir}")
            print(f"[ERROR] Run 'scaffold' command first.")
            sys.exit(1)
        
        # 6) Load prompt template
        prompt_template_path = project_root / ".github" / "prompts" / f"generate_{category}_code.prompt.md"
        if not prompt_template_path.exists():
            print(f"[ERROR] Prompt template not found: {prompt_template_path}")
            sys.exit(1)
        
        prompt_template = prompt_template_path.read_text(encoding="utf-8")
        
        # 7) Create output directory structure
        generated_src_root = project_root / "generated_src"
        generated_dir = generated_src_root / category_plural
        
        try:
            # First ensure generated_src root exists
            generated_src_root.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Created/verified generated_src root: {generated_src_root}")
            
            # Then create category subdirectory
            generated_dir.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Output directory: {generated_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to create output directory: {generated_dir}")
            print(f"[ERROR] Error: {e}")
            sys.exit(1)
        
        # 8) Process each file
        print(f"[INFO] Processing {len(scaffold_files)} {category} file(s)...")
        
        for idx, scaffold_file in enumerate(scaffold_files, 1):
            fileName = scaffold_file.name
            skeleton_content = scaffold_file.read_text(encoding="utf-8")
            
            # Extract class name from skeleton
            class_match = re.search(r'class\s+(\w+)', skeleton_content)
            className = class_match.group(1) if class_match else fileName.replace('.py', '')
            
            print(f"[{idx}/{len(scaffold_files)}] Generating code for: {fileName} (Class: {className})")
            
            # Find matching architecture item
            arch_items = architecture.get(category, [])
            arch_item = None
            for item in arch_items:
                item_name = item.get("name", "").lower()
                if (item_name == className.lower() or 
                    item_name.replace('view', '').replace('controller', '') == 
                    className.lower().replace('view', '').replace('controller', '')):
                    arch_item = item
                    break
            
            if not arch_item and arch_items:
                arch_item = arch_items[0]  # Fallback to first item
            
            # Get SRS context - use RAG for views/controllers, full text for models
            srs_context = "SRS content not available."
            if srs_path.exists():
                if category == 'view' and srs_indexed:
                    # For views, use RAG to get relevant SRS sections
                    try:
                        view_name = className.replace('View', '').replace('Screen', '').strip()
                        query = f"user interface screen {view_name} display elements layout components"
                        if arch_item and arch_item.get("description"):
                            query += f" {arch_item.get('description')}"
                        
                        print(f"  → Retrieving relevant SRS sections for {className}...")
                        from src.core.config import DEFAULT_TOP_K
                        chunks = rag_pipeline.search(query, k=min(DEFAULT_TOP_K, 5))  # Get top 5 chunks
                        if chunks and chunks.get("documents") and chunks["documents"][0]:
                            srs_context = "\n\n".join(chunks["documents"][0])  # Combine chunks
                            print(f"  → Retrieved {len(chunks['documents'][0])} relevant SRS chunks")
                        else:
                            # Fallback to full SRS (first 5000 chars)
                            srs_context = srs_path.read_text(encoding="utf-8")[:5000]
                            print(f"  → RAG returned no results, using first 5000 chars of SRS")
                    except Exception as e:
                        print(f"  → RAG retrieval failed: {e}, using full SRS (first 5000 chars)")
                        srs_context = srs_path.read_text(encoding="utf-8")[:5000]
                elif category == 'controller' and srs_indexed:
                    # For controllers, use RAG to get relevant business logic sections
                    try:
                        controller_name = className.replace('Controller', '').strip()
                        query = f"business logic {controller_name} actions operations workflow"
                        if arch_item and arch_item.get("actions"):
                            actions_str = " ".join(arch_item.get("actions", [])[:3])
                            query += f" {actions_str}"
                        
                        print(f"  → Retrieving relevant SRS sections for {className}...")
                        from src.core.config import DEFAULT_TOP_K
                        chunks = rag_pipeline.search(query, k=min(DEFAULT_TOP_K, 5))
                        if chunks and chunks.get("documents") and chunks["documents"][0]:
                            srs_context = "\n\n".join(chunks["documents"][0])
                            print(f"  → Retrieved {len(chunks['documents'][0])} relevant SRS chunks")
                        else:
                            srs_context = srs_path.read_text(encoding="utf-8")[:5000]
                            print(f"  → RAG returned no results, using first 5000 chars of SRS")
                    except Exception as e:
                        print(f"  → RAG retrieval failed: {e}, using full SRS (first 5000 chars)")
                        srs_context = srs_path.read_text(encoding="utf-8")[:5000]
                else:
                    # For models or if RAG not available, use first 5000 chars
                    srs_context = srs_path.read_text(encoding="utf-8")[:5000]
            
            # Build prompt
            prompt = prompt_template
            prompt = prompt.replace("{{class_name}}", className)
            prompt = prompt.replace("{{file_name}}", fileName)
            prompt = prompt.replace("{{skeleton}}", skeleton_content)
            prompt = prompt.replace("{{arch_info}}", json.dumps(arch_item or {}, indent=2))
            prompt = prompt.replace("{{srs_context}}", srs_context)
            
            # For controllers, add related models and views
            if category == 'controller':
                related_models = json.dumps(architecture.get("model", [])[:3], indent=2)
                related_views = json.dumps(architecture.get("view", [])[:3], indent=2)
                prompt = prompt.replace("{{related_models}}", related_models)
                prompt = prompt.replace("{{related_views}}", related_views)
            
            # Generate code using LLM
            try:
                print(f"  → Calling LLM to generate code...")
                generated_code = llm_client.generate_content(prompt)
                
                # Clean up the code (remove markdown code blocks if present)
                generated_code = generated_code.strip()
                if generated_code.startswith("```python"):
                    generated_code = generated_code[9:]  # Remove ```python
                if generated_code.startswith("```"):
                    generated_code = generated_code[3:]  # Remove ```
                if generated_code.endswith("```"):
                    generated_code = generated_code[:-3]  # Remove trailing ```
                generated_code = generated_code.strip()
                
                # Write to generated_src
                output_file = generated_dir / fileName
                try:
                    output_file.write_text(generated_code, encoding="utf-8")
                    print(f"  ✓ Code generated: {output_file.relative_to(project_root)}")
                except Exception as e:
                    print(f"  ✗ Failed to write file {output_file}: {e}")
                    raise
                
                # Rate limiting - wait between requests
                if idx < len(scaffold_files):
                    time.sleep(2)  # 2 second delay between files
                    
            except QuotaExceededError as qe:
                print(f"\n{str(qe)}")
                print(f"\n[INFO] Code generation stopped. {idx-1} file(s) generated successfully.")
                sys.exit(0)
            except LLMConnectionError as lce:
                print(f"\n[FATAL ERROR] LLM connection failed: {lce}")
                print(f"[INFO] {idx-1} file(s) generated successfully before error.")
                sys.exit(1)
            except Exception as e:
                print(f"  ✗ Error generating code for {fileName}: {e}")
                # Continue with next file
                continue
        
        # Verify generated files
        generated_files = sorted([f for f in generated_dir.glob("*.py")])
        print(f"\n[SUCCESS] Code generation complete!")
        print(f"[SUCCESS] Generated {len(generated_files)} file(s) in: {generated_dir}")
        if generated_files:
            print(f"[INFO] Generated files:")
            for gen_file in generated_files:
                print(f"  - {gen_file.name}")
        else:
            print(f"[WARN] No files were generated. Check errors above.")
        
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Generate-code command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


def cmd_run_fix(args: argparse.Namespace) -> None:
    """
    Automatically applies recommendations from audit report.
    Only fixes the specific issues mentioned in recommendations.
    """
    try:
        # 1) Initialize LLM and RAG
        try:
            llm_client = LLMClient()
            rag_pipeline = RAGPipeline(llm_client=llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Client initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        # 2) Initialize RecommendationFixerAgent
        try:
            fixer_agent = RecommendationFixerAgent(
                rag_pipeline=rag_pipeline,
                llm_client=llm_client
            )
        except Exception as e:
            print(f"[FATAL ERROR] Fixer agent initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        # 3) Get audit report path (optional argument)
        audit_report_path = None
        if hasattr(args, 'audit_report') and args.audit_report:
            audit_report_path = Path(str(args.audit_report)).resolve()
            if not audit_report_path.exists():
                print(f"[ERROR] Audit report not found: {audit_report_path}")
                sys.exit(1)

        # 4) Apply recommendations
        print("[INFO] Applying recommendations from audit report...")
        result = fixer_agent.apply_recommendations(audit_report_path=audit_report_path)
        
        if result["success"]:
            print("\n[SUCCESS] All recommendations applied successfully!")
            print(f"Fixed {len(result.get('fixed_files', []))} file(s)")
        else:
            print(f"\n[PARTIAL SUCCESS] Fixed {len(result.get('fixed_files', []))} file(s), "
                  f"failed {len(result.get('failed_files', []))} file(s)")
            
            if result.get("failed_files"):
                print("\nFailed files:")
                for failed in result["failed_files"]:
                    print(f"  - {Path(failed['file']).name}: {failed.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Fix command failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


# ---------------------------------------------------------
# Main CLI parser
# ---------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mvc_arch_cli",
        description="CLI for MVC Test Orchestrator (SRS → Architecture → Scaffold)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-srs komutu
    p_create = subparsers.add_parser(
        "create-srs",
        help="Creates SRS from user idea (no architecture extraction).",
    )
    p_create.add_argument(
        "--user-idea", 
        required=True,
        help="The user's high-level idea for the software.",
    )
    p_create.add_argument(
        "--output",
        required=True,
        help="Path to write combined architecture JSON.",
    )
    p_create.set_defaults(func=cmd_create_srs)
    
    p_extract = subparsers.add_parser(
        "extract",
        help="Extract MVC architecture from SRS. Only runs Architect Agent (creates architecture_map.json).",
    )
    p_extract.add_argument(
        "--srs-path", 
        required=True,
        help="Path to the existing SRS (.txt/.pdf) file.",
    )
    p_extract.add_argument(
        "--output",
        required=True,
        help="Path to write architecture JSON (default: data/architecture_map.json).",
    )
    p_extract.set_defaults(func=cmd_extract)
    
    p_index = subparsers.add_parser(
        "index-srs",
        help="[LEGACY] Alias for 'extract' command.",
    )
    p_index.add_argument(
        "--srs-path", 
        required=True,
        help="Path to the existing SRS (.txt/.pdf) file.",
    )
    p_index.add_argument(
        "--output",
        required=True,
        help="Path to write combined architecture JSON.",
    )
    p_index.set_defaults(func=cmd_index_srs)


    p_scaffold = subparsers.add_parser(
        "scaffold",
        help="Generate MVC scaffold files. Only runs Scaffolder Agent (no LLM, rule-based). Creates empty .py files in scaffolds/.",
    )
    p_scaffold.add_argument(
        "--arch-path",
        required=True,
        help="Path to architecture JSON file (from 'extract' command).",
    )
    p_scaffold.set_defaults(func=cmd_scaffold)
    
    
    p_audit = subparsers.add_parser(
        "audit",
        help="Run quality audit. Only runs Rules & Reviewer Agents (scans generated_src/ for MVC violations).",
    )
    p_audit.add_argument(
        "--arch-path",
        required=False,
        help="[OPTIONAL] Path to architecture JSON file. Audit works without it (direct file scanning).",
        default="data/architecture_map.json",
    )
    p_audit.set_defaults(func=cmd_run_audit)
    
    p_run_audit = subparsers.add_parser(
        "run-audit",
        help="[LEGACY] Alias for 'audit' command.",
    )
    p_run_audit.add_argument(
        "--arch-path",
        required=True,
        help="Path to architecture JSON file.",
    )
    p_run_audit.set_defaults(func=cmd_run_audit)

    p_generate_code = subparsers.add_parser(
        "generate-code",
        help="Generate complete code for scaffold files using LLM. Uses prompt templates to fill scaffold classes with real code.",
    )
    p_generate_code.add_argument(
        "--category",
        required=True,
        choices=["model", "controller", "view"],
        help="Category to generate code for (model, controller, or view)",
    )
    p_generate_code.add_argument(
        "--arch-path",
        required=True,
        help="Path to architecture JSON file (from 'extract' command).",
    )
    p_generate_code.set_defaults(func=cmd_generate_code)
    
    p_fix = subparsers.add_parser(
        "run-fix",
        help="Automatically apply recommendations from audit report. Only fixes specific issues mentioned in recommendations.",
    )
    p_fix.add_argument(
        "--audit-report",
        type=str,
        help="Path to audit report JSON (default: data/final_audit_report.json)",
    )
    p_fix.set_defaults(func=cmd_run_fix)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Command execution failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()