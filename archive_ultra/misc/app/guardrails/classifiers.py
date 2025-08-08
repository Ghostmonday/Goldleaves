# Minimal deterministic classifiers (no ML)
import re
from typing import Optional, Dict, Literal

class IntentClassifier:
    @staticmethod
    def classify(utterance: str) -> Literal["inform","advise","draft","unknown"]:
        u = utterance or ""
        if re.search(r'\b(what is|define|definition of|explain)\b', u, re.I):
            return "inform"
        if re.search(r'\b(should I|what should|my case|my situation|help me)\b', u, re.I):
            return "advise"
        if re.search(r'\b(write|draft|create|prepare)\b', u, re.I):
            return "draft"
        return "unknown"

class JurisdictionDetector:
    STATE = r'\b(California|CA|Texas|TX|New York|NY)\b'
    COURT = r'(Superior Court of (\w+))|((\w+) County Court)'
    @staticmethod
    def detect(utterance: str, metadata: Dict) -> Optional[str]:
        u = utterance or ""
        if re.search(JurisdictionDetector.STATE, u, re.I):
            m = re.search(JurisdictionDetector.STATE, u, re.I).group(1).upper()
            return "US-" + (m if len(m) == 2 else {"CALIFORNIA":"CA","TEXAS":"TX","NEW YORK":"NY"}[m])
        # fallbacks skipped for MVP
        return None
