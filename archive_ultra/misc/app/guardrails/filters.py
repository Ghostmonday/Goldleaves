# Output sanitization
import re
from typing import List
from .guardrail_service import Decision

class OutputFilter:
    @staticmethod
    def sanitize(text: str, decision: Decision) -> str:
        t = text or ""
        # Replace prescriptive language
        t = re.sub(r'\byou should\b', 'one might consider', t, flags=re.I)
        t = re.sub(r'\byou must\b', 'the law may require', t, flags=re.I)
        t = re.sub(r'\bfile this\b', 'this form exists', t, flags=re.I)
        t = re.sub(r'\byour best option\b', 'available options include', t, flags=re.I)
        return t

    @staticmethod
    def inject_disclaimers(text: str, disclaimers: List[str]) -> str:
        if not disclaimers:
            return text
        block = "\n\n".join([f"**Disclaimer:** {d}" for d in disclaimers if d])
        return f"{block}\n\n{text}"
