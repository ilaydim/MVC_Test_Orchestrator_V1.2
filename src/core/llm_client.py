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
             raise RuntimeError(f"FATAL: Gemini modeli '{self.model_name}' başlatılamadı. Hata: {e}")
             
    # ------------------------------------------------------------------
    # ANA METOT: Agent'ların çağırdığı sade metot (tek çağrı)
    # ------------------------------------------------------------------
    def generate_content(self, prompt: str, max_retries: int = 3) -> str:
        """
        Verilen prompt ile modelden içerik üretir. 
        429 quota hatalarında otomatik retry yapar (API'nin önerdiği delay ile).
        """
        
        if self.model is None:
             raise RuntimeError("Gemini modeli kullanıma hazır değil.")
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Doğrudan model çağrısı
                response = self.model.generate_content(prompt)
                
                # Yanıtı string olarak döndür.
                return response.text
                
            except google_exceptions.ResourceExhausted as e:
                # 429 quota hatası - API'nin önerdiği delay'i kullan
                last_exception = e
                
                # Retry delay'i exception'dan al (eğer varsa)
                retry_delay = 30  # varsayılan 30 saniye
                
                # Önce exception'un retry_delay attribute'unu kontrol et
                if hasattr(e, 'retry_delay') and e.retry_delay:
                    if hasattr(e.retry_delay, 'total_seconds'):
                        retry_delay = e.retry_delay.total_seconds()
                    elif hasattr(e.retry_delay, 'seconds'):
                        retry_delay = float(e.retry_delay.seconds)
                
                # Eğer bulamadıysak, exception mesajından parse etmeye çalış
                if retry_delay == 30:
                    import re
                    error_str = str(e)
                    # "Please retry in 46.96s" formatını yakala
                    match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str, re.IGNORECASE)
                    if match:
                        retry_delay = float(match.group(1))
                    else:
                        # "retry_delay { seconds: 46 }" formatını yakala
                        match = re.search(r'retry_delay.*?seconds.*?(\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
                        if match:
                            retry_delay = float(match.group(1))
                
                if attempt < max_retries - 1:
                    print(f"[LLMClient] Quota exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s before retry...")
                    time.sleep(retry_delay)
                else:
                    # Son deneme de başarısız oldu
                    raise ConnectionError(
                        f"Gemini API quota exceeded after {max_retries} attempts. "
                        f"Please wait and try again later. Last error: {e}"
                    )
                    
            except Exception as e:
                # Diğer hatalar için retry yapma, direkt fırlat
                raise ConnectionError(f"Gemini API çağrısı başarısız oldu: {e}")
        
        # Buraya gelmemeli ama güvenlik için
        if last_exception:
            raise ConnectionError(f"Gemini API çağrısı başarısız oldu: {last_exception}")
        raise ConnectionError("Unexpected error in generate_content")


# ÖNEMLİ NOT: Diğer JSON veya RAG odaklı metotları (llm_json gibi) bu sınıfa 
# projeniz gerektirdikçe ekleyebilirsiniz.