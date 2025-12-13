# src/core/llm_client.py

import google.generativeai as genai
from dotenv import load_dotenv
import os
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
    def generate_content(self, prompt: str) -> str:
        """
        Verilen prompt ile modelden içerik üretir. Hata deneme mekanizması YOKTUR.
        """
        
        if self.model is None:
             raise RuntimeError("Gemini modeli kullanıma hazır değil.")
        
        try:
            # Doğrudan model çağrısı
            response = self.model.generate_content(prompt)
            
            # Yanıtı string olarak döndür.
            return response.text
            
        except Exception as e:
            # API hatasını yakalar ve üst seviyeye fırlatır (SRS Writer Agent bunu yakalayacak)
            raise ConnectionError(f"Gemini API çağrısı başarısız oldu: {e}")


# ÖNEMLİ NOT: Diğer JSON veya RAG odaklı metotları (llm_json gibi) bu sınıfa 
# projeniz gerektirdikçe ekleyebilirsiniz.