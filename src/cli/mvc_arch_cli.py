import argparse
import json
import sys
from pathlib import Path

from src.rag.rag_pipeline import RAGPipeline 
from src.core.llm_client import LLMClient 
from src.agents.mvc_pipeline_orchestrator import MVCPipelineOrchestrator
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder


    # --- Yardımcı Fonksiyon (Kod tekrarını azaltmak için) ---
def _run_extraction_pipeline(
    user_idea: str = None,
    srs_path: Path = None,
    output_path: Path = None,
    skip_scaffold: bool = False,  # Artık kullanılmıyor ama CLI imzası için tutuluyor
):
    """
    Ortak mimari çıkarma mantığı.

    Yeni akış:
      - Eğer user_idea verilmişse önce SRS üretilir.
      - Ardından verilen/üretilen SRS üzerinden sadece mimari çıkarılır
        ve JSON olarak output_path'e yazılır (scaffold / code / audit yok).
    """

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
            llm_client=llm_client,
        )
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)

    # 3) SRS kaynağını belirle (user_idea veya mevcut SRS dosyası)
    current_srs_path: Path | None = None

    if user_idea:
        print(f"[INFO] Generating SRS from user idea: '{user_idea[:40]}...'")
        try:
            current_srs_path = orch.srs_writer_agent.generate_srs(user_idea)
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

    # 4) Yalnızca mimari çıkarma (senin yeni Orchestrator metoduna göre)
    orch.run_extraction_only(current_srs_path, str(output_path))


# ---------------------------------------------------------
# create-srs command
# ---------------------------------------------------------
def cmd_create_srs(args: argparse.Namespace) -> None:
    """
    YENİ DAVRANIŞ:
      - Sadece user_idea'dan SRS üretir.
      - Scaffold / mimari çıkarma BU ADIMDA yapılmaz.
      - Üretilen SRS dosyası, --output ile verilen yola taşınır.
      - Sonrasında MİMARİ çıkarmak için ayrı olarak index-srs komutu kullanılmalıdır.
    """
    output_path = Path(args.output).resolve()
    user_idea = args.user_idea

    # 1) Bağımlılıkları Başlat (LLM için gerekli)
    print("[INFO] Initializing RAG and LLM Clients for SRS creation...")
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Client initialization failed: {e}")
        sys.exit(1)

    # 2) Orchestrator'ı Başlat
    print("[INFO] Initializing MVC Pipeline Orchestrator (SRS only)...")
    try:
        orch = MVCPipelineOrchestrator(
            rag_pipeline=rag_pipeline,
            llm_client=llm_client,
        )
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)

    # 3) Sadece SRS üret
    try:
        srs_path = orch.srs_writer_agent.generate_srs(user_idea)
    except Exception as e:
        print(f"[FATAL ERROR] SRS generation failed: {e}")
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
        full_data = json.load(f)

    # JSON yapısını kontrol et: "architecture" key'i var mı?
    # Eğer varsa (run_extraction_only çıktısı), onu kullan
    # Yoksa direkt root'u kullan (eski format veya direkt architecture map)
    if "architecture" in full_data:
        architecture = full_data["architecture"]
        print(f"[INFO] Using 'architecture' key from JSON structure.")
    else:
        architecture = full_data
        print(f"[INFO] Using root-level architecture structure.")

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
    Mimari (JSON) ve Scaffold (dosyalar) üzerinden Audit aşamasını çalıştırır.
    Orchestrator'ın run_audit_only metodunu kullanır.
    """
    arch_path = Path(args.arch_path).resolve()
    
    if not arch_path.exists():
        print(f"[ERROR] Architecture JSON not found: {arch_path}")
        sys.exit(1)
    
    # 1) Orchestrator'ı başlat (RAG/LLM bağımlılıklarıyla)
    try:
        llm_client = LLMClient()
        rag_pipeline = RAGPipeline(llm_client=llm_client) 
        orch = MVCPipelineOrchestrator(rag_pipeline=rag_pipeline, llm_client=llm_client)
    except Exception as e:
        print(f"[FATAL ERROR] Orchestrator initialization failed: {e}")
        sys.exit(1)
    
    # 2) Orchestrator'ın run_audit_only metodunu kullan
    print("[INFO] Running Quality Audit...")
    try:
        final_report = orch.run_audit_only(arch_path)
        
        if final_report:
            print("[SUCCESS] Audit completed.")
            print(f"Audit Report saved to: {arch_path.parent / 'final_audit_report.json'}")
        else:
            print("[WARN] Audit completed but no report was generated.")
        
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
    p_create.add_argument(
        "--skip-scaffold",
        action="store_true", # Flag olarak çalışır
        help="If set, skips PHASE 3 (Scaffolding) and PHASE 4-5 are implicitly skipped.",
    )
    p_create.set_defaults(func=cmd_create_srs)
    
    # index-srs komutu
    p_index = subparsers.add_parser(
        "index-srs",
        help="Loads an existing SRS file and extracts MVC architecture.",
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