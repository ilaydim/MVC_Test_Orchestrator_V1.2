# src/tests/rag_test.py

import os
import sys
from pathlib import Path

# Proje yolunu ekle (import hatalarını önler)
PROJECT_ROOT = Path(__file__).resolve().parents[2] 
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
    
# Gerekli importlar
from src.core.llm_client import LLMClient
from src.rag.rag_pipeline import RAGPipeline
from src.agents.architect_agent.requirements_agent import RequirementsAgent


def test_agent_initialization():
    """LLM ve RAG'ın Agent içinde hatasız başlatılıp başlatılmadığını test eder."""
    try:
        print("\n--- BAŞLATMA TESTİ ---")
        llm = LLMClient()
        rag = RAGPipeline()
        
        # Agent'ı başlatmayı dene (Hata burada çıkabilir)
        agent = RequirementsAgent(rag_pipeline=rag, llm_client=llm)
        print("✅ Agent, LLM ve RAG hatasız başlatıldı.")
        
        # Dosya yollarını kontrol et (data/ klasörüne erişimi test eder)
        print(f"Data Dizini: {agent.data_dir}")
        assert agent.data_dir.exists(), "Data dizini bulunamadı!"
        print("✅ Data dizini erişimi başarılı.")

    except Exception as e:
        print(f"❌ KRİTİK HATA: Agent başlatma sırasında hata: {e}")
        sys.exit(1)


def test_rag_indexing():
    """RAG'ın bir metin dosyasını (SRS simülasyonu) indexleyip indexlemediğini test eder."""
    print("\n--- RAG INDEXLEME TESTİ ---")
    rag = RAGPipeline()
    test_content = "Bu bir test gereksinimler belgesidir. Model, Controller ve View mimarileri hakkında bilgi içerir."
    test_file_path = rag.data_dir / "temp_srs_test.txt"
    
    # Geçici dosyayı oluştur
    test_file_path.write_text(test_content, encoding="utf-8")

    try:
        # SRS'yi indexle (rag_pipeline.py'deki düzeltmeyi uyguladığınızı varsayarak)
        result = rag.index_pdf(test_file_path)
        
        if result['chunks_added'] > 0:
            print(f"✅ Indexleme başarılı. Eklenen parça sayısı: {result['chunks_added']}")
        else:
            print("❌ Indexleme başarısız. Parça eklenmedi (Chunker hatası olabilir).")
            
        # Test sonrası temizlik
        test_file_path.unlink() 

    except Exception as e:
        print(f"❌ KRİTİK HATA: RAG Indexleme sırasında hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_agent_initialization()
    test_rag_indexing()