# api_test.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
import sys # Hata durumunda programı durdurmak için

# 1. .env dosyasını yükle
load_dotenv()

print("--- API BAĞLANTI TESTİ BAŞLIYOR ---")

# 2. Anahtarı kontrol et
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("FATAL HATA: GOOGLE_API_KEY bulunamadı! Lütfen .env dosyanızı kontrol edin.")
    sys.exit(1)

print("BAŞARILI: API Anahtarı yüklendi.")


# 3. API'ye bağlanma denemesi (Ağ ve Kütüphane Testi)
try:
    genai.configure(api_key=API_KEY)
    
    # Model bağlantısı
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 4. Basit bir içerik oluşturma isteği gönder
    print("API'ye ilk istek gönderiliyor...")
    response = model.generate_content("Hello, can you confirm the connection?")
    
    # 5. Başarılı yanıtı yazdır
    print("\n✅ BAĞLANTI TESTİ BAĞARILI!")
    print(f"API Yanıtı: {response.text.strip()[:50]}...")
    
except Exception as e:
    # Kritik hata: İnternet kesintisi, API yasağı veya kota bitimi.
    print("\n❌ KRİTİK HATA: Bağlantı veya API Hatası.")
    print("Bu hata, temel Agent'larınızı durduran hatadır.")
    print(f"Hata Detayı: {e}")
    sys.exit(1)