# src/core/llm_client.py

import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

from src.core.config import LLM_MODEL_NAME  

load_dotenv()


class LLMClient:
    """
    Handles Gemini API calls and constructs grounded RAG prompts.
    Used by architect agent, reviewer agent, and scaffolder agent.
    """

    def __init__(self, model_name: str = LLM_MODEL_NAME):
        self.model_name = model_name

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("ERROR: GOOGLE_API_KEY is missing in .env file!")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)