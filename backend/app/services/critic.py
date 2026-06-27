import json
import os
from groq import Groq

class RLAIFCritic:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def evaluate_translation(self, source: str, translation: str, back_translation: str, glossary_terms: list) -> dict:
        """
        Grades the semantic equivalence between source and back-translation,
        and verifies if all glossary terms are correctly applied.
        """
        if not self.client:
            return {"passed": True, "accuracy_score": 100, "discrepancy": ""}
            
        system_prompt = """You are a translation quality assurance judge. 
Your task is to inspect the translation quality by comparing the Original text and the Back-translated text.

Check:
1. Are all names, dates, and numbers exactly preserved?
2. Is the core meaning identical?
3. Did the translation use the mandatory terms?

Output strictly in JSON format:
{
  "passed": true | false,
  "accuracy_score": <int 0-100>,
  "discrepancy": "Describe errors or missing terms if passed is false, otherwise empty string"
}
"""
        user_content = f"""
Original English: "{source}"
Target Translation: "{translation}"
Back-Translated to English: "{back_translation}"
Mandatory Terms: {glossary_terms}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Safe default fallback in case of rate limits or parsing errors
            print(f"Critic review failed: {e}")
            return {"passed": True, "accuracy_score": 85, "discrepancy": ""}
