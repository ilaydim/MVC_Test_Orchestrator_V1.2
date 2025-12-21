# 🎯 MVC Test Orchestrator v1.2

**AI-powered MVC architecture extraction and code generation system**

MVC Test Orchestrator, Software Requirements Specification (SRS) belgelerinden MVC mimarisini otomatik olarak çıkarır ve Python kodunu üreten, RAG (Retrieval-Augmented Generation) tabanlı bir AI agent sistemidir.

> 📦 **Kurulum**: [INSTALL.md](INSTALL.md) dosyasında detaylı kurulum adımları bulunmaktadır.  
> 🚀 **Dağıtım**: Projeyi GitHub'a yüklemek için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın.  
> 📖 **Kullanım**: Başka projelerde kullanım için [USAGE.md](USAGE.md) dosyasına bakın.

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Sistem Gereksinimleri](#-sistem-gereksinimleri)
- [Kurulum](#-kurulum) - [Detaylı Kurulum Rehberi (INSTALL.md)](INSTALL.md)
- [Hızlı Başlangıç](#-hızlı-başlangıç)
- [Kullanım](#-kullanım)
- [Mimari ve Akış](#-mimari-ve-akış)
- [Agent'lar](#-agentlar)
- [Dosya Yapısı](#-dosya-yapısı)
- [Komut Referansı](#-komut-referansı)
- [Yapılandırma](#-yapılandırma)
- [Sorun Giderme](#-sorun-giderme)
- [Dokümantasyon](#-dokümantasyon)
- [Başka Projelerde Kullanım](#-başka-projelerde-kullanım)

---

## ✨ Özellikler

### 🔧 Temel Özellikler

- ✅ **SRS Oluşturma**: Kullanıcı fikrinden otomatik SRS belgesi oluşturma
- ✅ **RAG Tabanlı Mimari Çıkarma**: SRS'den MVC mimarisini çıkarma (Requirements, Model, Controller, View)
- ✅ **Otomatik Scaffold Oluşturma**: Boş sınıf dosyaları oluşturma
- ✅ **Kod Üretimi**: LLM ile gerçek Python kodu üretme
- ✅ **Kalite Denetimi**: MVC kurallarına uyum kontrolü ve ihlal tespiti
- ✅ **Otomatik Düzeltme**: Denetim raporundaki önerileri otomatik uygulama

### 🤖 AI Agent Sistemi

- **SRS Writer Agent**: Kullanıcı fikrinden SRS oluşturur
- **Requirements Agent**: SRS'den domain entities ve system functions çıkarır
- **Model Architect Agent**: Entity'lerden model mimarisini oluşturur
- **Controller Architect Agent**: Fonksiyonlardan controller mimarisini oluşturur
- **View Architect Agent**: UI ekranlarını ve bileşenlerini belirler
- **MVC Scaffolder**: Rule-based scaffold dosyaları oluşturur
- **Rules Agent**: AST tabanlı MVC ihlal tespiti yapar
- **Reviewer Agent**: İhlalleri human-readable raporlara dönüştürür
- **Recommendation Fixer Agent**: Önerileri otomatik olarak uygular

---

## 💻 Sistem Gereksinimleri

- **Python**: 3.9 veya üzeri
- **VS Code**: 1.80.0 veya üzeri (opsiyonel - CLI de kullanılabilir)
- **Google Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)'dan ücretsiz alınabilir
- **Disk Alanı**: ~500MB (bağımlılıklar ve model için)

### Model Yapılandırması

Varsayılan model: `gemini-2.5-flash`

Model değiştirmek için `src/core/config.py` dosyasını düzenleyin:
- `gemini-2.5-flash` - Varsayılan (önerilen)
- `gemini-1.5-flash` - Alternatif
- `gemini-pro` - Eski ama stabil

---

## 🚀 Kurulum

### GitHub'dan İndirme ve Kurulum

#### Yöntem 1: Otomatik Kurulum Scripti (Önerilen)

**Linux/Mac:**
```bash
# Repository'yi klonlayın
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2

# Kurulum scriptini çalıştırın
chmod +x install.sh
./install.sh
```

**Windows:**
```powershell
# Repository'yi klonlayın
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2

# Kurulum scriptini çalıştırın
install.bat
```

#### Yöntem 2: Manuel Kurulum

```bash
# 1. Repository'yi klonlayın
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2

# 2. Virtual environment oluşturun (önerilen)
python -m venv .venv

# 3. Virtual environment'ı aktifleştirin
# Linux/Mac:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 4. Bağımlılıkları yükleyin
pip install --upgrade pip
pip install -r requirements.txt

# 5. .env dosyası oluşturun
# Windows
echo GOOGLE_API_KEY=your_api_key_here > .env
# Linux/Mac
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# 6. API key'inizi ekleyin
# .env dosyasını düzenleyin ve Google Gemini API key'inizi ekleyin
# API key almak için: https://makersuite.google.com/app/apikey
```

#### Yöntem 3: Python Paketi Olarak Kurulum (Geliştirme Aşamasında)

```bash
# Repository'yi klonlayın
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2

# Paketi kurun (editable mode)
pip install -e .

# veya development dependencies ile
pip install -e ".[dev]"
```

### API Key'i Ayarlayın

`.env` dosyası oluşturun ve Google Gemini API key'inizi ekleyin:

```bash
# Manuel oluşturma
# Windows
echo GOOGLE_API_KEY=your_api_key_here > .env

# Linux/Mac
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

veya `.env` dosyasını manuel olarak oluşturup içine ekleyin:

```env
GOOGLE_API_KEY=your_api_key_here
```

**API Key Nasıl Alınır?**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine gidin
2. Google hesabınızla giriş yapın
3. "Create API Key" butonuna tıklayın
4. Oluşturulan key'i kopyalayıp `.env` dosyasına yapıştırın

### 3. VS Code Extension (Opsiyonel)

VS Code kullanıyorsanız:

1. `mvc-test-orchestrator` klasörünü VS Code'da açın
2. Extension'ı build edin: `npm install && npm run compile`
3. F5 ile test edin veya `.vsix` paketini oluşturun

---

## 🎯 Hızlı Başlangıç

### VS Code ile Kullanım (Önerilen)

VS Code Copilot Chat'te `@mvc` kullanarak:

```bash
@mvc /create-srs Simple blog with posts and comments
@mvc /extract
@mvc /scaffold
@mvc /generate_code --category model
@mvc /audit
```

### CLI ile Kullanım

```bash
# 1. SRS oluştur
python -m src.cli.mvc_arch_cli create-srs --user-idea "Simple blog with posts and comments" --output data/srs_document.txt

# 2. Mimariyi çıkar
python -m src.cli.mvc_arch_cli extract --srs-path data/srs_document.txt --output data/architecture_map.json

# 3. Scaffold oluştur
python -m src.cli.mvc_arch_cli scaffold --arch-path data/architecture_map.json

# 4. Kod üret (kategori bazlı)
python -m src.cli.mvc_arch_cli generate-code --category model --arch-path data/architecture_map.json
python -m src.cli.mvc_arch_cli generate-code --category controller --arch-path data/architecture_map.json
python -m src.cli.mvc_arch_cli generate-code --category view --arch-path data/architecture_map.json

# 5. Kalite denetimi
python -m src.cli.mvc_arch_cli audit --arch-path data/architecture_map.json

# 6. Otomatik düzeltme (opsiyonel)
python -m src.cli.mvc_arch_cli run-fix --audit-report data/final_audit_report.json
```

---

## 📖 Kullanım

### Tam İş Akışı

#### 1. SRS Oluşturma veya Yükleme

**Seçenek A: Yeni SRS Oluştur**
```bash
@mvc /create-srs "Task manager for students with categories and deadlines"
```

**Seçenek B: Mevcut SRS Kullan**
```bash
# SRS dosyanızı data/ klasörüne koyun, sonra extract komutunu kullanın
```

#### 2. Mimari Çıkarma

```bash
@mvc /extract
```

Bu komut şunları yapar:
- SRS'yi RAG pipeline'a indexler
- Requirements Agent ile domain entities ve functions çıkarır
- Model, Controller, View Agent'ları ile mimariyi çıkarır
- Tüm sonuçları `architecture_map.json`'da birleştirir

#### 3. Scaffold Oluşturma

```bash
@mvc /scaffold
```

Boş Python sınıf dosyaları oluşturur:
- `scaffolds/mvc_skeleton/models/*.py`
- `scaffolds/mvc_skeleton/views/*.py`
- `scaffolds/mvc_skeleton/controllers/*.py`

#### 4. Kod Üretimi

Kategori bazlı kod üretimi (sırayla yapılması önerilir):

```bash
@mvc /generate_code --category model
@mvc /generate_code --category controller
@mvc /generate_code --category view
```

Her kategori için:
- Scaffold dosyalarını okur
- Architecture map'ten ilgili bilgileri alır
- SRS context'ini RAG ile çeker
- LLM ile gerçek kodu üretir
- `generated_src/{category}s/*.py` altına yazar

#### 5. Kalite Denetimi

```bash
@mvc /audit
```

- `generated_src/` klasöründeki dosyaları tarar
- MVC kurallarına uyumu kontrol eder
- İhlalleri tespit eder ve raporlar
- `final_audit_report.json` oluşturur

#### 6. Otomatik Düzeltme (Opsiyonel)

```bash
@mvc /fix
```

Audit raporundaki önerileri otomatik olarak uygular.

---

## 🏗️ Mimari ve Akış

### Genel Akış Diagramı

```
User Idea / SRS
    ↓
[SRS Writer Agent] → srs_document.txt
    ↓
[RAG Pipeline Indexing]
    ↓
[Requirements Agent] → requirements_analysis.json
    ↓
[Model Architect Agent] → model_architecture.json
    ↓
[Controller Architect Agent] → controller_architecture.json
    ↓
[View Architect Agent] → view_architecture.json
    ↓
architecture_map.json (birleştirilmiş)
    ↓
[MVC Scaffolder] → scaffolds/mvc_skeleton/*.py (boş)
    ↓
[Code Generator] → generated_src/*.py (dolu kod)
    ↓
[Rules Agent] → violations.json
    ↓
[Reviewer Agent] → final_audit_report.json
    ↓
[Fixer Agent] → Düzeltilmiş kod (opsiyonel)
```

Detaylı flowchart için: [FLOWCHART.md](FLOWCHART.md)

### RAG Pipeline

Sistem, SRS belgelerini işlemek için RAG (Retrieval-Augmented Generation) kullanır:

1. **PDFLoader / TextLoader**: SRS dosyasını yükler
2. **Chunker**: Metni parçalara böler (RecursiveCharacterTextSplitter)
3. **Embedder**: SentenceTransformer ile embedding oluşturur
4. **VectorStore**: ChromaDB'de saklar
5. **Query**: Agent'lar ilgili chunk'ları çeker

---

## 🤖 Agent'lar

### SRS Writer Agent
- **Görev**: Kullanıcı fikrinden SRS belgesi oluşturur
- **Kullanım**: `create-srs` komutu
- **Çıktı**: `srs_document.txt`
- **LLM Kullanımı**: ✅

### Requirements Agent
- **Görev**: SRS'den domain entities ve system functions çıkarır
- **Kullanım**: `extract` komutu içinde
- **Çıktı**: `requirements_analysis.json`
- **LLM Kullanımı**: ✅

### Model Architect Agent
- **Görev**: Entity'lerden model mimarisini oluşturur
- **Bağımlılık**: Requirements Agent çıktısı
- **Çıktı**: `model_architecture.json`
- **LLM Kullanımı**: ✅

### Controller Architect Agent
- **Görev**: Fonksiyonlardan controller mimarisini oluşturur
- **Bağımlılık**: Requirements + Model çıktıları
- **Çıktı**: `controller_architecture.json`
- **LLM Kullanımı**: ✅

### View Architect Agent
- **Görev**: UI ekranlarını ve bileşenlerini belirler
- **Bağımlılık**: Model + Controller çıktıları
- **Çıktı**: `view_architecture.json`
- **LLM Kullanımı**: ✅

### MVC Scaffolder
- **Görev**: Boş Python sınıf dosyaları oluşturur
- **Kullanım**: `scaffold` komutu
- **Çıktı**: `scaffolds/mvc_skeleton/*.py`
- **LLM Kullanımı**: ❌ (Rule-based)

### Rules Agent
- **Görev**: MVC kurallarına uyumu kontrol eder
- **Kullanım**: `audit` komutu içinde
- **Çıktı**: `violations.json`
- **LLM Kullanımı**: ❌ (AST-based)

### Reviewer Agent
- **Görev**: İhlalleri human-readable raporlara dönüştürür
- **Bağımlılık**: Rules Agent çıktısı
- **Çıktı**: `final_audit_report.json`
- **LLM Kullanımı**: ✅

### Recommendation Fixer Agent
- **Görev**: Audit önerilerini otomatik uygular
- **Kullanım**: `run-fix` komutu
- **LLM Kullanımı**: ✅ (fallback, AST-based primary)

---

## 📁 Dosya Yapısı

### Proje Yapısı

```
MVC_Test_Orchestrator_V1.2/
├── data/                          # Çıktı dosyaları
│   ├── srs_document.txt          # Oluşturulan/yüklenen SRS
│   ├── requirements_analysis.json
│   ├── model_architecture.json
│   ├── controller_architecture.json
│   ├── view_architecture.json
│   ├── architecture_map.json     # Birleştirilmiş mimari
│   ├── violations.json           # Audit ihlalleri
│   └── final_audit_report.json   # Final audit raporu
│
├── scaffolds/                     # Scaffold dosyaları (boş)
│   └── mvc_skeleton/
│       ├── models/*.py
│       ├── views/*.py
│       └── controllers/*.py
│
├── generated_src/                 # Üretilen kod (dolu)
│   ├── models/*.py
│   ├── views/*.py
│   └── controllers/*.py
│
├── src/
│   ├── agents/                    # AI Agent'ları
│   │   ├── srs_writer_agent.py
│   │   ├── rules_agent.py
│   │   ├── reviewer_agent.py
│   │   ├── recommendation_fixer_agent.py
│   │   ├── architect_agent/
│   │   │   ├── requirements_agent.py
│   │   │   ├── model_architect_agent.py
│   │   │   ├── controller_architect_agent.py
│   │   │   ├── view_architect_agent.py
│   │   │   └── base_architect_agent.py
│   │   └── scaffolder/
│   │       └── mvc_scaffolder.py
│   │
│   ├── cli/                       # CLI arayüzü
│   │   └── mvc_arch_cli.py
│   │
│   ├── core/                      # Çekirdek modüller
│   │   ├── config.py             # Yapılandırma
│   │   └── llm_client.py         # LLM istemcisi
│   │
│   └── rag/                       # RAG pipeline
│       └── rag_pipeline.py
│
├── .github/
│   └── prompts/                   # Prompt şablonları
│       ├── create_srs.prompt.md
│       ├── extract_requirements.prompt.md
│       ├── extract_model.prompt.md
│       ├── extract_controller.prompt.md
│       ├── extract_view.prompt.md
│       └── generate_{category}_code.prompt.md
│
├── mvc-test-orchestrator/         # VS Code Extension
│   ├── src/
│   │   └── extension.ts
│   └── package.json
│
├── requirements.txt               # Python bağımlılıkları
├── .env                          # API key (oluşturulmalı)
└── README.md                     # Bu dosya
```

---

## 📝 Komut Referansı

### VS Code Komutları (Copilot Chat)

| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `@mvc /create-srs <idea>` | SRS oluştur | `idea`: Proje fikri |
| `@mvc /extract` | Mimari çıkar | - |
| `@mvc /scaffold` | Scaffold oluştur | - |
| `@mvc /generate_code --category <cat>` | Kod üret | `cat`: model/controller/view |
| `@mvc /audit` | Kalite denetimi | - |
| `@mvc /fix` | Otomatik düzelt | - |

### CLI Komutları

#### create-srs
```bash
python -m src.cli.mvc_arch_cli create-srs \
    --user-idea "Your project idea" \
    --output data/srs_document.txt
```

#### extract
```bash
python -m src.cli.mvc_arch_cli extract \
    --srs-path data/srs_document.txt \
    --output data/architecture_map.json
```

#### scaffold
```bash
python -m src.cli.mvc_arch_cli scaffold \
    --arch-path data/architecture_map.json
```

#### generate-code
```bash
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
```bash
python -m src.cli.mvc_arch_cli audit \
    --arch-path data/architecture_map.json
```

#### run-fix
```bash
python -m src.cli.mvc_arch_cli run-fix \
    --audit-report data/final_audit_report.json
```

---

## ⚙️ Yapılandırma

### API Key

`.env` dosyasında:
```env
GOOGLE_API_KEY=your_api_key_here
```

### Model Ayarları

`src/core/config.py` dosyasında:
```python
DEFAULT_MODEL = "gemini-2.5-flash"  # veya gemini-1.5-flash, gemini-pro
DEFAULT_TOP_K = 5  # RAG için chunk sayısı
```

### RAG Ayarları

`src/rag/rag_pipeline.py` içinde:
- `DEFAULT_CHUNK_SIZE`: Chunk boyutu (varsayılan: 1000)
- `DEFAULT_CHUNK_OVERLAP`: Chunk overlap (varsayılan: 200)
- `EMBEDDING_MODEL_NAME`: Embedding model adı

### Prompt Şablonları

Prompt'ları özelleştirmek için `.github/prompts/` klasöründeki `.md` dosyalarını düzenleyin:
- `create_srs.prompt.md`
- `extract_requirements.prompt.md`
- `extract_model.prompt.md`
- `extract_controller.prompt.md`
- `extract_view.prompt.md`
- `generate_model_code.prompt.md`
- `generate_controller_code.prompt.md`
- `generate_view_code.prompt.md`

---

## 🔧 Sorun Giderme

### API Quota Hatası

**Hata**: `QuotaExceededError`

**Çözüm**:
- Google AI Studio'da quota durumunuzu kontrol edin
- 24 saat bekleyin veya yeni API key kullanın
- Free tier limitlerini kontrol edin

### LLM Bağlantı Hatası

**Hata**: `LLMConnectionError`

**Çözüm**:
- İnternet bağlantınızı kontrol edin
- API key'in doğru olduğundan emin olun
- `.env` dosyasının doğru konumda olduğunu kontrol edin

### Dosya Bulunamadı Hatası

**Hata**: `File not found`

**Çözüm**:
- Önceki adımların tamamlandığından emin olun
- Dosya yollarının doğru olduğunu kontrol edin
- `data/` klasörünün var olduğundan emin olun

### ChromaDB Telemetry Hatası

**Hata**: Telemetry ile ilgili hatalar

**Çözüm**:
- Sistem otomatik olarak telemetry'yi devre dışı bırakır
- Hata devam ederse, `requirements.txt`'teki ChromaDB versiyonunu kontrol edin (0.4.15 önerilir)

### VS Code Extension Çalışmıyor

**Hata**: Extension komutları görünmüyor

**Çözüm**:
- Extension'ı yeniden build edin: `npm run compile`
- VS Code'u yeniden başlatın
- Copilot Chat'in aktif olduğundan emin olun

---

## 📚 Dokümantasyon

### Ekstra Dokümantasyon

- **Flowchart**: Detaylı akış diagramı için [FLOWCHART.md](FLOWCHART.md) dosyasına bakın
- **Prompt Şablonları**: `.github/prompts/` klasöründe düzenlenebilir prompt'lar
- **Kaynak Kod**: Her agent için docstring'ler ve type hints mevcuttur

### Öğrenme Kaynakları

Bu proje eğitim amaçlıdır ve şunları öğrenmenize yardımcı olur:
- MVC (Model-View-Controller) mimarisi
- RAG (Retrieval-Augmented Generation) sistemleri
- AI Agent mimarileri
- Prompt engineering
- Python AST parsing
- ChromaDB vector database kullanımı

---

## 🎓 Best Practices

### SRS Yazma İpuçları

✅ **İyi Örnekler**:
```
"Simple blog with posts and comments"
"Task manager for students with categories"
"E-commerce with products, cart, and orders"
```

❌ **Kaçınılması Gerekenler**:
```
"Full-featured enterprise ERP system with..."
"Complex social network with messaging, stories, live streaming..."
```

**Kural**: Basit ve odaklanmış proje fikirleri daha iyi sonuçlar verir.

### Kod Üretimi Stratejisi

1. **Sıralı Üretim**: Önce models, sonra controllers, en son views
2. **Kategori Bazlı Test**: Her kategoriyi ürettikten sonra kontrol edin
3. **Audit Kullanımı**: Kod üretiminden sonra mutlaka audit çalıştırın
4. **Iteratif İyileştirme**: Audit raporuna göre kodları düzeltin veya yeniden üretin

### Mimari Sınırlamaları

- **Models**: Maksimum 8-10 model önerilir
- **Controllers**: Maksimum 6-8 controller
- **Views**: Maksimum 6-8 view
- **Dosya Başına Satır**: 20-50 satır (öğrenme için ideal)

---

## 📞 Destek

### Hata Raporlama

VS Code kullanıyorsanız:
- **Output Channel**: View → Output → "MVC Orchestrator"
- Terminal çıktısını kontrol edin

CLI kullanıyorsanız:
- Terminal çıktısını inceleyin
- Traceback bilgilerini not edin

### Debug Mode

Daha detaylı log için Python kodunda `print` statement'ları ekleyebilir veya logging modülünü kullanabilirsiniz.

---

## 🔗 Başka Projelerde Kullanım

MVC Test Orchestrator'ı başka bir projede kullanmak için birkaç yöntem vardır:

### Hızlı Başlangıç

#### Yöntem 1: CLI Olarak Kullanım

```bash
# MVC Test Orchestrator'ı klonlayın
git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
cd MVC_Test_Orchestrator_V1.2
./install.sh

# Başka projeden kullanın
python -m src.cli.mvc_arch_cli create-srs --user-idea "Your idea" --output data/srs.txt
```

#### Yöntem 2: Python Modülü Olarak

```python
# MVC Test Orchestrator'ı editable mode'da kurun
pip install -e /path/to/MVC_Test_Orchestrator_V1.2

# Kodunuzda kullanın
from src.agents.srs_writer_agent import SRSWriterAgent
from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient

llm_client = LLMClient()
rag_pipeline = RAGPipeline(llm_client=llm_client)
srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
srs_path = srs_writer.generate_srs("Your project idea")
```

#### Yöntem 3: Git Submodule

```bash
# Ana projenize submodule olarak ekleyin
git submodule add https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git tools/mvc-orchestrator
```

**Detaylı bilgi için**: [USAGE.md](USAGE.md) dosyasına bakın.

---

## 📄 Lisans

Bu proje eğitim amaçlıdır.

---

## 🙏 Teşekkürler

- **Google Gemini API**: LLM desteği için
- **ChromaDB**: Vector database için
- **Sentence Transformers**: Embedding modelleri için

---

**Made for learners, by learners. Keep it simple!** 🎓
