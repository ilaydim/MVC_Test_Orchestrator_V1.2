# 🧠 MVC Architect Orchestrator

**Otomatik MVC Mimari Çıkarımı ve İskelet Oluşturma (Scaffolding)**  
Çoklu-agent’lı, LLM destekli yazılım mühendisliği sistemi.

---

## 🚀 Genel Bakış (Overview)

**MVC Architect Orchestrator**, bir yazılım fikrini veya mevcut bir **Yazılım Gereksinimleri Şartnamesini (SRS)** analiz ederek **Model–View–Controller (MVC)** mimarisinin tüm katmanlarını otomatik olarak çıkaran ve bu mimariye dayalı bir **proje iskeleti (scaffold)** oluşturan gelişmiş bir pipeline’dır.

Sistem; **LLM**, **RAG (Retrieval-Augmented Generation)** ve **çoklu agent mimarisi** kullanarak gereksinimlerden doğrudan yazılım mimarisi üretmeyi hedefler.

---

## 🧩 Pipeline Aşamaları

1. **Gereksinim Girişi**
   - Kullanıcı fikrinden otomatik SRS oluşturma  
   - Veya mevcut `.txt` / `.pdf` SRS dosyasını yükleme

2. **RAG Indexleme**
   - Gereksinim dokümanlarının RAG sistemi için parçalanması ve indekslenmesi

3. **Mimari Çıkarımı**
   - Endekslenen veriler sorgulanarak sırasıyla:
     - **Model Layer**: Varlıklar, ilişkiler
     - **View Layer**: Ekranlar, UI soyutlamaları
     - **Controller Layer**: İş akışları, eylemler

4. **Scaffolding**
   - Çıkarılan JSON mimarisinden proje klasör yapısı ve iskelet dosyalarının oluşturulması

5. **Audit & Kodlama**
   - Oluşturulan iskelet kodunun denetlenmesi
   - İş mantığının eklenmesi ve mimari tutarlılık kontrolü

---

## ⚙️ Kullanım Modları

Sistem, farklı geliştirme ihtiyaçlarına uyum sağlayacak şekilde çoklu kullanım modları sunar:

- **CLI (Command Line Interface)**  
  Gerçek projeler ve otomasyon senaryoları için

- **VS Code Extension**  
  Geliştirici ortamına gömülü kullanım (geliştirme aşamasında)

- **Web UI (Streamlit)**  
  Hızlı testler ve demo amaçlı kullanım

---

## 📦 Kurulum (Installation)

### 1️⃣ Sanal Ortam Oluşturma ve Etkinleştirme

```bash
python -m venv .venv
.\.venv\Scripts\activate    # Windows
source .venv/bin/activate   # Linux / macOS
