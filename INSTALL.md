# 📦 MVC Test Orchestrator - Kurulum Rehberi

Bu doküman, MVC Test Orchestrator'ı GitHub'dan indirip kurmanız için detaylı adımları içerir.

---

## 🔍 Ön Gereksinimler

- **Python 3.9 veya üzeri**: [Python İndir](https://www.python.org/downloads/)
- **Git**: [Git İndir](https://git-scm.com/downloads)
- **Google Gemini API Key**: [Ücretsiz Al](https://makersuite.google.com/app/apikey)
- **~500MB disk alanı**

---

## 🚀 Hızlı Kurulum (Önerilen)

### Linux/Mac

```bash
# 1. Repository'yi klonlayın
git clone https://github.com/your-username/mvc-test-orchestrator.git
cd mvc-test-orchestrator

# 2. Kurulum scriptini çalıştırın
chmod +x install.sh
./install.sh

# 3. .env dosyasını düzenleyin ve API key'inizi ekleyin
nano .env  # veya başka bir editör kullanın
```

### Windows

```powershell
# 1. Repository'yi klonlayın
git clone https://github.com/your-username/mvc-test-orchestrator.git
cd mvc-test-orchestrator

# 2. Kurulum scriptini çalıştırın
install.bat

# 3. .env dosyasını düzenleyin ve API key'inizi ekleyin
notepad .env
```

---

## 📝 Adım Adım Manuel Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/your-username/mvc-test-orchestrator.git
cd mvc-test-orchestrator
```

### 2. Virtual Environment Oluşturun (Önerilen)

Virtual environment kullanmak, proje bağımlılıklarını sistem Python'unuzdan izole eder.

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Bağımlılıkları Yükleyin

```bash
# pip'i güncelleyin
pip install --upgrade pip

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

Bu işlem birkaç dakika sürebilir (ilk kez embedding modeli indiriliyor).

### 4. API Key'i Yapılandırın

#### 4.1 Google Gemini API Key Alın

1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine gidin
2. Google hesabınızla giriş yapın
3. "Create API Key" butonuna tıklayın
4. API key'inizi kopyalayın

#### 4.2 .env Dosyası Oluşturun

**Linux/Mac:**
```bash
cat > .env << EOF
GOOGLE_API_KEY=your_api_key_here
EOF
```

**Windows:**
```powershell
echo GOOGLE_API_KEY=your_api_key_here > .env
```

Sonra `.env` dosyasını düzenleyip `your_api_key_here` yerine gerçek API key'inizi yapıştırın.

### 5. Veri Klasörünü Oluşturun

```bash
mkdir -p data
```

---

## ✅ Kurulum Doğrulama

Kurulumun başarılı olduğunu kontrol edin:

```bash
python -m src.cli.mvc_arch_cli --help
```

Çıktı şöyle görünmelidir:

```
usage: mvc_arch_cli [-h] {create-srs,extract,scaffold,audit,generate-code,run-fix} ...

CLI for MVC Test Orchestrator (SRS → Architecture → Scaffold)

positional arguments:
  {create-srs,extract,scaffold,audit,generate-code,run-fix}
    create-srs          Creates SRS from user idea (no architecture extraction).
    extract             Extract MVC architecture from SRS. Only runs Architect Agent.
    ...
```

---

## 🧪 İlk Kullanım

Kurulum tamamlandıktan sonra, basit bir test yapın:

```bash
# SRS oluştur
python -m src.cli.mvc_arch_cli create-srs \
    --user-idea "Simple blog with posts and comments" \
    --output data/srs_document.txt
```

Eğer hata alırsanız, [Sorun Giderme](#-sorun-giderme) bölümüne bakın.

---

## 🔧 Gelişmiş Kurulum Seçenekleri

### Python Paketi Olarak Kurulum

Projeyi Python paketi olarak kurabilirsiniz (geliştirme için):

```bash
pip install -e .
```

Bu şekilde kurulum yaparsanız, CLI komutunu şöyle kullanabilirsiniz:

```bash
mvc-orchestrator --help
```

### Development Dependencies ile Kurulum

Geliştirme için ek araçlar:

```bash
pip install -e ".[dev]"
```

Bu, şunları içerir:
- `pytest` - Test framework
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker

---

## 🐛 Sorun Giderme

### Python Bulunamıyor

**Hata:** `python: command not found` veya `python3: command not found`

**Çözüm:**
- Python'un kurulu olduğundan emin olun: `python --version` veya `python3 --version`
- PATH'e eklendiğinden emin olun
- Windows'ta Python kurulumunda "Add Python to PATH" seçeneğini işaretlediğinizden emin olun

### pip Kurulumu Başarısız

**Hata:** `pip install` komutu çalışmıyor

**Çözüm:**
```bash
# pip'i güncelleyin
python -m pip install --upgrade pip

# Tekrar deneyin
pip install -r requirements.txt
```

### ChromaDB Telemetry Hatası

**Hata:** ChromaDB ile ilgili telemetry uyarıları

**Çözüm:**
- Bu normaldir ve proje otomatik olarak telemetry'yi devre dışı bırakır
- Hata devam ederse, `requirements.txt`'teki ChromaDB versiyonunu kontrol edin (0.4.15 önerilir)

### API Key Hatası

**Hata:** `LLMConnectionError` veya API key ile ilgili hatalar

**Çözüm:**
1. `.env` dosyasının proje kök dizininde olduğundan emin olun
2. API key'in doğru formatta olduğundan emin: `GOOGLE_API_KEY=your_actual_key`
3. API key'in geçerli olduğundan emin (Google AI Studio'dan kontrol edin)
4. İnternet bağlantınızı kontrol edin

### Virtual Environment Aktif Değil

**Hata:** Bağımlılıklar bulunamıyor

**Çözüm:**
```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Virtual environment aktif olduğunda, terminal prompt'unuzda `(.venv)` görünmelidir.

---

## 🔄 Güncelleme

Projeyi güncellemek için:

```bash
# Değişiklikleri çekin
git pull origin main

# Yeni bağımlılıkları yükleyin
pip install -r requirements.txt --upgrade
```

---

## 🗑️ Kaldırma

Projeyi kaldırmak için:

```bash
# Virtual environment'ı deaktif edin
deactivate

# Klasörü silin
cd ..
rm -rf mvc-test-orchestrator  # Linux/Mac
# veya
rmdir /s mvc-test-orchestrator  # Windows
```

---

## 📚 Sonraki Adımlar

Kurulum tamamlandıktan sonra:

1. [README.md](README.md) dosyasını okuyun
2. [FLOWCHART.md](FLOWCHART.md) ile sistem akışını anlayın
3. İlk projenizi oluşturun

**Örnek Kullanım:**

```bash
# 1. SRS oluştur
python -m src.cli.mvc_arch_cli create-srs \
    --user-idea "Task manager for students" \
    --output data/srs_document.txt

# 2. Mimari çıkar
python -m src.cli.mvc_arch_cli extract \
    --srs-path data/srs_document.txt \
    --output data/architecture_map.json

# 3. Scaffold oluştur
python -m src.cli.mvc_arch_cli scaffold \
    --arch-path data/architecture_map.json

# 4. Kod üret
python -m src.cli.mvc_arch_cli generate-code \
    --category model \
    --arch-path data/architecture_map.json
```

---

## 💡 İpuçları

- **Virtual Environment Kullanın**: Her zaman virtual environment kullanın, sistem Python'unuzu kirletmeyin
- **API Key Güvenliği**: `.env` dosyasını asla Git'e commit etmeyin (zaten .gitignore'da)
- **Disk Alanı**: İlk kurulumda embedding modeli indirileceği için yeterli disk alanı olduğundan emin olun (~500MB)
- **İnternet Bağlantısı**: İlk kullanımda model indirme için internet bağlantısı gerekir

---

## 🆘 Yardım

Sorun yaşıyorsanız:

1. [README.md](README.md) dosyasındaki "Sorun Giderme" bölümüne bakın
2. GitHub Issues'da benzer sorunları arayın
3. Yeni bir issue oluşturun

---

**Başarılar! 🎉**

