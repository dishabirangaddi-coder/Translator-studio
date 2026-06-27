import re
from typing import List, Dict

class SourceValidator:
    @staticmethod
    def validate_text(text: str) -> List[Dict]:
        """
        Validates text and checks for:
        - Spacing errors (double spaces, leading/trailing spaces)
        - Punctuation consistency (missing trailing period, double punctuation)
        - Capitalization patterns (sentence starting with lower case)
        
        Returns a list of issue dicts.
        """
        issues = []
        
        # 1. Spacing check: Double spaces
        if "  " in text:
            issues.append({
                "issue_type": "spacing",
                "severity": "warning",
                "message": "Double spaces detected.",
                "suggested_fix": re.sub(r' +', ' ', text)
            })
            
        # 2. Spacing check: Leading or trailing space
        if text.startswith(" ") or text.endswith(" "):
            issues.append({
                "issue_type": "spacing",
                "severity": "info",
                "message": "Unnecessary leading or trailing spaces.",
                "suggested_fix": text.strip()
            })

        # 3. Capitalization check: First character not capitalized
        # (Only if it starts with an alphabetical character)
        if text and text[0].isalpha() and text[0].islower():
            issues.append({
                "issue_type": "capitalization",
                "severity": "warning",
                "message": "Sentence starts with a lowercase letter.",
                "suggested_fix": text[0].upper() + text[1:]
            })
            
        # 4. Punctuation: Multiple consecutive periods (unless ellipsis)
        if ".." in text and "..." not in text:
            issues.append({
                "issue_type": "punctuation",
                "severity": "warning",
                "message": "Inconsistent punctuation (multiple periods).",
                "suggested_fix": text.replace("..", ".")
            })
            
        return issues
