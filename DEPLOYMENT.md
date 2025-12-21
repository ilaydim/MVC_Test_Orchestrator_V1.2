# 🚀 GitHub'a Yükleme ve Dağıtım Rehberi

Bu doküman, MVC Test Orchestrator projesini GitHub'a yükleyip kullanıcıların kullanması için gerekli adımları içerir.

---

## 📦 Hazırlık

### 1. Repository Hazırlığı

Projenizi GitHub'da yayınlamadan önce:

1. **Git Repository Kontrolü**
   ```bash
   git status
   git log
   ```

2. **.gitignore Kontrolü**
   - `.env` dosyası ignore edilmeli ✅
   - `__pycache__/` ignore edilmeli ✅
   - `data/` klasörü ignore edilmeli ✅
   - `generated_src/` ignore edilmeli ✅
   - `scaffolds/` ignore edilmeli ✅

3. **Gerekli Dosyaların Varlığı**
   - ✅ `README.md` - Ana dokümantasyon
   - ✅ `INSTALL.md` - Kurulum rehberi
   - ✅ `LICENSE` - Lisans dosyası
   - ✅ `requirements.txt` - Python bağımlılıkları
   - ✅ `pyproject.toml` - Python paket yapılandırması
   - ✅ `install.sh` - Linux/Mac kurulum scripti
   - ✅ `install.bat` - Windows kurulum scripti
   - ✅ `env.example` - Örnek environment dosyası
   - ✅ `CONTRIBUTING.md` - Katkı rehberi
   - ✅ `.github/pull_request_template.md` - PR template

---

## 🌐 GitHub'da Repository Oluşturma

### Adım 1: GitHub'da Yeni Repository Oluştur

1. [GitHub](https://github.com) hesabınıza giriş yapın
2. "New repository" butonuna tıklayın
3. Repository bilgilerini doldurun:
   - **Repository name**: `mvc-test-orchestrator` (veya tercih ettiğiniz isim)
   - **Description**: "AI-powered MVC architecture extraction and code generation system"
   - **Visibility**: Public (veya Private)
   - **Initialize**: README, .gitignore, license eklemeyin (zaten var)
4. "Create repository" butonuna tıklayın

### Adım 2: Local Repository'yi GitHub'a Bağla

```bash
# Mevcut Git repository'nizi kontrol edin
git remote -v

# Eğer remote yoksa, GitHub repository URL'inizi ekleyin
git remote add origin https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git

# Veya SSH kullanıyorsanız:
# git remote add origin git@github.com:ilaydim/MVC_Test_Orchestrator_V1.2.git  # SSH için

# Remote'u kontrol edin
git remote -v
```

### Adım 3: Değişiklikleri Commit ve Push Et

```bash
# Tüm dosyaları staging area'ya ekle
git add .

# Commit et
git commit -m "Initial commit: MVC Test Orchestrator v1.2"

# Main branch'e push et
git branch -M main
git push -u origin main
```

---

## 📝 README.md'yi Güncelle

README.md dosyasındaki placeholder'ları güncelleyin:

1. **Repository URL'ini Güncelle**
   - Repository URL: `https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git`

2. **Kurulum Bölümündeki Komutları Güncelle**
   - Git clone komutlarındaki URL'i güncelleyin

---

## 🏷️ Release Oluşturma (Opsiyonel)

İlk release'i oluşturmak için:

1. GitHub repository sayfasında "Releases" → "Create a new release"
2. Tag version: `v1.2.0`
3. Release title: `MVC Test Orchestrator v1.2.0`
4. Description:
   ```markdown
   ## Initial Release

   ### Features
   - SRS creation from user ideas
   - RAG-based architecture extraction
   - MVC code generation
   - Quality audit and auto-fix

   ### Installation
   See [INSTALL.md](INSTALL.md) for detailed installation instructions.

   ### Quick Start
   ```bash
   git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
   cd MVC_Test_Orchestrator_V1.2
   ./install.sh  # Linux/Mac
   # veya
   install.bat   # Windows
   ```
   ```
5. "Publish release" butonuna tıklayın

---

## 📦 PyPI'ye Yükleme (Opsiyonel - İleri Seviye)

Python paketi olarak yayınlamak isterseniz:

### 1. Build Araçlarını Yükleyin

```bash
pip install build twine
```

### 2. Paketi Build Edin

```bash
python -m build
```

Bu komut `dist/` klasöründe `.whl` ve `.tar.gz` dosyaları oluşturur.

### 3. PyPI Test Server'da Test Edin

```bash
# Test PyPI'ye yükle
twine upload --repository testpypi dist/*

# Test edin
pip install --index-url https://test.pypi.org/simple/ mvc-test-orchestrator
```

### 4. Gerçek PyPI'ye Yükle

```bash
# PyPI credentials gerekli (https://pypi.org/manage/account/)
twine upload dist/*
```

### 5. Kullanım

Artık kullanıcılar şöyle kurabilir:

```bash
pip install mvc-test-orchestrator
```

**Not**: PyPI'ye yüklemeden önce `pyproject.toml` dosyasındaki metadata'yı kontrol edin.

---

## 🎯 VS Code Extension Yayınlama (Opsiyonel)

VS Code Extension'ı marketplace'e yayınlamak için:

### 1. VSIX Paketi Oluştur

```bash
cd mvc-test-orchestrator
npm install
npm run compile
npm install -g @vscode/vsce
vsce package
```

Bu komut `.vsix` dosyası oluşturur.

### 2. Marketplace'e Yükle

1. [VS Code Marketplace Publisher](https://marketplace.visualstudio.com/manage) sayfasına gidin
2. "Create new publisher" ile publisher hesabı oluşturun
3. "New extension" → "Visual Studio Code" seçin
4. `.vsix` dosyasını yükleyin

### 3. Kullanım

Kullanıcılar VS Code'da Extension sekmesinden "MVC Test Orchestrator" arayıp kurabilir.

---

## ✅ Dağıtım Öncesi Kontrol Listesi

### Dokümantasyon
- [ ] README.md güncel ve tam
- [ ] INSTALL.md hazır
- [ ] CONTRIBUTING.md hazır
- [ ] LICENSE dosyası eklendi
- [ ] GitHub repository URL'leri güncel

### Kod
- [ ] `.gitignore` doğru yapılandırılmış
- [ ] Gereksiz dosyalar commit edilmemiş (`.env`, `__pycache__`, vb.)
- [ ] Testler çalışıyor (varsa)
- [ ] Kod standartlarına uygun

### Konfigürasyon
- [ ] `requirements.txt` güncel
- [ ] `pyproject.toml` metadata doğru
- [ ] `env.example` dosyası mevcut
- [ ] Kurulum scriptleri (`install.sh`, `install.bat`) çalışıyor

### GitHub
- [ ] Repository oluşturuldu
- [ ] README.md görünür
- [ ] Description ve topics eklendi
- [ ] License seçildi
- [ ] İlk commit ve push yapıldı

---

## 🎉 Yayınlama Sonrası

1. **Repository Ayarları**
   - About bölümüne açıklama ekleyin
   - Topics ekleyin: `python`, `mvc`, `ai`, `llm`, `rag`, `code-generation`
   - Website URL ekleyin (varsa)
   - Social preview image ekleyin (opsiyonel)

2. **Community Standards**
   - Code of Conduct ekleyin (opsiyonel)
   - Security policy ekleyin (opsiyonel)

3. **Dökümantasyon**
   - Wiki'yi aktifleştirin (opsiyonel)
   - Discussions'ı aktifleştirin (opsiyonel)

4. **İletişim**
   - Issues'ı aktif tutun
   - Pull Request'lere yanıt verin
   - Kullanıcı sorularını yanıtlayın

---

## 📊 Kullanım İstatistikleri

GitHub Insights'tan şunları takip edebilirsiniz:
- Repository trafiği
- Clone sayıları
- Issue ve PR istatistikleri
- Contributor grafikleri

---

## 🔄 Güncelleme ve Bakım

### Yeni Versiyon Yayınlama

1. Version numarasını güncelleyin:
   - `pyproject.toml`: `version = "1.2.1"`
   - `README.md`: Başlıktaki versiyon
   - `mvc-test-orchestrator/package.json`: `"version": "0.0.2"`

2. CHANGELOG.md oluşturun/güncelleyin (opsiyonel)

3. Commit ve push edin:
   ```bash
   git add .
   git commit -m "chore: bump version to 1.2.1"
   git push
   ```

4. Yeni release oluşturun (GitHub Releases)

---

## 🆘 Sorun Giderme

### Push Hatası: "Permission denied"

**Çözüm:**
- SSH key'lerinizi kontrol edin
- HTTPS kullanıyorsanız, Personal Access Token kullanın
- Repository'ye erişim izniniz olduğundan emin olun

### Large File Hatası

**Çözüm:**
- `.gitignore`'a büyük dosyaları ekleyin
- Git LFS kullanın (çok büyük dosyalar için)
- Gereksiz dosyaları commit etmeyin

---

## 📚 Ek Kaynaklar

- [GitHub Documentation](https://docs.github.com/)
- [PyPI Packaging Guide](https://packaging.python.org/)
- [VS Code Extension Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)

---

**Başarılar! 🚀**

