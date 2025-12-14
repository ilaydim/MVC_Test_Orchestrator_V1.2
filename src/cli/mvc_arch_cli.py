import argparse
import json
import sys
from pathlib import Path

from src.rag.rag_pipeline import RAGPipeline 
from src.core.llm_client import LLMClient 
from src.agents.mvc_pipeline_orchestrator import MVCPipelineOrchestrator
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder


# --- Yardımcı Fonksiyon (Kod tekrarını azaltmak için) ---
def _run_extraction_pipeline(user_idea: str = None, srs_path: Path = None, output_path: Path = None, skip_scaffold: bool = False):
    """Ortak Pipeline çalıştırma mantığı."""
    
    # 1) Bağımlılıkları Başlat
    print("[INFO] Initializing RAG and LLM Clients...")
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
    except Exception as e:
        print(f"[FATAL ERROR] Client initialization failed: {e}")
        sys.exit(1)

    # 2) Orchestrator'ı Başlat ve bağımlılıkları aktar
    print("[INFO] Initializing MVC Pipeline Orchestrator...")
    try:
        orch = MVCPipelineOrchestrator(
            rag_pipeline=rag_pipeline,
            llm_client=llm_client
        )
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)

    # 3) Pipeline'ı çalıştır
    if user_idea:
        print(f"[INFO] Running pipeline from user idea: '{user_idea[:40]}...'")
        final_result = orch.run_full_pipeline(user_idea=user_idea, skip_scaffold=skip_scaffold)
    elif srs_path:
        print(f"[INFO] Running pipeline from existing SRS: {srs_path.name}")
        final_result = orch.run_full_pipeline(srs_path=srs_path, skip_scaffold=skip_scaffold)
    else:
        print("[FATAL ERROR] No user idea or SRS path provided for extraction/creation.")
        sys.exit(1)
        

    # 4) Çıktı Kontrolü ve Yazma (Sadece mimari çıkış yapıldıysa JSON yazar)
    if final_result.get("status") == "COMPLETED":
        architecture = final_result.get('architecture') 
        
        if architecture and output_path:
             output_path.parent.mkdir(parents=True, exist_ok=True)
             with output_path.open("w", encoding="utf-8") as f:
                json.dump(architecture, f, indent=2, ensure_ascii=False)
             print(f"[SUCCESS] Full pipeline completed. Architecture JSON written to: {output_path}")
        else:
             print("[SUCCESS] Pipeline completed (Audit/Code phase). No new architecture JSON written.")
    else:
        print(f"[FAILED] Pipeline terminated early. Reason: {final_result.get('reason')}")
        sys.exit(1)


# ---------------------------------------------------------
# create-srs command
# ---------------------------------------------------------
def cmd_create_srs(args: argparse.Namespace) -> None:
    output_path = Path(args.output).resolve()
    user_idea = args.user_idea 
    
    # Varsayılan olarak scaffold'u atlamadan çalıştırır. (Eğer sadece extract isteniyorsa skip_scaffold=True olmalı)
    _run_extraction_pipeline(user_idea=user_idea, output_path=output_path, skip_scaffold=args.skip_scaffold)


# ---------------------------------------------------------
# index-srs command 
# ---------------------------------------------------------
def cmd_index_srs(args: argparse.Namespace) -> None:
    output_path = Path(args.output).resolve()
    srs_path = Path(args.srs_path).resolve()
    
    if not srs_path.exists():
        print(f"[ERROR] SRS file not found: {srs_path}")
        return

    _run_extraction_pipeline(srs_path=srs_path, output_path=output_path, skip_scaffold=args.skip_scaffold)


# ---------------------------------------------------------
# scaffold command (AYNI KALDI)
# ---------------------------------------------------------
def cmd_scaffold(args: argparse.Namespace) -> None:
    arch_path = Path(args.arch_path).resolve()

    if not arch_path.exists():
        print(f"[ERROR] Architecture JSON not found: {arch_path}")
        return

    with arch_path.open("r", encoding="utf-8") as f:
        architecture = json.load(f)

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
        print(f"  - {key.capitalize()}:")
        for p in files:
            try:
                rel = p.relative_to(scaffolder.project_root)
            except ValueError:
                rel = p
            print(f"      * {rel}")


# ---------------------------------------------------------
# run-audit command (YENİ)
# ---------------------------------------------------------
def cmd_run_audit(args: argparse.Namespace) -> None:
    """
    Mimari (JSON) ve Scaffold (dosyalar) üzerinden Audit aşamasını çalıştırır (PHASE 4).
    """
    # 1) Orchestrator'ı başlat (RAG/LLM bağımlılıklarıyla)
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
        orch = MVCPipelineOrchestrator(rag_pipeline=rag_pipeline, llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)
    
    # Audit'in çalışması için mimari JSON'un RulesAgent tarafından yüklenebilir olması gerekir.
    print("[INFO] Running PHASE 4: Quality Audit...")
    try:
        scaffold_root = orch.scaffolder.scaffold_root 
        
        # Rules Agent: Teknik ihlalleri tespit eder.
        technical_violations = orch.rules_agent.detect_violations(scaffold_root)
        
        # Reviewer Agent: İhlalleri doğal dil önerilerine çevirir.
        final_audit_report = orch.reviewer_agent.generate_audit_report(technical_violations)
        
        print("[SUCCESS] Audit completed.")
        print(f"Audit Report: \n{final_audit_report}")
        
    except Exception as e:
        print(f"[FATAL ERROR] Audit execution failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------
# run-code command (YENİ)
# ---------------------------------------------------------
def cmd_run_code(args: argparse.Namespace) -> None:
    """
    Audit sonrası Kodlama aşamasını (PHASE 5) çalıştırır.
    """
    # 1) Orchestrator'ı başlat
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
        orch = MVCPipelineOrchestrator(rag_pipeline=rag_pipeline, llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)

    print("[INFO] Running PHASE 5: Code Generation...")
    try:
        orch.coder_agent.generate_code()
        print("[SUCCESS] Code generation completed.")
    except Exception as e:
        print(f"[FATAL ERROR] Code generation failed: {e}")
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
        help="Creates SRS from user idea, indexes it, and extracts MVC architecture.",
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
    p_create.add_argument(
        "--skip-scaffold",
        action="store_true", # Flag olarak çalışır
        help="If set, skips PHASE 3 (Scaffolding) and PHASE 4-5 are implicitly skipped.",
    )
    p_create.set_defaults(func=cmd_create_srs)
    
    # index-srs komutu
    p_index = subparsers.add_parser(
        "index-srs",
        help="Loads an existing SRS file, indexes it, and extracts MVC architecture.",
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
    p_index.add_argument(
        "--skip-scaffold",
        action="store_true",
        help="If set, skips PHASE 3 (Scaffolding) and PHASE 4-5 are implicitly skipped.",
    )
    p_index.set_defaults(func=cmd_index_srs)


    # scaffold komutu
    p_scaffold = subparsers.add_parser(
        "scaffold",
        help="Generate MVC scaffolds from an architecture JSON file.",
    )
    p_scaffold.add_argument(
        "--arch-path",
        required=True,
        help="Path to combined architecture JSON file.",
    )
    p_scaffold.set_defaults(func=cmd_scaffold)
    
    
    # run-audit komutu
    p_audit = subparsers.add_parser(
        "run-audit",
        help="Runs PHASE 4: Quality Audit on existing scaffold and architecture JSON.",
    )
    # Audit Agent'ın mimariyi yüklemesi için path gerekli
    p_audit.add_argument(
        "--arch-path",
        required=True,
        help="Path to combined architecture JSON file (needed by RulesAgent).",
    )
    p_audit.set_defaults(func=cmd_run_audit)

    # run-code komutu
    p_code = subparsers.add_parser(
        "run-code",
        help="Runs PHASE 5: Code Generation on existing scaffold.",
    )
    p_code.set_defaults(func=cmd_run_code)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()