import re
from typing import List, Dict
from sqlalchemy.orm import Session
from ..models import GlossaryTerm

class GlossaryEnforcer:
    @staticmethod
    def get_matching_terms(db: Session, text: str, source_lang: str, target_lang: str) -> List[Dict]:
        """
        Scans source text for any glossary terms defined for the given language pair.
        Returns a list of matching term dictionaries.
        """
        # Query all glossary terms for this language pair
        terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.source_lang == source_lang,
            GlossaryTerm.target_lang == target_lang
        ).all()
        
        matched_terms = []
        
        # Look for occurrences using case-insensitive word boundary checks
        for term in terms:
            # Escape term in case it contains special regex characters
            pattern = r'\b' + re.escape(term.source_term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                matched_terms.append({
                    "source": term.source_term,
                    "target": term.target_term,
                    "context": term.context_note or "No specific context provided."
                })
                
        return matched_terms

    @staticmethod
    def format_glossary_instructions(matched_terms: List[Dict]) -> str:
        """
        Formats matches into a clear instructions block for the LLM system prompt.
        """
        if not matched_terms:
            return ""
        
        instructions = "\n### GLOSSARY ENFORCEMENT RULES:\n"
        instructions += "You MUST translate the following terms EXACTLY as specified. Do not substitute synonyms:\n"
        for idx, term in enumerate(matched_terms, 1):
            instructions += f"{idx}. '{term['source']}' must be translated as '{term['target']}'. (Context: {term['context']})\n"
        
        return instructions
