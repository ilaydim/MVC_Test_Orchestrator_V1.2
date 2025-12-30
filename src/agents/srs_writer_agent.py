from pathlib import Path

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent
from src.core.llm_client import QuotaExceededError, LLMConnectionError

class SRSWriterAgent(BaseArchitectAgent):
    """
    Generates the Software Requirements Specification (SRS) document based on the user's high-level idea.
    """

    def __init__(self, rag_pipeline=None, llm_client=None):
        super().__init__(rag_pipeline, llm_client)

    def generate_srs(self, user_idea: str) -> Path:
        """
        Instructs the LLM to generate the SRS document, saves the output to the data/ folder, 
        and returns the file path.
        """
        # Load prompt from external file
        prompt_path = Path(__file__).resolve().parents[2] / ".github" / "prompts" / "create_srs.prompt.md"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        
        prompt = prompt_template.replace("{{user_idea}}", user_idea)
        
        print("[SRS Writer] Generating SRS text...")
        
        try:
            srs_text = self.llm.generate_content(prompt, stream=False) 

        except QuotaExceededError as qe:
            print(f"\n{str(qe)}")
            print("[SRS Writer] Pipeline stopped gracefully. Please try again later.")
            raise
            
        except LLMConnectionError as lce:
            print(f"\n[SRS Writer ERROR] LLM connection failed: {lce}")
            print("[SRS Writer] Pipeline stopped. Check your network/API key.")
            raise
            
        except Exception as e:
            print(f"[SRS Writer ERROR] Unexpected error: {e}")
            raise

        self.data_dir.mkdir(parents=True, exist_ok=True)
        srs_filename = "srs_document.txt"
        srs_path = self.data_dir / srs_filename
        srs_path.write_text(srs_text, encoding="utf-8")
        
        print(f"[SRS Writer] SRS successfully created: {srs_path.name}")
        
        return srs_path