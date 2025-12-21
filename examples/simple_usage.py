"""
MVC Test Orchestrator - Basit Kullanım Örneği

Bu örnek, MVC Test Orchestrator'ı başka bir projede nasıl kullanacağınızı gösterir.
"""

import os
import sys
from pathlib import Path

# MVC Test Orchestrator path'ini ekleyin (kendi path'inize göre ayarlayın)
MVC_ORCHESTRATOR_PATH = Path(__file__).parent.parent  # Bu örnekte parent klasör
sys.path.insert(0, str(MVC_ORCHESTRATOR_PATH))

# API Key'i ayarlayın
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"  # Kendi API key'inizi ekleyin

from src.rag.rag_pipeline import RAGPipeline
from src.core.llm_client import LLMClient
from src.agents.srs_writer_agent import SRSWriterAgent
from src.agents.architect_agent.requirements_agent import RequirementsAgent
from src.agents.architect_agent.model_architect_agent import ModelArchitectAgent
from src.agents.architect_agent.controller_architect_agent import ControllerArchitectAgent
from src.agents.architect_agent.view_architect_agent import ViewArchitectAgent
from src.agents.scaffolder.mvc_scaffolder import MVCScaffolder
from src.core.config import DEFAULT_TOP_K


def example_1_create_srs():
    """Örnek 1: SRS Oluşturma"""
    print("=" * 60)
    print("Örnek 1: SRS Oluşturma")
    print("=" * 60)
    
    # Initialize
    llm_client = LLMClient()
    rag_pipeline = RAGPipeline(llm_client=llm_client)
    srs_writer = SRSWriterAgent(rag_pipeline, llm_client)
    
    # SRS oluştur
    user_idea = "Simple blog with posts and comments"
    srs_path = srs_writer.generate_srs(user_idea)
    
    print(f"\n✅ SRS oluşturuldu: {srs_path}")
    return srs_path


def example_2_extract_architecture(srs_path: Path):
    """Örnek 2: Mimari Çıkarma"""
    print("\n" + "=" * 60)
    print("Örnek 2: Mimari Çıkarma")
    print("=" * 60)
    
    # Initialize
    llm_client = LLMClient()
    rag_pipeline = RAGPipeline(llm_client=llm_client)
    
    # SRS'yi indexle
    rag_pipeline.index_srs(srs_path)
    print("✅ SRS indexed")
    
    # Agents
    requirements_agent = RequirementsAgent(rag_pipeline, llm_client)
    model_agent = ModelArchitectAgent(rag_pipeline, llm_client)
    controller_agent = ControllerArchitectAgent(rag_pipeline, llm_client)
    view_agent = ViewArchitectAgent(rag_pipeline, llm_client)
    
    # Extract
    print("\n📋 Extracting requirements...")
    requirements = requirements_agent.extract_analysis(k=DEFAULT_TOP_K)
    
    print("🏗️  Extracting models...")
    models = model_agent.extract_models(k=DEFAULT_TOP_K)
    
    print("🎮 Extracting controllers...")
    controllers = controller_agent.extract_controllers(k=DEFAULT_TOP_K)
    
    print("👁️  Extracting views...")
    views = view_agent.extract_views(k=DEFAULT_TOP_K)
    
    # Combine
    architecture = {
        "model": models.get("model", []),
        "controller": controllers.get("controller", []),
        "view": views.get("view", [])
    }
    
    print(f"\n✅ Mimari çıkarıldı:")
    print(f"   - Models: {len(architecture['model'])}")
    print(f"   - Controllers: {len(architecture['controller'])}")
    print(f"   - Views: {len(architecture['view'])}")
    
    return architecture


def example_3_create_scaffold(architecture: dict, output_dir: Path):
    """Örnek 3: Scaffold Oluşturma"""
    print("\n" + "=" * 60)
    print("Örnek 3: Scaffold Oluşturma")
    print("=" * 60)
    
    # Scaffolder oluştur
    scaffolder = MVCScaffolder(
        project_root=output_dir,
        scaffold_root=output_dir / "scaffolds"
    )
    
    # Scaffold oluştur
    result = scaffolder.scaffold_all(architecture)
    
    print(f"\n✅ Scaffold oluşturuldu:")
    print(f"   - Models: {len(result['models'])} dosya")
    print(f"   - Views: {len(result['views'])} dosya")
    print(f"   - Controllers: {len(result['controllers'])} dosya")
    
    return result


def main():
    """Ana fonksiyon"""
    # Output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 1. SRS oluştur
        srs_path = example_1_create_srs()
        
        # 2. Mimari çıkar
        architecture = example_2_extract_architecture(srs_path)
        
        # 3. Scaffold oluştur
        scaffold_result = example_3_create_scaffold(architecture, output_dir)
        
        print("\n" + "=" * 60)
        print("🎉 Tüm örnekler başarıyla tamamlandı!")
        print(f"📁 Çıktılar: {output_dir}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

