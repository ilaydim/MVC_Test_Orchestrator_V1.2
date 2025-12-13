# src/cli/mvc_arch_cli.py

import argparse
import json
import sys
from pathlib import Path

# Yeni importlar: Pipeline'ın bağımlılıklarını ekle
from src.rag.rag_pipeline import RAGPipeline 
from src.core.llm_client import LLMClient 
from src.agents.mvc_pipeline_orchestrator import MVCPipelineOrchestrator
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder


# ---------------------------------------------------------
# extract command (SRS Yazarını da içeren tam pipeline)
# ---------------------------------------------------------
def cmd_extract(args: argparse.Namespace) -> None:
    """
    Runs the full MVC Extraction pipeline (User Idea -> SRS -> Index -> Arch).
    """
    
    # Argümanları al
    output_path = Path(args.output).resolve()
    user_idea = args.user_idea 

    # 1) BAĞIMLILIKLARI BAŞLAT (KRİTİK DÜZELTME BURADA)
    print("[INFO] Initializing RAG and LLM Clients...")
    try:
        # LLM ve RAGPipeline nesnelerini oluştur
        llm_client = LLMClient()
        # RAGPipeline, LLMClient'ı parametre olarak alır
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
    except Exception as e:
        print(f"[FATAL ERROR] Client initialization failed: {e}")
        sys.exit(1)

    # 2) Orchestrator'ı başlat ve bağımlılıkları aktar (Dependency Injection)
    print("[INFO] Initializing MVC Pipeline Orchestrator...")
    try:
        # RAG ve LLM'i Orchestrator'ın __init__'ine aktar
        orch = MVCPipelineOrchestrator(
            rag_pipeline=rag_pipeline,
            llm_client=llm_client
        )
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)

    # 3) Tam pipeline'ı çalıştır
    print(f"[INFO] Running full pipeline for user idea: '{user_idea[:40]}...'")
    try:
        final_result = orch.run_full_pipeline(user_idea=user_idea)
    except Exception as e:
        print(f"[FATAL ERROR] Pipeline execution failed: {e}")
        sys.exit(1)
        
    
    # 4) Çıktı Kontrolü ve Yazma
    if final_result.get("status") == "COMPLETED":
        # ... (Geri kalan başarı kodu aynı kalır)
        architecture = final_result.get('architecture') 
        
        if not architecture:
             print("[WARN] Pipeline completed but returned no architecture map.")
             sys.exit(1)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            # Buradaki 'architecture' anahtarı sizin MVCPipelineOrchestrator'ınızdan gelmelidir
            # Eğer arch map'i final_result'ın kök seviyesinde dönmüyorsa, düzeltmeniz gerekebilir.
            # Şimdilik final_result.get('architecture') olduğunu varsayıyoruz.
            json.dump(architecture, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] Full pipeline completed. Architecture JSON written to: {output_path}")
    else:
        # Eğer pipeline erken durursa (örn: RAG Indexleme Hatası)
        print(f"[FAILED] Pipeline terminated early. Reason: {final_result.get('reason')}")
        sys.exit(1)


# ---------------------------------------------------------
# scaffold command (AYNI KALDI)
# ---------------------------------------------------------
def cmd_scaffold(args: argparse.Namespace) -> None:
    """
    CLI entry point for:
        python -m src.cli.mvc_arch_cli scaffold --arch-path ...
    """
    arch_path = Path(args.arch_path).resolve()

    if not arch_path.exists():
        print(f"[ERROR] Architecture JSON not found: {arch_path}")
        return

    # 1) Load architecture JSON
    with arch_path.open("r", encoding="utf-8") as f:
        architecture = json.load(f)

    # 2) Run scaffolder
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
            # Show path relative to project root for readability
            try:
                rel = p.relative_to(scaffolder.project_root)
            except ValueError:
                rel = p
            print(f"      * {rel}")


# ---------------------------------------------------------
# Main CLI parser (Argüman Düzeltmesi)
# ---------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mvc_arch_cli",
        description="CLI for MVC Test Orchestrator (SRS → Architecture → Scaffold)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract komutu güncellendi
    p_extract = subparsers.add_parser(
        "extract",
        help="Runs the full pipeline from user idea to architecture JSON.",
    )
    p_extract.add_argument(
        "--user-idea", # <-- YENİ ARGÜMAN
        required=True,
        help="The user's high-level idea for the software.",
    )
    p_extract.add_argument(
        "--output",
        required=True,
        help="Path to write combined architecture JSON (model/view/controller).",
    )
    p_extract.set_defaults(func=cmd_extract)

    # scaffold komutu aynı kaldı
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()