# 📋 MVC Test Orchestrator - Prompt Library

Bu klasör, MVC Test Orchestrator projesindeki tüm LLM prompt'larını içerir. Prompt'lar Python kodundan ayrılarak daha kolay yönetim ve güncelleme sağlar.

## 🎯 Avantajlar

### ✅ Kolay Güncelleme
- Prompt'ları güncellemek için Python kodunu düzenlemenize gerek yok
- Markdown dosyalarını düzenleyin, değişiklik hemen etkili olur

### ✅ Version Control
- Prompt değişiklikleri git'te net görünür
- Prompt history'si takip edilebilir
- Team collaboration kolaylaşır

### ✅ Hoca Standardı: Clarification Phase
- Her prompt'ta "Clarification Phase" var
- LLM eksik bilgi varsa kullanıcıya soru sorar
- Daha kaliteli çıktı üretilir

### ✅ Şablon Yapısı
- `{{variable}}` formatında değişkenler
- Python'da `.replace()` ile kolayca enjekte edilir
- Okunabilirlik artar

## 📂 Prompt Dosyaları

### 1. SRS Generation
**Dosya**: `create_srs.prompt.md`  
**Kullanıldığı Yer**: `src/agents/srs_writer_agent.py`  
**Amaç**: Kullanıcı fikrinden detaylı SRS dokümanı oluşturur

**Değişkenler**:
- `{{user_idea}}`: Kullanıcının proje fikri

### 2. Requirements Analysis
**Dosya**: `extract_requirements.prompt.md`  
**Kullanıldığı Yer**: `src/agents/architect_agent/requirements_agent.py`  
**Amaç**: SRS'den domain entities ve system functions çıkarır

**Değişkenler**:
- `{{context}}`: RAG'den gelen SRS chunk'ları

### 3. Model Architecture Extraction
**Dosya**: `extract_model_architecture.prompt.md`  
**Kullanıldığı Yer**: `src/agents/architect_agent/model_architect_agent.py`  
**Amaç**: Domain model'leri belirler

**Değişkenler**:
- `{{context}}`: RAG'den gelen SRS chunk'ları

### 4. View Architecture Extraction
**Dosya**: `extract_view_architecture.prompt.md`  
**Kullanıldığı Yer**: `src/agents/architect_agent/view_architect_agent.py`  
**Amaç**: UI ekranlarını/sayfalarını belirler

**Değişkenler**:
- `{{context}}`: RAG'den gelen SRS chunk'ları

### 5. Controller Architecture Extraction
**Dosya**: `extract_controller_architecture.prompt.md`  
**Kullanıldığı Yer**: `src/agents/architect_agent/controller_architect_agent.py`  
**Amaç**: Controller'ları ve action'ları belirler

**Değişkenler**:
- `{{context}}`: RAG'den gelen SRS chunk'ları

### 6. Model Code Generation
**Dosya**: `generate_model_code.prompt.md`  
**Kullanıldığı Yer**: `src/agents/coder_agent.py`  
**Amaç**: Model skeleton'ını tamamlar

**Değişkenler**:
- `{{class_name}}`: Model sınıf adı
- `{{skeleton}}`: Boş skeleton kodu
- `{{arch_info}}`: Architecture bilgisi
- `{{srs_context}}`: İlgili SRS içeriği

### 7. View Code Generation
**Dosya**: `generate_view_code.prompt.md`  
**Kullanıldığı Yer**: `src/agents/coder_agent.py`  
**Amaç**: View skeleton'ını tamamlar

**Değişkenler**:
- `{{class_name}}`: View sınıf adı
- `{{skeleton}}`: Boş skeleton kodu
- `{{arch_info}}`: Architecture bilgisi
- `{{srs_context}}`: İlgili SRS içeriği

### 8. Controller Code Generation
**Dosya**: `generate_controller_code.prompt.md`  
**Kullanıldığı Yer**: `src/agents/coder_agent.py`  
**Amaç**: Controller skeleton'ını tamamlar

**Değişkenler**:
- `{{class_name}}`: Controller sınıf adı
- `{{skeleton}}`: Boş skeleton kodu
- `{{arch_info}}`: Architecture bilgisi
- `{{srs_context}}`: İlgili SRS içeriği
- `{{related_models}}`: İlişkili model'ler (JSON)
- `{{related_views}}`: İlişkili view'lar (JSON)

## 🔧 Nasıl Çalışır?

### Agent Tarafında (Python)

```python
from pathlib import Path

# 1. Prompt dosyasını oku
prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "create_srs.prompt.md"
prompt_template = prompt_path.read_text(encoding="utf-8")

# 2. Değişkenleri değiştir
prompt = prompt_template.replace("{{user_idea}}", user_idea)

# 3. LLM'e gönder
response = llm.generate_content(prompt)
```

### Prompt Dosyasında (Markdown)

```markdown
# SRS Creation Prompt

## Role
You are an expert Software Requirements Analyst.

## Clarification Phase
Before generating, if any information is unclear, ask:
- Target Platform?
- User Roles?
- Core Features?

## Variables
- `{{user_idea}}`: The user's project idea

## Output
Generate detailed SRS...
```

## 📝 Prompt Güncelleme

### Adım 1: Markdown Dosyasını Düzenle

```bash
# Prompt dosyasını aç
code .github/prompts/create_srs.prompt.md

# İstediğiniz değişikliği yapın
```

### Adım 2: Test Et

```bash
# Agent'ı çalıştır
python -m src.cli.mvc_arch_cli create-srs --user-idea "Test project"
```

### Adım 3: Commit Et

```bash
git add .github/prompts/create_srs.prompt.md
git commit -m "Update SRS creation prompt: Add more detailed data model section"
```

## 🎓 Best Practices

### 1. Clarification Phase Kullan

Her prompt'ta kullanıcıya soru sorma fırsatı ver:

```markdown
## Clarification Phase
If the following are unclear:
- [Liste kritik bilgiler]

Ask clarifying questions. Otherwise proceed.
```

### 2. Değişken Formatı

Tutarlı değişken formatı kullan:

```markdown
Good: {{user_idea}}, {{context}}, {{class_name}}
Bad: {user_idea}, $context, %class_name%
```

### 3. Örnek Ekle

Prompt'a örnek output ekle:

```markdown
## Output Example
\`\`\`json
{
  "model": [
    {"name": "User", "description": "System user"}
  ]
}
\`\`\`
```

### 4. Kısıtlamaları Net Belirt

```markdown
## Very Important Rules
- DO NOT include X
- DO NOT infer Y
- KEEP THE OUTPUT MINIMAL
```

## 🐛 Troubleshooting

### Problem: Prompt dosyası bulunamıyor

**Hata**: `FileNotFoundError: .github/prompts/create_srs.prompt.md`

**Çözüm**:
```bash
# Dosya path'ini kontrol et
ls -la .github/prompts/

# Eğer yoksa, git pull
git pull origin main
```

### Problem: Değişken replace edilmiyor

**Hata**: LLM çıktısında `{{user_idea}}` görünüyor

**Çözüm**:
```python
# Replace'i kontrol et
prompt = prompt_template.replace("{{user_idea}}", user_idea)
print(prompt)  # Debug: Değişken yerini aldı mı?
```

### Problem: Encoding hatası

**Hata**: `UnicodeDecodeError`

**Çözüm**:
```python
# UTF-8 encoding ekle
prompt_template = prompt_path.read_text(encoding="utf-8")
```

## 🔄 Migration (Eski Koddan Yeni Sisteme)

Eğer hala eski sistemi (prompt'lar kod içinde) kullanıyorsanız:

### Adım 1: Prompt'u Çıkar

```python
# ESKİ (kod içinde)
prompt = f"""
You are an expert...
User Idea: {user_idea}
"""

# YENİ (dosyadan oku)
prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "my_prompt.prompt.md"
prompt_template = prompt_path.read_text(encoding="utf-8")
prompt = prompt_template.replace("{{user_idea}}", user_idea)
```

### Adım 2: Markdown Dosyası Oluştur

```markdown
# my_prompt.prompt.md

## Role
You are an expert...

## Variables
- `{{user_idea}}`: User's idea

## Task
Generate output based on {{user_idea}}...
```

### Adım 3: Test Et

```bash
# Eski ve yeni çıktıyı karşılaştır
python test_prompt_migration.py
```

## 📚 Daha Fazla Bilgi

- **Ana Proje**: [../../README.md](../../README.md)
- **Agent Dokümantasyonu**: [../../src/agents/README.md](../../src/agents/README.md)
- **CLI Kullanımı**: [../../src/cli/README.md](../../src/cli/README.md)

---

**Son Güncelleme**: 2024-12-17  
**Versiyon**: 2.0  
**Durum**: ✅ Production Ready

