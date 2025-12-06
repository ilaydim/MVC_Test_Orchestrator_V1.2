import os
import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# Import orchestrator + RAG
from src.rag.rag_pipeline import RAGPipeline
from src.agents.architect_agent.mvc_architect_orchestrator import MVCArchitectOrchestrator

# Import scaffolder
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder


# ---------------------------------------------------------
# Streamlit Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="MVC Test Orchestrator",
    layout="wide",
)

st.title("MVC Test Orchestrator")
st.write("Upload your SRS PDF and generate the full MVC architecture.")


# ---------------------------------------------------------
# Initialize shared state
# ---------------------------------------------------------
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = RAGPipeline()

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MVCArchitectOrchestrator(
        rag_pipeline=st.session_state.rag_pipeline
    )

if "index_info" not in st.session_state:
    st.session_state.index_info = None

if "architecture_map" not in st.session_state:
    st.session_state.architecture_map = None

if "scaffolder" not in st.session_state:
    st.session_state.scaffolder = MVCScaffolder()


# ---------------------------------------------------------
# Clean List Renderer (no .py, no tree, minimal)
# ---------------------------------------------------------
def render_layer_items(items, title: str) -> None:
    """
    Renders a simple numbered list for a given architecture layer.
    """
    if not items:
        st.info(f"No {title} found.")
        return

    st.markdown(f"### {title}")

    for idx, comp in enumerate(items, start=1):
        name = comp.get("name", "Unknown").replace(" ", "")

        # Fix duplicate 'ControllerController' names
        if name.endswith("ControllerController"):
            name = name.replace("ControllerController", "Controller")

        # Ensure exactly one 'Controller' suffix in controller layer
        if "controller" in title.lower():
            if not name.endswith("Controller"):
                name = f"{name}Controller"

        st.markdown(f"{idx}. **{name}**")


rag = st.session_state.rag_pipeline
orch = st.session_state.orchestrator


# ---------------------------------------------------------
# Sidebar – Upload & Index PDF
# ---------------------------------------------------------
st.sidebar.header("📄 Upload SRS PDF")

uploaded_file = st.sidebar.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    accept_multiple_files=False,
)

if uploaded_file is not None:
    if st.sidebar.button("Index PDF", use_container_width=True):

        with st.spinner("Indexing PDF into RAG pipeline..."):
            info = rag.index_pdf(uploaded_file)
            st.session_state.index_info = info
            time.sleep(0.5)

        st.success("PDF indexed successfully!")


# Show index status
if st.session_state.index_info:
    info = st.session_state.index_info
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Index Status")
    st.sidebar.write(f"**Document:** {info['document_name']}")
    st.sidebar.write(f"**Pages:** {info['page_count']}")
    st.sidebar.write(f"**Total Chunks:** {info['total_chunks_in_db']}")


# ---------------------------------------------------------
# Main UI — Generate Architecture
# ---------------------------------------------------------
st.subheader("⚙️ Generate MVC Architecture")

if st.button("🚀 Extract Architecture", use_container_width=True):

    if not st.session_state.index_info:
        st.error("Please upload and index an SRS PDF first.")
    else:
        # Placeholders for each agent output
        model_preview = st.empty()
        view_preview = st.empty()
        controller_preview = st.empty()

        # ----------------------------------------------------------
        # 1) MODEL AGENT
        # ----------------------------------------------------------
        with st.spinner("Extracting Model Layer..."):
            model_json = orch.model_agent.extract_models(k=6)

        with model_preview.container():
            render_layer_items(model_json.get("model", []), "🧩 Model Layer")

        # ----------------------------------------------------------
        # 2) VIEW AGENT
        # ----------------------------------------------------------
        with st.spinner("Extracting View Layer..."):
            view_json = orch.view_agent.extract_views(k=6)

        with view_preview.container():
            render_layer_items(view_json.get("view", []), "🎨 View Layer")

        # ----------------------------------------------------------
        # 3) CONTROLLER AGENT
        # ----------------------------------------------------------
        with st.spinner("Extracting Controller Layer..."):
            controller_json = orch.controller_agent.extract_controllers(k=6)

        with controller_preview.container():
            render_layer_items(
                controller_json.get("controller", []),
                "🧠 Controller Layer",
            )

        # ----------------------------------------------------------
        # FINAL JSON MERGE
        # ----------------------------------------------------------
        architecture = {
            "model": model_json.get("model", []),
            "view": view_json.get("view", []),
            "controller": controller_json.get("controller", []),
        }

        st.session_state.architecture_map = architecture

        st.success("🎉 Architecture fully extracted!")

        st.markdown("### 📐 Full Architecture Map (JSON)")
        st.json(architecture)


# ---------------------------------------------------------
# Scaffold Generation (only if architecture exists)
# ---------------------------------------------------------
if st.session_state.architecture_map:
    st.markdown("---")
    st.subheader("🛠 Scaffold Generation")

    if st.button("Create Scaffold from Architecture", use_container_width=True):
        scaffolder: MVCScaffolder = st.session_state.scaffolder

        result = scaffolder.scaffold_all(st.session_state.architecture_map)

        model_files = result.get("models", [])
        view_files = result.get("views", [])
        controller_files = result.get("controllers", [])

        st.success("Scaffold created under `scaffolds/mvc_skeleton/`!")

        st.markdown("**Created files:**")

        if model_files:
            st.markdown("• Models:")
            for p in model_files:
                st.code(str(p.relative_to(scaffolder.project_root)))

        if view_files:
            st.markdown("• Views:")
            for p in view_files:
                st.code(str(p.relative_to(scaffolder.project_root)))

        if controller_files:
            st.markdown("• Controllers:")
            for p in controller_files:
                st.code(str(p.relative_to(scaffolder.project_root)))
