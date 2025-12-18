# src/core/llm_client.py

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import os
import time
from typing import Optional # Tip hint'leri tutuldu.

# Projenizin konfigürasyonunu yükle.
from src.core.config import LLM_MODEL_NAME 

load_dotenv()


# ============================================================
# Custom Exception Classes (Graceful Error Handling)
# ============================================================
class QuotaExceededError(Exception):
    """Günlük API kota limiti dolduğunda fırlatılır."""
    pass


class LLMConnectionError(Exception):
    """Genel LLM bağlantı hatası."""
    pass


class LLMClient:
    """
    Handles minimal Gemini API calls for Agent operations.
    """

    def __init__(self, model_name: str = LLM_MODEL_NAME):
        self.model_name = model_name

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("ERROR: GOOGLE_API_KEY is missing in .env file!")

        genai.configure(api_key=api_key)
        self.model: Optional[genai.GenerativeModel] = None
        
        try:
             # Modeli başlat
             self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
             error_msg = str(e)
             # Provide helpful error message for model issues
             if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
                 suggestion = (
                     f"\n💡 Model '{self.model_name}' bulunamadı veya erişilemiyor.\n"
                     f"   Çalışan alternatifler:\n"
                     f"   - 'gemini-1.5-flash' (önerilen, ücretsiz tier)\n"
                     f"   - 'gemini-pro' (eski ama stabil)\n"
                     f"   - 'gemini-1.5-pro' (faturalandırma gerekebilir)\n"
                     f"   src/core/config.py dosyasında LLM_MODEL_NAME'i değiştirin."
                 )
                 raise RuntimeError(f"FATAL: Gemini modeli '{self.model_name}' başlatılamadı.\n{error_msg}{suggestion}")
             elif "billing" in error_msg.lower() or "quota" in error_msg.lower():
                 suggestion = (
                     f"\n💡 Model '{self.model_name}' faturalandırma gerektiriyor olabilir.\n"
                     f"   Ücretsiz tier için 'gemini-1.5-flash' veya 'gemini-pro' kullanın.\n"
                     f"   src/core/config.py dosyasında LLM_MODEL_NAME'i değiştirin."
                 )
                 raise RuntimeError(f"FATAL: Gemini modeli '{self.model_name}' başlatılamadı.\n{error_msg}{suggestion}")
             else:
                 raise RuntimeError(f"FATAL: Gemini modeli '{self.model_name}' başlatılamadı. Hata: {e}")
             
    # ------------------------------------------------------------------
    # ANA METOT: Agent'ların çağırdığı sade metot (tek çağrı)
    # ------------------------------------------------------------------
    def generate_content(self, prompt: str, max_retries: int = 0, stream: bool = False) -> str:
        """
        Verilen prompt ile modelden içerik üretir. 
        429 quota hatalarında gracefully fail eder (sürekli retry yapmaz).
        max_retries=0: Kota dolduğunda hemen durdur (varsayılan).
        stream=True: Streaming yanıt (progress için, ama toplam süre aynı)
        """
        
        if self.model is None:
             raise RuntimeError("Gemini modeli kullanıma hazır değil.")
        
        import sys
        
        try:
            if stream:
                # Streaming mode: Progress göster ama toplam süre aynı
                print("[LLM] Generating...", end="", flush=True)
                response = self.model.generate_content(prompt, stream=True)
                chunks = []
                for chunk in response:
                    if chunk.text:
                        chunks.append(chunk.text)
                        print(".", end="", flush=True)  # Progress indicator
                print(" ✓", flush=True)
                return "".join(chunks)
            else:
                # Normal mode: Tek seferde al (daha hızlı)
                response = self.model.generate_content(prompt)
                return response.text
            
        except google_exceptions.ResourceExhausted as e:
            # 429 quota/rate limit hatası
            error_msg = str(e)
            
            # Rate limit mi yoksa daily quota mu?
            is_rate_limit = "rate limit" in error_msg.lower() or "quota" not in error_msg.lower()
            
            if is_rate_limit:
                # Rate limit - kısa süre bekle ve retry yap
                import re
                retry_seconds = 5  # Default 5 saniye
                match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_msg, re.IGNORECASE)
                if match:
                    retry_seconds = float(match.group(1))
                    retry_seconds = min(retry_seconds, 60)  # Max 60 saniye
                
                # Rate limit hatası - LLMConnectionError olarak fırlat (retry edilebilir)
                raise LLMConnectionError(
                    f"Rate limit reached. Retry after {retry_seconds:.0f} seconds. "
                    f"Error: {error_msg}"
                )
            else:
                # Daily quota doldu - QuotaExceededError fırlat (dur)
                import re
                retry_delay_str = "bilinmeyen süre"
                match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_msg, re.IGNORECASE)
                if match:
                    retry_seconds = float(match.group(1))
                    retry_hours = retry_seconds / 3600
                    retry_delay_str = f"{retry_hours:.1f} saat" if retry_hours >= 1 else f"{retry_seconds:.0f} saniye"
                
                raise QuotaExceededError(
                    f"\n⛔ Gemini API günlük kota limiti doldu!\n"
                    f"   Yaklaşık {retry_delay_str} sonra tekrar deneyebilirsiniz.\n"
                    f"   Alternatif: .env dosyanıza yeni bir GOOGLE_API_KEY ekleyin.\n"
                    f"   Detay: {error_msg}"
                )
                
        except Exception as e:
            # Diğer hatalar için detaylı mesaj
            raise LLMConnectionError(f"Gemini API çağrısı başarısız oldu: {str(e)}")


# ÖNEMLİ NOT: Diğer JSON veya RAG odaklı metotları (llm_json gibi) bu sınıfa 
# projeniz gerektirdikçe ekleyebilirsiniz.