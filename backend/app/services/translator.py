import json
import os
from groq import Groq
from sqlalchemy.orm import Session
from .glossary_enforcer import GlossaryEnforcer
from .critic import RLAIFCritic
from ..models import StyleProfile

class TranslationService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.critic = RLAIFCritic(api_key=self.api_key)
        
    def translate_segment(
        self,
        db: Session,
        text: str,
        source_lang: str,
        target_lang: str,
        style_profile: StyleProfile = None
    ) -> dict:
        """
        Translates a single segment enforcing glossary, tone, and formatting constraints.
        Applies a self-correction RLAIF loop if the critic flags the quality.
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Set GROQ_API_KEY environment variable.")
            
        # 1. Fetch matching glossary terms
        matched_terms = GlossaryEnforcer.get_matching_terms(db, text, source_lang, target_lang)
        glossary_rules = GlossaryEnforcer.format_glossary_instructions(matched_terms)
        glossary_list = [t["source"] for t in matched_terms]
        
        # 2. Extract style profile configurations
        tone = style_profile.tone if style_profile else "Formal"
        custom_rules = style_profile.custom_rules if style_profile else []
        style_instructions = f"Tone: {tone}\n"
        if custom_rules:
            style_instructions += "Custom style rules you MUST follow:\n"
            for rule in custom_rules:
                style_instructions += f"- {rule}\n"
                
        # 3. Create System Prompt
        system_prompt = f"""You are a professional corporate translator.
Translate the input text from {source_lang} to {target_lang}.

### CRITICAL REQUIREMENTS:
1. Preserve all formatting, placeholders (e.g., {{user_name}}), HTML tags, or escape characters.
2. Respect the target tone and style rules:
{style_instructions}
3. Strict Glossary Enforcement:
{glossary_rules}

### OUTPUT FORMAT:
Provide your response strictly in the following JSON format. Do not write any markdown codeblock fences, explanations, or introductory text.
{{
    "translation": "translated text goes here",
    "confidence_score": <an integer between 1 and 10 reflecting translation certainty>
}}
"""

        # We will attempt translation, run back-translation, check with Critic, and retry if failed
        attempts = 0
        max_attempts = 3
        translation = ""
        back_translation = ""
        confidence = 8
        critic_feedback = ""
        
        while attempts < max_attempts:
            user_prompt = f"Translate this text: {text}"
            if critic_feedback:
                user_prompt += f"\n\n[CRITIC CORRECTION REQUEST]: The previous translation failed validation with discrepancy: '{critic_feedback}'. Please correct it and output the updated JSON."
            
            # Invoke LLM for Translation
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                translation = result.get("translation", "")
                confidence = result.get("confidence_score", 8)
            except Exception as e:
                print(f"Error parsing translation JSON: {e}")
                translation = response.choices[0].message.content.strip()
            
            # Generate Back-Translation
            back_translation = self.back_translate(translation, target_lang, source_lang)
            
            # Evaluate with RLAIF Critic
            critic_result = self.critic.evaluate_translation(
                source=text,
                translation=translation,
                back_translation=back_translation,
                glossary_terms=glossary_list
            )
            
            if critic_result.get("passed", True) or attempts == max_attempts - 1:
                # Loop ends if critic passes or we hit max retries
                break
            else:
                attempts += 1
                critic_feedback = critic_result.get("discrepancy", "General meaning misalignment.")
                print(f"Critic correction triggered for segment (Attempt {attempts}): {critic_feedback}")
        
        return {
            "translated_text": translation,
            "back_translated_text": back_translation,
            "confidence_score": confidence
        }

    def back_translate(self, translated_text: str, target_lang: str, source_lang: str) -> str:
        """
        Translates target output back into source language for quick verification by non-native reviewers.
        """
        if not self.client or not translated_text:
            return ""
            
        system_prompt = f"""You are an objective translator.
Translate the input text back from {target_lang} to {source_lang} literally to help a non-bilingual manager verify if the meaning is exactly preserved.
Output ONLY the translated text without explanations or headers.
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": translated_text}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Back-translation failed: {e}")
            return ""
