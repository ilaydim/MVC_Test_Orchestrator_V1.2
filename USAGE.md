# 📖 MVC Test Orchestrator - Başka Projelerde Kullanım Rehberi

Bu doküman, MVC Test Orchestrator'ı başka bir projede nasıl kullanacağınızı açıklar.

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: CLI Olarak Kullanım (En Basit)

Diğer projeden CLI komutlarını çalıştırmak.

### Senaryo 2: Python Modülü Olarak Kullanım

Kendi Python kodunuzda agent'ları import edip kullanmak.

### Senaryo 3: Git Submodule Olarak Ekleme

Projenize submodule olarak eklemek.

---

## 🚀 Senaryo 1: CLI Olarak Kullanım

### Kurulum

#### Yöntem A: Git Clone (Geliştirme İçin)

```bash
# Ana projenizin yanına MVC Test Orchestrator'ı klonlayın
cd /path/to/your/workspace
git clone https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git
cd mvc-test-orchestrator

# Kurulum yapın
./install.sh  # veya install.bat (Windows)

# .env dosyasını yapılandırın
echo "GOOGLE_API_KEY=your_api_key" > .env
```

#### Yöntem B: Python Paketi Olarak Kurulum (Editable)

```bash
# MVC Test Orchestrator'ı klonlayın
git clone https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git
cd mvc-test-orchestrator

# Editable mode'da kurun (değişiklikler otomatik yansır)
pip install -e .
```

### Kullanım

#### Başka Bir Projeden CLI Komutlarını Çalıştırma

```python
# your_project/generate_mvc.py
import subprocess
from pathlib import Path

# MVC Test Orchestrator'ın yolunu belirtin
mvc_orchestrator_path = Path("/path/to/mvc-test-orchestrator")

# SRS oluştur
subprocess.run([
    "python", "-m", "src.cli.mvc_arch_cli",
    "create-srs",
    "--user-idea", "Task manager for students",
    "--output", str(mvc_orchestrator_path / "data" / "srs_document.txt")
], cwd=mvc_orchestrator_path)

# Mimari çıkar
subprocess.run([
    "python", "-m", "src.cli.mvc_arch_cli",
    "extract",
    "--srs-path", str(mvc_orchestrator_path / "data" / "srs_document.txt"),
    "--output", str(mvc_orchestrator_path / "data" / "architecture_map.json")
], cwd=mvc_orchestrator_path)
```

#### Shell Script ile Kullanım

```bash
#!/bin/bash
# your_project/generate_architecture.sh

MVC_ORCHESTRATOR="/path/to/mvc-test-orchestrator"
YOUR_PROJECT="/path/to/your/project"

cd "$MVC_ORCHESTRATOR"

# SRS oluştur
python -m src.cli.mvc_arch_cli create-srs \
    --user-idea "Your project idea" \
    --output data/srs_document.txt

# Mimari çıkar
python -m src.cli.mvc_arch_cli extract \
    --srs-path data/srs_document.txt \
    --output data/architecture_map.json

# Scaffold oluştur
python -m src.cli.mvc_arch_cli scaffold \
    --arch-path data/architecture_map.json

# Sonuçları kendi projenize kopyala
cp data/architecture_map.json "$YOUR_PROJECT/architecture.json"
cp -r scaffolds/mvc_skeleton/* "$YOUR_PROJECT/src/"
```

---

## 🐍 Senaryo 2: Python Modülü Olarak Kullanım

### Kurulum

```bash
# MVC Test Orchestrator'ı klonlayıp editable mode'da kurun
git clone https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git
cd mvc-test-orchestrator
pip install -e .

# Veya direkt path ile kullanabilirsiniz (PYTHONPATH ekleyerek)
export PYTHONPATH="/path/to/mvc-test-orchestrator:$PYTHONPATH"
```

### Örnek 1: SRS Oluşturma

```python
# your_project/mvc_generator.py
import os
from pathlib import Path

# Environment variable ayarla
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"

from src.agents.srs_writer_agent import SRSWriterAgent
from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient

# Initialize
llm_client = LLMClient()
rag_pipeline = RAGPipeline(llm_client=llm_client)
srs_writer = SRSWriterAgent(rag_pipeline, llm_client)

# SRS oluştur
user_idea = "Simple blog with posts and comments"
srs_path = srs_writer.generate_srs(user_idea)
print(f"SRS created at: {srs_path}")
```

### Örnek 2: Mimari Çıkarma

```python
# your_project/extract_architecture.py
import os
from pathlib import Path
import json

os.environ["GOOGLE_API_KEY"] = "your_api_key_here"

from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient
from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.core.config import DEFAULT_TOP_K

# Initialize
llm_client = LLMClient()
rag_pipeline = RAGPipeline(llm_client=llm_client)

# SRS'yi indexle
srs_path = Path("data/srs_document.txt")
rag_pipeline.index_srs(srs_path)

# Agents
requirements_agent = RequirementsAgent(rag_pipeline, llm_client)
model_agent = ModelArchitectAgent(rag_pipeline, llm_client)
controller_agent = ControllerArchitectAgent(rag_pipeline, llm_client)
view_agent = ViewArchitectAgent(rag_pipeline, llm_client)

# Extract
requirements = requirements_agent.extract_analysis(k=DEFAULT_TOP_K)
models = model_agent.extract_models(k=DEFAULT_TOP_K)
controllers = controller_agent.extract_controllers(k=DEFAULT_TOP_K)
views = view_agent.extract_views(k=DEFAULT_TOP_K)

# Combine
architecture = {
    "model": models.get("model", []),
    "controller": controllers.get("controller", []),
    "view": views.get("view", [])
}

# Save
output_path = Path("your_project/architecture.json")
with open(output_path, "w") as f:
    json.dump(architecture, f, indent=2)

print(f"Architecture saved to: {output_path}")
```

### Örnek 3: Scaffold Oluşturma

```python
# your_project/create_scaffold.py
import json
from pathlib import Path

from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder

# Architecture'ı yükle
with open("architecture.json", "r") as f:
    architecture = json.load(f)

# Scaffolder oluştur (custom output path ile)
project_root = Path("/path/to/your/project")
scaffold_root = project_root / "src" / "mvc"

scaffolder = MVCScaffolder(
    project_root=project_root,
    scaffold_root=scaffold_root
)

# Scaffold oluştur
result = scaffolder.scaffold_all(architecture)

print(f"Created {len(result['models'])} models")
print(f"Created {len(result['views'])} views")
print(f"Created {len(result['controllers'])} controllers")
```

### Örnek 4: Tam Pipeline

```python
# your_project/full_pipeline.py
"""
MVC Test Orchestrator'ı kullanarak tam pipeline çalıştırma
"""
import os
from pathlib import Path
import json

# Configuration
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient
from src.agents.srs_writer_agent import SRSWriterAgent
from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder
from src.core.config import DEFAULT_TOP_K


def run_full_pipeline(user_idea: str, output_dir: Path):
    """Tam MVC pipeline'ı çalıştırır"""
    
    # Initialize
    llm_client = LLMClient()
    rag_pipeline = RAGPipeline(llm_client=llm_client)
    
    # 1. SRS Oluştur
    print("Step 1: Creating SRS...")
    srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
    srs_path = srs_writer.generate_srs(user_idea)
    print(f"✅ SRS created: {srs_path}")
    
    # 2. Index SRS
    print("\nStep 2: Indexing SRS...")
    rag_pipeline.index_srs(srs_path)
    print("✅ SRS indexed")
    
    # 3. Extract Architecture
    print("\nStep 3: Extracting architecture...")
    requirements_agent = RequirementsAgent(rag_pipeline, llm_client)
    model_agent = ModelArchitectAgent(rag_pipeline, llm_client)
    controller_agent = ControllerArchitectAgent(rag_pipeline, llm_client)
    view_agent = ViewArchitectAgent(rag_pipeline, llm_client)
    
    requirements = requirements_agent.extract_analysis(k=DEFAULT_TOP_K)
    models = model_agent.extract_models(k=DEFAULT_TOP_K)
    controllers = controller_agent.extract_controllers(k=DEFAULT_TOP_K)
    views = view_agent.extract_views(k=DEFAULT_TOP_K)
    
    architecture = {
        "model": models.get("model", []),
        "controller": controllers.get("controller", []),
        "view": views.get("view", [])
    }
    
    # Save architecture
    arch_path = output_dir / "architecture.json"
    with open(arch_path, "w") as f:
        json.dump(architecture, f, indent=2)
    print(f"✅ Architecture saved: {arch_path}")
    
    # 4. Create Scaffold
    print("\nStep 4: Creating scaffold...")
    scaffolder = MVCScaffolder(
        project_root=output_dir,
        scaffold_root=output_dir / "scaffolds"
    )
    result = scaffolder.scaffold_all(architecture)
    print(f"✅ Scaffold created: {len(result['models'])} models, "
          f"{len(result['views'])} views, {len(result['controllers'])} controllers")
    
    return {
        "srs_path": srs_path,
        "architecture_path": arch_path,
        "scaffold_result": result
    }


if __name__ == "__main__":
    result = run_full_pipeline(
        user_idea="Task manager for students with categories",
        output_dir=OUTPUT_DIR
    )
    print("\n🎉 Pipeline completed!")
    print(f"Results in: {OUTPUT_DIR}")
```

---

## 🔗 Senaryo 3: Git Submodule Olarak Ekleme

### Submodule Ekleme

```bash
# Ana projenize gidin
cd /path/to/your/project

# MVC Test Orchestrator'ı submodule olarak ekleyin
git submodule add https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git tools/mvc-orchestrator

# Submodule'ü initialize edin
git submodule update --init --recursive
```

### Kullanım (Submodule ile)

```python
# your_project/config.py
from pathlib import Path

# Submodule path'ini bul
PROJECT_ROOT = Path(__file__).parent
MVC_ORCHESTRATOR_PATH = PROJECT_ROOT / "tools" / "mvc-orchestrator"

# PYTHONPATH'e ekle
import sys
sys.path.insert(0, str(MVC_ORCHESTRATOR_PATH))

# Artık import edebilirsiniz
from src.agents.srs_writer_agent import SRSWriterAgent
# ...
```

### Submodule Güncelleme

```bash
# Submodule'ü güncelle
cd tools/mvc-orchestrator
git pull origin main

# Ana projeye dön
cd ../..
git add tools/mvc-orchestrator
git commit -m "Update mvc-orchestrator submodule"
```

---

## ⚙️ Yapılandırma

### Environment Variables

```bash
# .env dosyası oluşturun
echo "GOOGLE_API_KEY=your_api_key" > .env
```

Veya Python kodunda:

```python
import os
os.environ["GOOGLE_API_KEY"] = "your_api_key"
```

### Custom Paths

Agent'lar varsayılan olarak kendi `data/` klasörünü kullanır. Farklı path kullanmak için:

```python
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from pathlib import Path

class CustomAgent(BaseArchitectAgent):
    def __init__(self, custom_data_dir: Path):
        super().__init__()
        self.data_dir = custom_data_dir
        self.data_dir.mkdir(exist_ok=True)
```

---

## 📦 Paket Bağımlılığı Olarak Ekleme

### requirements.txt'te Belirtme

```txt
# Local package (editable)
-e /path/to/mvc-test-orchestrator

# Veya git repository'den
git+https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git@main
```

### setup.py / pyproject.toml'de Belirtme

```python
# setup.py
setup(
    install_requires=[
        # ... diğer bağımlılıklar
        "mvc-test-orchestrator @ file:///path/to/mvc-test-orchestrator",
    ]
)
```

veya

```toml
# pyproject.toml
[project]
dependencies = [
    "mvc-test-orchestrator @ git+https://github.com/YOUR_USERNAME/mvc-test-orchestrator.git",
]
```

---

## 🎯 En İyi Pratikler

### 1. API Key Yönetimi

```python
# Güvenli API key yönetimi
import os
from pathlib import Path

def get_api_key():
    """API key'i güvenli şekilde al"""
    # Önce environment variable'dan dene
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    
    # Sonra .env dosyasından oku
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return os.getenv("GOOGLE_API_KEY")
    
    raise ValueError("GOOGLE_API_KEY not found in environment or .env file")
```

### 2. Error Handling

```python
from src.core.llm_client import QuotaExceededError, LLMConnectionError

try:
    # MVC operations
    pass
except QuotaExceededError as e:
    print(f"API quota exceeded: {e}")
    # Fallback logic
except LLMConnectionError as e:
    print(f"Connection error: {e}")
    # Retry logic
```

### 3. Output Path Yönetimi

```python
from pathlib import Path

class ProjectConfig:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.output_dir = project_root / "generated"
        self.output_dir.mkdir(exist_ok=True)
        
        # MVC Test Orchestrator çıktılarını buraya yönlendir
        self.mvc_data_dir = self.output_dir / "mvc_data"
        self.mvc_data_dir.mkdir(exist_ok=True)
```

---

## 🐛 Sorun Giderme

### Import Hatası

**Hata**: `ModuleNotFoundError: No module named 'src'`

**Çözüm**:
```python
import sys
from pathlib import Path

mvc_path = Path("/path/to/mvc-test-orchestrator")
sys.path.insert(0, str(mvc_path))
```

### Path Problemi

**Hata**: Agent'lar yanlış path'te dosya arıyor

**Çözüm**: Agent'ları initialize ederken custom path kullanın:

```python
from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from pathlib import Path

# Custom data directory
custom_data_dir = Path("/your/custom/path/data")
```

---

## 📚 Örnekler

Tam çalışan örnekler için:
- `examples/` klasörüne bakın (oluşturulacak)
- GitHub repository'deki example projeleri inceleyin

---

## 💡 İpuçları

1. **Development Mode**: Geliştirme sırasında `pip install -e .` kullanın
2. **Production Mode**: Production'da specific version kullanın
3. **Caching**: RAG pipeline'ı cache'leyin (aynı SRS için)
4. **Error Handling**: Her zaman try-except kullanın
5. **Logging**: İşlemleri loglayın

---

**Başarılar! 🚀**

