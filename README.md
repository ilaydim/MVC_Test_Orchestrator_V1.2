# 🎯 MVC Test Orchestrator v1.2

**AI-powered MVC architecture extraction and code generation system**

MVC Test Orchestrator automatically extracts an MVC (Model–View–Controller) architecture from Software Requirements Specification (SRS) documents and generates Python code using a Retrieval-Augmented Generation (RAG)–based multi-agent AI system.

This project demonstrates an AI-driven architecture extraction and code generation pipeline that combines RAG, multi-agent orchestration, and static-analysis-based validation. The approach was published as a peer-reviewed paper at IISEC 2026 (see [Publication](#-publication) below).

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Architecture and Flow](#️-architecture-and-flow)
- [Agents](#-agents)
- [Command Reference](#-command-reference)
- [Documentation](#-documentation)
- [Best Practices](#-best-practices)
- [Publication](#-publication)
- [Contributors](#-contributors)
- [License](#-license)
- [Acknowledgements](#-thank-you)

---

## ✨ Features

### 🔧 Core Capabilities

- ✅ **Automatic SRS Generation** from a user-provided project idea
- ✅ **RAG-Based Architecture Extraction** (Requirements, Models, Controllers, Views)
- ✅ **MVC Scaffold Generation** (empty Python class skeletons)
- ✅ **AI-Based Code Generation** for each MVC layer
- ✅ **Architecture Compliance Audit** using AST-based rules
- ✅ **Automatic Fixing** based on audit recommendations
- ✅ **Automatic Markdown Documentation** for all generated JSON outputs

### 🤖 AI Agent System (Overview)

- **SRS Writer Agent** – Generates an SRS document from a project idea
- **Requirements Agent** – Extracts domain entities and system functions
- **Model / Controller / View Agents** – Build MVC architecture layers
- **MVC Scaffolder** – Generates rule-based empty class files
- **Rules Agent** – Detects MVC violations using AST analysis
- **Reviewer Agent** – Converts violations into human-readable reports
- **Fixer Agent** – Applies recommended fixes automatically

---

## 💻 System Requirements

- **Python**: 3.9 or higher
- **VS Code**: 1.80+ (optional – CLI usage is supported)
- **Google Gemini API Key** (free): <https://makersuite.google.com/app/apikey>
- **Disk Space**: ~500 MB

---

## 🚀 Installation

#### 1. Download the VSIX Package

1. Go to the GitHub Releases page: <https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2/releases>
2. Open the latest release (**v1.2.0**)
3. Download the file: `mvc-test-orchestrator-1.2.0.vsix`

#### 2. Install in VS Code

1. Open **Visual Studio Code**
2. Go to the **Extensions** view
3. Click the **three dots (⋯)** menu
4. Select **"Install from VSIX…"**
5. Choose the downloaded `.vsix` file
6. Restart VS Code if prompted

### 3. Clone the Repository

```
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2
```

### 4. Create and Activate a Virtual Environment

```
python -m venv .venv

Linux / macOS : source .venv/bin/activate
Windows : .venv\Scripts\activate
```

### 5. Install Dependencies

```
pip install -r requirements.txt
```

### 6. Configure the API Key

Create a `.env` file in the project root directory and add your Google Gemini API key.

```
GOOGLE_API_KEY=your_api_key_here
```

**How to obtain an API key:**

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click Create API Key
4. Copy the generated key and paste it into the `.env` file

---

## 🎯 Quick Start

### Usage with VS Code (Recommended)

Using `@mvc` in VS Code Copilot Chat:

```
@mvc /create-srs "Write your idea."
@mvc /extract
@mvc /scaffold
@mvc /generate_code --category model
@mvc /audit
```

### Usage with CLI

```
# 1. Create SRS
python -m src.cli.mvc_arch_cli create-srs --user-idea "Simple blog with posts and comments" --output data/srs_document.txt

# 2. Extract the architecture
python -m src.cli.mvc_arch_cli extract --srs-path data/srs_document.txt --output data/architecture_map.json

# 3. Create scaffold
python -m src.cli.mvc_arch_cli scaffold --arch-path data/architecture_map.json

# 4. Generate code (category based)
python -m src.cli.mvc_arch_cli generate-code --category model --arch-path data/architecture_map.json
python -m src.cli.mvc_arch_cli generate-code --category controller --arch-path data/architecture_map.json
python -m src.cli.mvc_arch_cli generate-code --category view --arch-path data/architecture_map.json

# 5. Quality inspection
python -m src.cli.mvc_arch_cli audit --arch-path data/architecture_map.json

# 6. Autocorrect (optional)
python -m src.cli.mvc_arch_cli run-fix --audit-report data/final_audit_report.json
```

---

## 📖 Usage

### Full Workflow

#### 1. Creating or Uploading an SRS

**Option A: Create a New SRS**
```
@mvc /create-srs "Task manager for students with categories and deadlines"
```

**Option B: Use an Existing SRS**
```
# Place your SRS file in the data/ folder, then use the extract command
```

#### 2. Extracting Architecture

```
@mvc /extract
```

This command:
- Indexes the SRS to the RAG pipeline
- Extracts domain entities and functions with the Requirements Agent
- Extracts the architecture with Model, Controller, and View Agents
- Combines all results into `architecture_map.json`

#### 3. Creating a Scaffold

```
@mvc /scaffold
```

Creates empty Python class files under `scaffolds/mvc_skeleton/{models,views,controllers}/*.py`

#### 4. Code Generation

```
@mvc /generate_code --category model
@mvc /generate_code --category controller
@mvc /generate_code --category view
```

For each category: reads scaffold files, pulls relevant architecture-map and SRS context via RAG, generates code with an LLM, and writes to `generated_src/{category}s/*.py`.

#### 5. Quality Audit

```
@mvc /audit
```

Scans `generated_src/`, checks MVC-rule compliance, detects violations, and generates `final_audit_report.json`.

#### 6. Automatic Fix (Optional)

```
@mvc /fix
```

Automatically applies the recommendations in the audit report.

---

## 🏗️ Architecture and Flow

```
User Idea / SRS
    ↓
[SRS Writer Agent] → srs_document.txt
    ↓
[RAG Pipeline Indexing]
    ↓
[Requirements Agent] → requirements_analysis.json + .md
    ↓
[Model Architect Agent] → model_architecture.json + .md
    ↓
[Controller Architect Agent] → controller_architecture.json + .md
    ↓
[View Architect Agent] → view_architecture.json + .md
    ↓
architecture_map.json + .md (merged)
    ↓
[MVC Scaffolder] → scaffolds/mvc_skeleton/*.py (empty)
    ↓
[Code Generator] → generated_src/*.py (full code)
    ↓
[Rules Agent] → violations.json
    ↓
[Reviewer Agent] → final_audit_report.json
    ↓
[Fixer Agent] → Corrected code (optional)
```

---

## 🤖 Agents

### SRS Writer Agent
- **Task**: Creates an SRS document from user ideas
- **Usage**: `create-srs` command
- **Output**: `srs_document.txt`
- **LLM Usage**: ✅

### Requirements Agent
- **Task**: Extracts domain entities and system functions from SRS
- **Usage**: Inside the `extract` command
- **Output**: `requirements_analysis.json`
- **LLM Usage**: ✅

### Model Architect Agent
- **Task**: Creates the model architecture from entities
- **Dependency**: Requirements Agent output
- **Output**: `model_architecture.json`
- **LLM Usage**: ✅

### Controller Architect Agent
- **Task**: Creates the controller architecture from functions
- **Dependency**: Requirements + Model outputs
- **Output**: `controller_architecture.json`
- **LLM Usage**: ✅

### View Architect Agent
- **Task**: Defines UI screens and components
- **Dependency**: Model + Controller outputs
- **Output**: `view_architecture.json`
- **LLM Usage**: ✅

### MVC Scaffolder
- **Task**: Creates empty Python class files
- **Usage**: `scaffold` command
- **Output**: `scaffolds/mvc_skeleton/*.py`
- **LLM Usage**: ❌ (Rule-based)

### Rules Agent
- **Task**: Checks compliance with MVC rules
- **Usage**: Inside the `audit` command
- **Output**: `violations.json`
- **LLM Usage**: ❌ (AST-based)

### Reviewer Agent
- **Task**: Converts violations into human-readable reports
- **Dependency**: Rules Agent output
- **Output**: `final_audit_report.json`
- **LLM Usage**: ✅

### Recommendation Fixer Agent
- **Task**: Automatically applies audit recommendations
- **Usage**: `run-fix` command
- **LLM Usage**: ✅ (fallback, AST-based primary)

---

## 📝 Command Reference

### VS Code Commands (Copilot Chat)

| Command | Description | Parameters |
| --- | --- | --- |
| `@mvc /create-srs <idea>` | Create SRS | `idea`: Project idea |
| `@mvc /extract` | Extract architecture | - |
| `@mvc /scaffold` | Create scaffold | - |
| `@mvc /generate_code --category <cat>` | Generate code | `cat`: model/controller/view |
| `@mvc /audit` | Quality control | - |
| `@mvc /fix` | Autofix | - |

### CLI Commands

#### create-srs
```
python -m src.cli.mvc_arch_cli create-srs \
    --user-idea "Your project idea" \
    --output data/srs_document.txt
```

#### extract
```
python -m src.cli.mvc_arch_cli extract \
    --srs-path data/srs_document.txt \
    --output data/architecture_map.json
```

#### scaffold
```
python -m src.cli.mvc_arch_cli scaffold \
    --arch-path data/architecture_map.json
```

#### generate-code
```
python -m src.cli.mvc_arch_cli generate-code \
    --category model \
    --arch-path data/architecture_map.json

python -m src.cli.mvc_arch_cli generate-code \
    --category controller \
    --arch-path data/architecture_map.json

python -m src.cli.mvc_arch_cli generate-code \
    --category view \
    --arch-path data/architecture_map.json
```

#### audit
```
python -m src.cli.mvc_arch_cli audit \
    --arch-path data/architecture_map.json
```

#### run-fix
```
python -m src.cli.mvc_arch_cli run-fix \
    --audit-report data/final_audit_report.json
```

---

## 📚 Documentation

- **Prompt Templates**: Editable prompts in the `.github/prompts/` folder
- **Source Code**: Docstrings and type hints are available for each agent

### Key Concepts Demonstrated

This project demonstrates the implementation of:
- MVC (Model-View-Controller) architecture
- RAG (Retrieval-Augmented Generation) systems
- AI agent architectures
- Prompt engineering
- Python AST parsing
- ChromaDB vector database usage

---

## 🎓 Best Practices

### SRS Writing Tips

✅ **Good Examples**:
```
"Simple blog with posts and comments"
"Task manager for students with categories"
"E-commerce with products, cart, and orders"
```

❌ **Things to Avoid**:
```
"Full-featured enterprise ERP system with..."
"Complex social network with messaging, stories, live streaming..."
```

**Rule**: Simple and focused project ideas yield better results.

### Code Generation Strategy

1. **Sequential Generation**: Models first, then controllers, last views
2. **Category-Based Testing**: Check each category after generation
3. **Use of Audits**: Always run audits after code generation
4. **Iterative Improvement**: Correct or regenerate code based on audit reports

### Architectural Limitations

- **Models**: Maximum 8-10 models recommended
- **Controllers**: Maximum 6-8 controllers
- **Views**: Maximum 6-8 views
- **Lines Per File**: 20-50 lines (ideal for readability)

---

## 📄 Publication

**MVC Test Orchestrator: SRS-Driven Architecture Extraction** — IISEC 2026 (5th International Informatics and Software Engineering Conference).
İ. Dim, Y. Saklavcı, K. Aytekin, M. Karakaya. [IEEE Xplore](https://ieeexplore.ieee.org/document/11418519)

---

## 👥 Contributors

- **İlayda Dim**
- **Kaan Aytekin**
- **Yaren Saklavcı**

**Academic Advisor / Co-author:** Murat Karakaya

### Project Context

MVC Test Orchestrator explores:
- AI-assisted software architecture extraction
- Retrieval-Augmented Generation (RAG) pipelines
- Multi-agent LLM-based systems
- Automated code generation and validation workflows

Contributions, suggestions, and feedback are welcome.

---

## 📄 License

[Add a license, e.g., MIT — see note below]

---

## 🙏 Thank you

- **Google Gemini API**: For LLM support
- **ChromaDB**: For vector database
- **Sentence Transformers**: For embedding models
