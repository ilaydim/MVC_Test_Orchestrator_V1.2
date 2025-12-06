# src/cli/mvc_arch_cli.py

import argparse
import json
from pathlib import Path

from src.rag.rag_pipeline import RAGPipeline
from src.agents.architect_agent.mvc_architect_orchestrator import MVCArchitectOrchestrator
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder


# ---------------------------------------------------------
# extract command
# ---------------------------------------------------------
def cmd_extract(args: argparse.Namespace) -> None:
    """
    CLI entry point for:
        python -m src.cli.mvc_arch_cli extract --srs-path ... --output ...
    """
    srs_path = Path(args.srs_path).resolve()
    output_path = Path(args.output).resolve()

    if not srs_path.exists():
        print(f"[ERROR] SRS file not found: {srs_path}")
        return

    print(f"[INFO] Using SRS PDF: {srs_path}")

    # 1) Build RAG + Orchestrator
    rag = RAGPipeline()
    orch = MVCArchitectOrchestrator(rag_pipeline=rag)

    # 2) Index SRS into RAG
    print("[INFO] Indexing SRS into RAG pipeline...")
    with srs_path.open("rb") as f:
        index_info = rag.index_pdf(f)

    doc_name = index_info.get("document_name")
    page_count = index_info.get("page_count")
    chunk_count = index_info.get("total_chunks_in_db")

    print(
        f"[INFO] Indexed document '{doc_name}' "
        f"with {page_count} pages and {chunk_count} chunks."
    )

    # 3) Extract full architecture (Model / View / Controller)
    print("[INFO] Extracting full MVC architecture (Model / View / Controller)...")
    architecture = orch.extract_full_architecture(k=6)

    # 4) Write JSON to output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(architecture, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Architecture JSON written to: {output_path}")


# ---------------------------------------------------------
# scaffold command
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
        print(f"  - {key.capitalize()}:")
        for p in files:
            # Show path relative to project root for readability
            try:
                rel = p.relative_to(scaffolder.project_root)
            except ValueError:
                rel = p
            print(f"      * {rel}")


# ---------------------------------------------------------
# Main CLI parser
# ---------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mvc_arch_cli",
        description="CLI for MVC Test Orchestrator (SRS → Architecture → Scaffold)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = subparsers.add_parser(
        "extract",
        help="Index an SRS PDF and extract full MVC architecture as JSON.",
    )
    p_extract.add_argument(
        "--srs-path",
        required=True,
        help="Path to the SRS PDF file.",
    )
    p_extract.add_argument(
        "--output",
        required=True,
        help="Path to write combined architecture JSON (model/view/controller).",
    )
    p_extract.set_defaults(func=cmd_extract)

    # scaffold
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
