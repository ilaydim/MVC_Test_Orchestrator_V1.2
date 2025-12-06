# 🧠 MVC Test Orchestrator  
**Automatic MVC Architecture Extraction + Scaffolding from SRS Documents**  
*A multi-agent LLM-powered system for software engineering teams.*

---

## 🚀 Overview  
MVC Test Orchestrator, bir SRS (Software Requirements Specification) belgesini analiz ederek:

- **Model Layer** (entities, relationships)
- **View Layer** (screens, UI abstractions)
- **Controller Layer** (actions, flows)

çıkarır ve bunlardan otomatik bir proje iskeleti (**scaffold**) oluşturur.

Sistem 3 farklı kullanım modu sunar:

1. **Web UI (Streamlit)** – hızlı test & demo  
2. **CLI (Command Line Interface)** – gerçek kullanım senaryosu  
3. **VSCode Extension (Level 2/3)** – geliştirici ortamına gömülü kullanım (devam ediyor)

---

## 📦 Installation

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate     # Windows
