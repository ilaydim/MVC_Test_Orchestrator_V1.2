# 🤝 Katkıda Bulunma Rehberi

MVC Test Orchestrator projesine katkıda bulunmak istediğiniz için teşekkürler! 

## 🚀 Başlangıç

1. Repository'yi fork edin
2. Local'de clone edin:
   ```bash
   git clone https://github.com/ilaydim/MVC_Test_Orchestrator_V1.2.git
   cd MVC_Test_Orchestrator_V1.2
   ```
3. Development branch oluşturun:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Geliştirme Ortamı Kurulumu

1. Virtual environment oluşturun:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # veya
   .venv\Scripts\activate  # Windows
   ```

2. Development dependencies ile kurulum yapın:
   ```bash
   pip install -e ".[dev]"
   ```

3. `.env` dosyası oluşturun (`env.example` dosyasını referans alın)

## ✅ Kod Standartları

- **Python Style**: PEP 8 uyumlu kod yazın
- **Type Hints**: Mümkün olduğunca type hints kullanın
- **Docstrings**: Tüm public fonksiyonlar ve sınıflar için docstring ekleyin
- **Formatting**: `black` kullanın (line length: 100)

### Code Formatting

```bash
# Kod formatlama
black src/

# Linting
flake8 src/

# Type checking
mypy src/
```

## 🧪 Testler

Test yazarken:

1. `src/tests/` klasörüne test dosyası ekleyin
2. Test dosyası adı `test_*.py` formatında olmalı
3. Test çalıştırma:
   ```bash
   pytest src/tests/
   ```

## 📤 Pull Request Gönderme

1. Değişikliklerinizi commit edin:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

2. Branch'inizi push edin:
   ```bash
   git push origin feature/your-feature-name
   ```

3. GitHub'da Pull Request oluşturun

### Commit Mesajları

Commit mesajları için [Conventional Commits](https://www.conventionalcommits.org/) formatını kullanın:

- `feat:` Yeni özellik
- `fix:` Hata düzeltmesi
- `docs:` Dokümantasyon değişiklikleri
- `style:` Kod formatı (işlevsellik değişikliği yok)
- `refactor:` Kod refactoring
- `test:` Test ekleme/düzenleme
- `chore:` Build process veya yardımcı araçlar

Örnek:
```
feat: add support for custom embedding models
fix: resolve ChromaDB connection issue
docs: update installation instructions
```

## 🐛 Bug Raporlama

Bug bulduysanız:

1. GitHub Issues'da yeni bir issue oluşturun
2. Şu bilgileri ekleyin:
   - Sorunun açıklaması
   - Beklenen davranış
   - Gerçekleşen davranış
   - Adımlar (reproduction steps)
   - Python versiyonu
   - İşletim sistemi

## 💡 Özellik İstekleri

Yeni özellik önermek için:

1. GitHub Issues'da "Feature Request" etiketi ile issue oluşturun
2. Özelliğin amacını ve kullanım senaryosunu açıklayın

## 📚 Dokümantasyon

- Dokümantasyon güncellemeleri hoş karşılanır
- README.md, INSTALL.md ve diğer .md dosyalarını güncelleyebilirsiniz
- Kod içi docstring'leri güncel tutun

## ❓ Sorular

Sorularınız için GitHub Discussions kullanabilirsiniz.

---

**Teşekkürler! 🎉**

