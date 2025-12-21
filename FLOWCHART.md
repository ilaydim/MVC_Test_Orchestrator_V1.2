# MVC Test Orchestrator - Flowchart

## Ana Akış Diagramı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BAŞLANGIÇ: İki Seçenek                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
        ┌──────────────────────┐           ┌──────────────────────┐
        │  1. create-srs       │           │  2. extract          │
        │  (SRS Oluşturma)     │           │  (SRS'den Çıkarma)   │
        └──────────────────────┘           └──────────────────────┘
                    │                                   │
                    │                                   │
                    ▼                                   ▼
        ┌──────────────────────┐           ┌──────────────────────┐
        │  SRS Writer Agent    │           │  RAG Pipeline        │
        │  (LLM ile SRS üretir)│           │  index_srs()         │
        └──────────────────────┘           └──────────────────────┘
                    │                                   │
                    │                                   │
                    ▼                                   │
        ┌──────────────────────┐                       │
        │  srs_document.txt    │◄──────────────────────┘
        │  (data/srs_document  │
        │   .txt)              │
        └──────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              PHASE 0.5: RAG Pipeline Indexing                 │
        │              (SRS dosyasını vector store'a ekle)              │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │          PHASE 1-2: MVC Architecture Extraction              │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Requirements Agent                                    │ │
        │  │  - extract_analysis()                                  │ │
        │  │  - RAG query: domain entities & system functions       │ │
        │  │  - Output: requirements_analysis.json                  │ │
        │  └────────────────────────────────────────────────────────┘ │
        │                    │                                         │
        │                    ▼                                         │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Model Architect Agent                                 │ │
        │  │  - extract_models()                                    │ │
        │  │  - Input: requirements_analysis.json (domain entities) │ │
        │  │  - RAG query: entity attributes & relationships        │ │
        │  │  - Output: model_architecture.json                     │ │
        │  └────────────────────────────────────────────────────────┘ │
        │                    │                                         │
        │                    ▼                                         │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Controller Architect Agent                            │ │
        │  │  - extract_controllers()                               │ │
        │  │  - Input: requirements_analysis.json (functions)       │ │
        │  │  - Input: model_architecture.json (entities)           │ │
        │  │  - RAG query: workflows & controller actions           │ │
        │  │  - Output: controller_architecture.json                │ │
        │  └────────────────────────────────────────────────────────┘ │
        │                    │                                         │
        │                    ▼                                         │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  View Architect Agent                                  │ │
        │  │  - extract_views()                                     │ │
        │  │  - Input: model_architecture.json                      │ │
        │  │  - Input: controller_architecture.json                 │ │
        │  │  - RAG query: UI screens & components                  │ │
        │  │  - Output: view_architecture.json                      │ │
        │  └────────────────────────────────────────────────────────┘ │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              Architecture Map Kombinasyonu                    │
        │  {                                                           │
        │    "model": [...],      (model_architecture.json)           │
        │    "view": [...],       (view_architecture.json)            │
        │    "controller": [...]  (controller_architecture.json)      │
        │  }                                                           │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────┐
        │  architecture_map.json│
        │  (data/architecture_  │
        │   map.json)           │
        └──────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                   PHASE 3: Scaffold                          │
        │                   (scaffold command)                         │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  MVC Scaffolder Agent                                  │ │
        │  │  - scaffold_all()                                      │ │
        │  │  - Input: architecture_map.json                        │ │
        │  │  - Rule-based (no LLM)                                 │ │
        │  │  - Output: Boş .py dosyaları                           │ │
        │  └────────────────────────────────────────────────────────┘ │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │  scaffolds/mvc_skeleton/                                     │
        │    ├── models/        (boş class dosyaları)                 │
        │    ├── views/         (boş class dosyaları)                 │
        │    └── controllers/   (boş class dosyaları)                 │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              PHASE 4: Code Generation                        │
        │              (generate-code command)                         │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  LLM Code Generator                                    │ │
        │  │  - Input: scaffold files (boş sınıflar)                │ │
        │  │  - Input: architecture_map.json                        │ │
        │  │  - Input: srs_document.txt (RAG context)               │ │
        │  │  - Prompt template: generate_{category}_code.prompt.md │ │
        │  │  - Output: Dolu kod dosyaları                          │ │
        │  └────────────────────────────────────────────────────────┘ │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │  generated_src/                                               │
        │    ├── models/        (gerçek kod)                          │
        │    ├── views/         (gerçek kod)                          │
        │    └── controllers/   (gerçek kod)                          │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              PHASE 5: Quality Audit                          │
        │              (audit / run-audit command)                     │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Rules Agent                                          │ │
        │  │  - detect_violations()                                │ │
        │  │  - Input: generated_src/ (Python dosyaları)           │ │
        │  │  - AST parsing + file scanning                        │ │
        │  │  - MVC dependency violation detection                 │ │
        │  │  - Output: violations.json                            │ │
        │  └────────────────────────────────────────────────────────┘ │
        │                    │                                         │
        │                    ▼                                         │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Reviewer Agent                                       │ │
        │  │  - generate_audit_report()                            │ │
        │  │  - Input: violations.json                             │ │
        │  │  - LLM ile human-readable rapor                       │ │
        │  │  - Output: final_audit_report.json                    │ │
        │  └────────────────────────────────────────────────────────┘ │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────┐
        │  final_audit_report  │
        │  .json               │
        │  (data/final_audit_  │
        │   report.json)       │
        └──────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              PHASE 6: Auto-Fix (Optional)                     │
        │              (run-fix command)                                │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐ │
        │  │  Recommendation Fixer Agent                           │ │
        │  │  - apply_recommendations()                            │ │
        │  │  - Input: final_audit_report.json                     │ │
        │  │  - AST-based fixes (import removals)                  │ │
        │  │  - LLM-based fixes (complex cases)                    │ │
        │  │  - Output: Fixed code in generated_src/               │ │
        │  └────────────────────────────────────────────────────────┘ │
        └──────────────────────────────────────────────────────────────┘
                    │
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────┐
        │  generated_src/ (güncellenmiş kod)                           │
        └──────────────────────────────────────────────────────────────┘
```

## Detaylı Akış Adımları

### 1. SRS Oluşturma veya Yükleme
```
create-srs command
    │
    ├─→ SRS Writer Agent
    │       │
    │       ├─→ LLM (create_srs.prompt.md)
    │       │
    │       └─→ srs_document.txt (data/)
```

veya

```
extract command (SRS path verilirse)
    │
    └─→ srs_document.txt (mevcut dosya kullanılır)
```

### 2. RAG Indexing
```
RAG Pipeline
    │
    ├─→ PDFLoader (eğer PDF ise)
    ├─→ TextLoader (eğer TXT ise)
    │
    ├─→ Chunker (RecursiveCharacterTextSplitter)
    │       ├─→ chunk_size: DEFAULT_CHUNK_SIZE
    │       └─→ overlap: DEFAULT_CHUNK_OVERLAP
    │
    ├─→ Embedder (SentenceTransformer)
    │       └─→ model_name: EMBEDDING_MODEL_NAME
    │
    └─→ VectorStore (ChromaDB)
            └─→ Collection: "mvc_srs_collection"
```

### 3. Architecture Extraction Pipeline

#### 3.1 Requirements Agent
```
Requirements Agent
    │
    ├─→ RAG Query: "Analyze entire document for domain entities and system functions"
    │
    ├─→ retrieve_chunks(query, k=DEFAULT_TOP_K)
    │
    ├─→ LLM (extract_requirements.prompt.md)
    │
    └─→ requirements_analysis.json
            {
                "project_name": "...",
                "domain_entities": [...],
                "system_functions": [...]
            }
```

#### 3.2 Model Architect Agent
```
Model Architect Agent
    │
    ├─→ Input: requirements_analysis.json (domain_entities)
    │
    ├─→ RAG Query: "For entities [X, Y, Z], identify attributes and relationships"
    │
    ├─→ retrieve_chunks(query, k=DEFAULT_TOP_K)
    │
    ├─→ LLM (extract_model.prompt.md)
    │
    └─→ model_architecture.json
            {
                "model": [
                    {
                        "name": "...",
                        "attributes": [...],
                        "relationships": [...]
                    }
                ]
            }
```

#### 3.3 Controller Architect Agent
```
Controller Architect Agent
    │
    ├─→ Input: requirements_analysis.json (system_functions)
    ├─→ Input: model_architecture.json (entities)
    │
    ├─→ RAG Query: "For functions [A, B] and models [X, Y], identify workflows"
    │
    ├─→ retrieve_chunks(query, k=DEFAULT_TOP_K)
    │
    ├─→ LLM (extract_controller.prompt.md)
    │
    └─→ controller_architecture.json
            {
                "controller": [
                    {
                        "name": "...",
                        "actions": [...],
                        "dependencies": [...]
                    }
                ]
            }
```

#### 3.4 View Architect Agent
```
View Architect Agent
    │
    ├─→ Input: model_architecture.json
    ├─→ Input: controller_architecture.json
    │
    ├─→ RAG Query: "For models [X, Y] and actions [A, B], identify UI screens"
    │
    ├─→ retrieve_chunks(query, k=DEFAULT_TOP_K)
    │
    ├─→ LLM (extract_view.prompt.md)
    │
    └─→ view_architecture.json
            {
                "view": [
                    {
                        "name": "...",
                        "components": [...],
                        "interactions": [...]
                    }
                ]
            }
```

#### 3.5 Architecture Map Kombinasyonu
```
All Architect Agents
    │
    └─→ architecture_map.json
            {
                "srs": "...",  (full context from RAG)
                "architecture": {
                    "model": [...],        (from model_architecture.json)
                    "view": [...],         (from view_architecture.json)
                    "controller": [...]    (from controller_architecture.json)
                }
            }
```

### 4. Scaffold Generation
```
MVC Scaffolder
    │
    ├─→ Input: architecture_map.json
    │
    ├─→ Rule-based file generation (NO LLM)
    │
    ├─→ scaffolds/mvc_skeleton/models/*.py (empty classes)
    ├─→ scaffolds/mvc_skeleton/views/*.py (empty classes)
    └─→ scaffolds/mvc_skeleton/controllers/*.py (empty classes)
```

### 5. Code Generation
```
LLM Code Generator
    │
    ├─→ For each scaffold file:
    │       │
    │       ├─→ Load skeleton content
    │       ├─→ Load matching architecture item
    │       ├─→ Load SRS context (via RAG if indexed)
    │       │
    │       ├─→ Prompt: generate_{category}_code.prompt.md
    │       │       ├─→ {{class_name}}
    │       │       ├─→ {{skeleton}}
    │       │       ├─→ {{arch_info}}
    │       │       ├─→ {{srs_context}}
    │       │       └─→ {{related_models/views}} (for controllers)
    │       │
    │       ├─→ LLM.generate_content(prompt)
    │       │
    │       └─→ Write to generated_src/{category}s/*.py
    │
    └─→ generated_src/
            ├── models/*.py (full code)
            ├── views/*.py (full code)
            └── controllers/*.py (full code)
```

### 6. Quality Audit

#### 6.1 Rules Agent
```
Rules Agent
    │
    ├─→ Input: generated_src/ (all .py files)
    │
    ├─→ AST Parsing + File Scanning
    │       ├─→ Check MVC dependency violations
    │       ├─→ Model → View violations
    │       ├─→ Model → Controller violations
    │       ├─→ View → Model violations
    │       └─→ Structural inconsistencies
    │
    └─→ violations.json
            {
                "violations": [
                    {
                        "violation_type": "...",
                        "file": "...",
                        "problem": "..."
                    }
                ],
                "total_count": N
            }
```

#### 6.2 Reviewer Agent
```
Reviewer Agent
    │
    ├─→ Input: violations.json
    │
    ├─→ LLM (reviewer prompt)
    │       └─→ Translates technical violations to human-readable recommendations
    │
    └─→ final_audit_report.json
            {
                "audit_summary": "...",
                "passed": true/false,
                "recommendations": [
                    {
                        "violation_type": "...",
                        "file": "...",
                        "problem": "...",
                        "recommendation": "..."
                    }
                ]
            }
```

### 7. Auto-Fix (Optional)
```
Recommendation Fixer Agent
    │
    ├─→ Input: final_audit_report.json
    │
    ├─→ For each recommendation:
    │       │
    │       ├─→ Try AST-based fix (for import violations)
    │       │       └─→ Remove problematic imports
    │       │
    │       └─→ Fallback to LLM-based fix
    │               └─→ Strict prompt (only fix specific issue)
    │
    └─→ Updated files in generated_src/
```

## Komut Özeti

| Komut | Açıklama | Çıktı |
|-------|----------|-------|
| `create-srs` | Kullanıcı fikrinden SRS oluşturur | `srs_document.txt` |
| `extract` | SRS'den MVC mimarisini çıkarır | `architecture_map.json` + tüm `*_architecture.json` |
| `scaffold` | Boş sınıf dosyaları oluşturur | `scaffolds/mvc_skeleton/*.py` |
| `generate-code` | Scaffold'lara gerçek kod üretir | `generated_src/*.py` |
| `audit` | Kod kalitesi denetimi yapar | `final_audit_report.json` |
| `run-fix` | Audit önerilerini otomatik uygular | Güncellenmiş `generated_src/*.py` |

## Dosya Yapısı

```
project_root/
├── data/
│   ├── srs_document.txt
│   ├── requirements_analysis.json
│   ├── model_architecture.json
│   ├── controller_architecture.json
│   ├── view_architecture.json
│   ├── architecture_map.json
│   ├── violations.json
│   └── final_audit_report.json
│
├── scaffolds/
│   └── mvc_skeleton/
│       ├── models/*.py (empty)
│       ├── views/*.py (empty)
│       └── controllers/*.py (empty)
│
└── generated_src/
    ├── models/*.py (full code)
    ├── views/*.py (full code)
    └── controllers/*.py (full code)
```

## Notlar

1. **RAG Pipeline**: Tüm extraction aşamalarında RAG kullanılır. SRS önce indexlenir, sonra her agent ilgili query'ler ile chunk'ları çeker.

2. **Agent Bağımlılıkları**:
   - Model Agent → Requirements Agent çıktısına bağımlı
   - Controller Agent → Requirements + Model çıktılarına bağımlı
   - View Agent → Model + Controller çıktılarına bağımlı

3. **LLM Kullanımı**:
   - SRS Writer: ✅
   - Requirements Agent: ✅
   - Model/Controller/View Agents: ✅
   - Scaffolder: ❌ (rule-based)
   - Code Generator: ✅
   - Rules Agent: ❌ (AST-based)
   - Reviewer Agent: ✅
   - Fixer Agent: ✅ (fallback)

4. **Prompt Templates**: `.github/prompts/` klasöründe:
   - `create_srs.prompt.md`
   - `extract_requirements.prompt.md`
   - `extract_model.prompt.md`
   - `extract_controller.prompt.md`
   - `extract_view.prompt.md`
   - `generate_{category}_code.prompt.md`

