from typing import Dict, Any, List
import json

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class ReviewerAgent(BaseArchitectAgent):
    """
    Receives the technical violations report from the Rules Agent and uses the 
    Gemini API to translate them into a professional audit report with 
    actionable, natural language recommendations.
    """

    def generate_audit_report(self, technical_violations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Main entry point. Generates the final, human-readable audit report.
        """
        
        if not technical_violations:
            report = {
                "audit_summary": "PASSED: No structural or convention violations detected.",
                "passed": True,
                "recommendations": []
            }
        else:
            violations_str = json.dumps(technical_violations, indent=2)
            prompt = self._build_reviewer_prompt(violations_str)
            report_json = self.llm_json(prompt)
            
            report = {
                "audit_summary": report_json.get("summary", "Review complete. See details."),
                "passed": False,
                "recommendations": report_json.get("recommendations", [])
            }

        self.save_output(report, "final_audit_report.json")
        return report

    def _build_reviewer_prompt(self, violations_str: str) -> str:
        """
        Builds the LLM prompt to generate the structured audit report.
        """
        
        return f"""
You are a Senior Software Reviewer AI. Your task is to analyze a list of technical 
violations found in an automatically generated MVC project scaffold and convert them 
into a professional audit report with actionable recommendations.

### TECHNICAL VIOLATIONS (JSON Array):
{violations_str}

### STRIKE ZONE:
- Focus on why each violation is a problem (e.g., maintainability, standard compliance).
- Provide a clear, step-by-step recommendation for *how* to fix the issue.
- Maintain a professional and constructive tone.

### STRICT JSON OUTPUT FORMAT (NO COMMENTS, NO EXTRA TEXT):
{{
    "summary": "A high-level summary of the most critical issue and the overall quality.",
    "recommendations": [
        {{
            "violation_type": "The type of violation (e.g., MVC_VIOLATION)",
            "file": "The file path where the issue was found (e.g., scaffolds/models/User.py)",
            "problem": "A brief explanation of the technical problem found.",
            "recommendation": "A clear, natural language instruction on how the developer should fix it."
        }}
    ]
}}

Return ONLY the JSON.
"""