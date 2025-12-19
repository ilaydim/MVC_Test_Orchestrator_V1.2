from typing import Dict, Any, List
import json

from src.agents.architect_agent.base_architect_agent import BaseArchitectAgent 

class ReviewerAgent(BaseArchitectAgent):
    """
    Receives the technical violations report from the Rules Agent and uses the 
    Gemini API to translate them into a professional audit report with 
    actionable, natural language recommendations.
    """

    def generate_audit_report(self, technical_violations: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Main entry point. Generates the final, human-readable audit report.
        Reads violations from violations.json (Structured Output) if technical_violations not provided.
        Sends to Google Gemini API and generates final_report.json (Structured Output).
        """
        
        # If violations not provided, try to load from violations.json
        if technical_violations is None:
            violations_file = self.data_dir / "violations.json"
            if violations_file.exists():
                try:
                    with open(violations_file, "r", encoding="utf-8") as f:
                        violations_data = json.load(f)
                    technical_violations = violations_data.get("violations", [])
                    print(f"[ReviewerAgent] Loaded {len(technical_violations)} violation(s) from violations.json")
                except Exception as e:
                    print(f"[ReviewerAgent] Warning: Could not load violations.json: {e}")
                    technical_violations = []
            else:
                print(f"[ReviewerAgent] violations.json not found, using empty violations list")
                technical_violations = []
        
        if not technical_violations:
            report = {
                "audit_summary": "PASSED: No structural or convention violations detected.",
                "passed": True,
                "recommendations": []
            }
        else:
            # Send violations.json content to Google Gemini API
            try:
                violations_str = json.dumps(technical_violations, indent=2)
                print(f"[ReviewerAgent] Sending {len(technical_violations)} violation(s) to Google Gemini API...")
                prompt = self._build_reviewer_prompt(violations_str)
                report_json = self.llm_json(prompt)
                
                if not report_json:
                    print(f"[ReviewerAgent] Warning: LLM returned empty response")
                    report = {
                        "audit_summary": "Review complete. LLM returned empty response.",
                        "passed": False,
                        "recommendations": []
                    }
                else:
                    report = {
                        "audit_summary": report_json.get("summary", "Review complete. See details."),
                        "passed": False,
                        "recommendations": report_json.get("recommendations", [])
                    }
                    print(f"[ReviewerAgent] Generated report with {len(report.get('recommendations', []))} recommendation(s)")
            except Exception as e:
                print(f"[ReviewerAgent] Error generating report from LLM: {e}")
                import traceback
                traceback.print_exc(file=__import__('sys').stdout)
                # Return a fallback report
                report = {
                    "audit_summary": f"Error generating report: {str(e)}. Check violations.json for details.",
                    "passed": False,
                    "recommendations": [
                        {
                            "violation_type": "SYSTEM_ERROR",
                            "file": "N/A",
                            "problem": f"Failed to generate audit report: {str(e)}",
                            "recommendation": "Check violations.json file for violation details. Retry audit after fixing LLM connection issues."
                        }
                    ]
                }

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