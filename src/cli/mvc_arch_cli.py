# Disable telemetry to prevent crashes
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import argparse
import json
import sys
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
from src.agents.model_coder_agent import ModelCoderAgent
from src.agents.view_coder_agent import ViewCoderAgent
from src.agents.controller_coder_agent import ControllerCoderAgent
from src.agents.rules_agent import RulesAgent
from src.agents.reviewer_agent import ReviewerAgent


def _run_extraction_pipeline(
    user_idea: str = None,
    srs_path: Path = None,
    output_path: Path = None,
):
    """Common architecture extraction logic. MODULAR: Only Architect Agent, writes to disk only."""

    # 1) Bağımlılıkları Başlat
    print("[INFO] Initializing RAG and LLM Clients...")
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Client initialization failed: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    # 2) Initialize SRS Writer and Architect Agents (MODULAR: Only what's needed for extract)
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

    # 3) SRS kaynağını belirle (user_idea veya mevcut SRS dosyası)
    current_srs_path: Path | None = None

    if user_idea:
        print(f"[INFO] Generating SRS from user idea: '{user_idea[:40]}...'")
        try:
            current_srs_path = srs_writer.generate_srs(user_idea)
        except QuotaExceededError as qe:
            # Kota doldu - gracefully exit
            print(f"\n{str(qe)}")
            print("\n[CLI] Pipeline stopped. No files were modified.")
            sys.exit(0)  # Normal exit (kota dolması fatal hata değil)
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

    # 4) Extract architecture (MODULAR: Direct agent calls, no wrapper)
    print(f"PHASE 0.5: Indexing SRS file: {current_srs_path.name}")
    rag_pipeline.index_srs(current_srs_path)
    
    print("PHASE 1-2: Extracting MVC Architecture (Extraction Only)...")
    from src.core.config import DEFAULT_TOP_K
    
    # Run all architect agents directly (no orchestrator wrapper)
    requirements_analysis = requirements_agent.extract_analysis(k=DEFAULT_TOP_K)
    model_json = model_agent.extract_models(k=DEFAULT_TOP_K)
    controller_json = controller_agent.extract_controllers(k=DEFAULT_TOP_K)
    view_json = view_agent.extract_views(k=DEFAULT_TOP_K)
    
    architecture_map = {
        "model": model_json.get("model", []),
        "view": view_json.get("view", []),
        "controller": controller_json.get("controller", []),
    }
    
    # Save output (using model_agent's save_output method)
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


# ---------------------------------------------------------
# create-srs command
# ---------------------------------------------------------
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

        # 2) Initialize SRS Writer Agent
        print("[INFO] Initializing SRS Writer Agent...")
        try:
            srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Agent initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        # 3) Sadece SRS üret
        try:
            srs_path = srs_writer.generate_srs(user_idea)
        except QuotaExceededError as qe:
            # Kota doldu - gracefully exit
            print(f"\n{str(qe)}")
            print("\n[CLI] SRS creation stopped. No files were created.")
            sys.exit(0)  # Normal exit (kota dolması fatal hata değil)
        except LLMConnectionError as lce:
            print(f"\n[FATAL ERROR] LLM connection failed: {lce}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        except Exception as e:
            print(f"[FATAL ERROR] SRS generation failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        # 4) Üretilen SRS'i kullanıcı tarafından belirtilen yola taşı
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            final_srs_path = srs_path.replace(output_path)
        except Exception:
            # replace başarısız olursa kopyala
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


# ---------------------------------------------------------
# extract command (MODULAR: Only Architect Agent)
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# scaffold command (MODULAR: Only Scaffolder Agent)
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# run-audit command
# ---------------------------------------------------------
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
        
        # Use default path if not provided
        if arch_path is None:
            project_root = Path(__file__).resolve().parents[1]
            arch_path = project_root / "data" / "architecture_map.json"
            if not arch_path.exists():
                print(f"[INFO] No architecture_map.json found. Using direct file scanning mode.")
                # Create dummy path for orchestrator (it will use direct scanning)
                arch_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1) Initialize Rules & Reviewer Agents (MODULAR: Only what's needed for audit)
        try:
            llm_client = LLMClient()
            rag_pipeline = RAGPipeline(llm_client=llm_client) 
            rules_agent = RulesAgent(rag_pipeline, llm_client)
            reviewer_agent = ReviewerAgent(rag_pipeline, llm_client)
        except Exception as e:
            print(f"[FATAL ERROR] Agent initialization failed: {e}")
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        
        # 2) Run audit (MODULAR: Direct file scanning)
        print("PHASE 5: Running Quality Audit (Independent)...")
        
        project_root = Path(__file__).resolve().parents[1]
        generated_root = project_root / "generated_src"
        scaffold_root = project_root / "scaffolds" / "mvc_skeleton"
        
        audit_root = None
        if generated_root.exists() and any(generated_root.rglob("*.py")):
            audit_root = generated_root
            print(f"[INFO] Auditing generated code in: {generated_root}")
        elif scaffold_root.exists() and any(scaffold_root.iterdir()):
            audit_root = scaffold_root
            print(f"[INFO] Auditing scaffold code in: {scaffold_root}")
        else:
            print("[ERROR] No code found to audit. Run scaffold and/or code generation first.")
            return
        
        # Direct file scanning - no architecture map needed
        technical_violations = rules_agent.detect_violations(audit_root)
        final_report = reviewer_agent.generate_audit_report(technical_violations)
        
        output_file = arch_path.parent / "final_audit_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=4)
            
        print(f"[SUCCESS] Audit report created: {output_file}")
        
        if final_report:
            print("[SUCCESS] Audit completed.")
            print(f"Audit Report saved to: {arch_path.parent / 'final_audit_report.json'}")
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
# generate command (MODULAR: Only Coder Agents)
# ---------------------------------------------------------
def cmd_generate(args: argparse.Namespace) -> None:
    """Generate code implementation. Only runs Coder Agents (reads from scaffolds/, writes to generated_src/)."""
    # 1) Initialize Coder Agents (MODULAR: Only what's needed for code generation)
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
        model_coder = ModelCoderAgent(rag_pipeline, llm_client)
        view_coder = ViewCoderAgent(rag_pipeline, llm_client)
        controller_coder = ControllerCoderAgent(rag_pipeline, llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Agent initialization failed: {e}")
        sys.exit(1)

    # Parse arguments - category is required
    category = getattr(args, 'category', None)
    
    if not category:
        print(f"[ERROR] Category is required. Use: --category model|controller|view")
        sys.exit(1)
    
    if category not in ['model', 'controller', 'view']:
        print(f"[ERROR] Invalid category: {category}. Use: model, controller, or view")
        sys.exit(1)
    
    # Validate scaffold exists
    project_root = Path(__file__).resolve().parents[1]
    scaffold_root = project_root / "scaffolds" / "mvc_skeleton"
    category_dir = scaffold_root / f"{category}s"
    
    if not category_dir.exists() or not any(category_dir.glob("*.py")):
        print(f"[ERROR] No scaffold files found in: {category_dir}")
        print(f"[ERROR] Please run 'scaffold' command first to create skeleton files.")
        sys.exit(1)
    
    # Use specialized coder agents - each processes ALL files in its category
    # Coder agents read from scaffolds/ and write to generated_src/
    try:
        if category == 'model':
            result = model_coder.generate_code()
        elif category == 'controller':
            result = controller_coder.generate_code()
        elif category == 'view':
            result = view_coder.generate_code()
        
        # Final summary
        completed = len(result.get('completed', []))
        failed = len(result.get('failed', []))
        hallucinated = len(result.get('hallucinated', []))
        
        print(f"\n{'='*60}")
        print("[CODE GENERATION COMPLETE]")
        print(f"{'='*60}")
        print(f"✅ Completed: {completed} files")
        if failed > 0:
            print(f"❌ Failed: {failed} files")
        if hallucinated > 0:
            print(f"🚫 Hallucinated: {hallucinated} files")
        print(f"{'='*60}\n")
            
    except KeyboardInterrupt:
        print(f"\n[CLI] ⚠️ Interrupted by user", flush=True)
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        # Catch ALL errors and print full details
        print(f"\n{'='*60}", flush=True)
        print(f"[FATAL ERROR] Code generation failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        traceback.print_exc(file=sys.stdout)
        print(f"{'='*60}\n", flush=True)
        sys.exit(1)


# ---------------------------------------------------------
# run-fix command
# ---------------------------------------------------------
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
    
    # extract komutu (MODULAR: Only Architect Agent)
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
    
    # index-srs komutu (Legacy alias for extract)
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


    # scaffold komutu (MODULAR: Only Scaffolder Agent)
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
    
    
    # audit komutu (MODULAR: Only Rules & Reviewer Agents)
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
    
    # run-audit komutu (Legacy alias for audit)
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

    # generate komutu (MODULAR: Only Coder Agents)
    p_generate = subparsers.add_parser(
        "generate",
        help="Generate code implementation. Only runs Coder Agents (reads from scaffolds/, writes to generated_src/).",
    )
    p_generate.add_argument(
        "--category",
        choices=["model", "controller", "view"],
        required=True,
        help="Category to process (model/controller/view). ALL files in this category will be generated.",
    )
    p_generate.set_defaults(func=cmd_generate)
    
    # run-code komutu (Legacy alias for generate)
    p_code = subparsers.add_parser(
        "run-code",
        help="[LEGACY] Alias for 'generate' command.",
    )
    p_code.add_argument(
        "--category",
        choices=["model", "controller", "view"],
        required=True,
        help="Category to process (model/controller/view). ALL files in this category will be generated.",
    )
    p_code.set_defaults(func=cmd_generate)

    # run-fix komutu
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