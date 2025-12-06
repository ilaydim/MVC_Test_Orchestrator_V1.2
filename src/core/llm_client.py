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

    # ------------------------------------------------------------------
    # RAG Question Answering Prompt
    # ------------------------------------------------------------------
    def build_prompt(self, query, retrieved_chunks):
        """
        Creates a clean RAG prompt for Gemini.
        """

        context_str = ""
        for i, chunk in enumerate(retrieved_chunks):
            context_str += f"\n\n--- Source {i+1} ---\n{chunk}\n"

        prompt = f"""
You are an AI assistant answering questions about a Software Requirements Specification (SRS) document.

### IMPORTANT RULES:
1. FIRST, determine if the question is related to the SRS content provided below.
2. If the question is NOT related to the SRS (e.g., general knowledge, unrelated topics, personal questions), reply EXACTLY with:
   "⚠️ This question is not related to the uploaded SRS document. Please ask questions about the Software Requirements Specification that was uploaded."
3. If the question IS related, answer using ONLY the provided SRS context.
4. Never use external knowledge. Never speculate.

### CONTEXT FROM SRS:
{context_str}

### QUESTION:
{query}
"""
        return prompt

    def answer(self, query, chunks):
        """
        Sends standard RAG prompt to Gemini and returns:
        - answer text
        - token usage metadata (if available)
        """
        prompt = self.build_prompt(query, chunks)
        response = self.model.generate_content(prompt)

        usage = getattr(response, "usage_metadata", {})

        return {
            "answer": response.text,
            "usage": usage,
        }

    # ------------------------------------------------------------------
    # MVC Architecture Extraction Prompt
    # ------------------------------------------------------------------
    def build_architecture_prompt(self, retrieved_chunks):
        """
        Builds a prompt that asks the LLM to extract an MVC-style
        architecture description in STRICT JSON format.
        """

        context_str = ""
        for i, chunk in enumerate(retrieved_chunks):
            context_str += f"\n\n--- SRS Excerpt {i+1} ---\n{chunk}\n"

        prompt = f"""
You are a senior software architect.
Your task is to extract an MVC architecture from the provided SRS excerpts.

Focus on *high-level responsibilities*, not implementation details.
Use ONLY the SRS context. If something is unclear, make the simplest consistent assumption.

Return a **single valid JSON object only**. No prose, no comments, no code fences.

### REQUIRED JSON FORMAT:
{{
  "model": [
    {{
      "name": "string",
      "description": "string",
      "related_requirements": ["string"]
    }}
  ],
  "view": [
    {{
      "name": "string",
      "description": "string",
      "related_requirements": ["string"]
    }}
  ],
  "controller": [
    {{
      "name": "string",
      "description": "string",
      "related_requirements": ["string"]
    }}
  ]
}}

### SRS CONTEXT:
{context_str}
"""
        return prompt

    def extract_architecture_json(self, chunks):
        """
        Sends architecture extraction prompt to Gemini and parses the JSON result.
        """
        prompt = self.build_architecture_prompt(chunks)
        response = self.model.generate_content(prompt)

        text = response.text.strip()

        # Remove ```json ... ``` fences if present
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON. Error: {e}\n"
                f"Raw response: {text[:500]}..."
            )
