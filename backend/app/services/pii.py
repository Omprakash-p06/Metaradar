import re
from typing import Dict, Tuple
from app.providers.base import DataClassification

PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "mrn": r"\b(?:MRN|Medical\s*Record\s*Number|Patient\s*ID|Chart\s*#?)[:\s]*#?[A-Za-z0-9-]{5,12}\b",
    "patient_dob": r"\b(?:DOB|Date\s*of\s*Birth|Born)[:\s]*\d{1,4}[/-]\d{1,2}[/-]\d{2,4}\b",
    "national_id": r"\b(?:National\s*ID|NHS\s*#?|CPR\s*#?)[:\s]*\d{6,12}\b",
    "clinical_subject": r"\b(?:Subject|Participant|Volunteer)\s*ID[:\s]*#?[A-Za-z0-9-]{4,16}\b",
    "patient_name": r"\bPatient(?:\s+Name)?[:\s]+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
}


class PIIPHIScrubber:
    @staticmethod
    def scrub(text: str) -> Tuple[str, bool, Dict[str, int]]:
        """
        Scrubs PII/PHI patterns from text.
        Returns: (redacted_text, is_scrubbed, match_counts)
        """
        redacted = text
        counts = {}
        has_pii = False

        for name, pattern in PATTERNS.items():
            matches = re.findall(pattern, redacted, flags=re.IGNORECASE)
            if matches:
                has_pii = True
                counts[name] = len(matches)
                redacted = re.sub(pattern, f"[{name.upper()}_REDACTED]", redacted, flags=re.IGNORECASE)

        return redacted, has_pii, counts

    @staticmethod
    def classify_payload(text: str, source_type: str = "unknown") -> DataClassification:
        """
        Determines classification for an incoming payload based on source & content checks.
        """
        _, has_pii, _ = PIIPHIScrubber.scrub(text)
        if has_pii:
            return DataClassification.CONFIDENTIAL
        src = source_type.lower().strip()
        if src in ["synthetic", "demo"]:
            return DataClassification.SYNTHETIC
        if src in [
            "pubmed",
            "clinical_trials",
            "fda",
            "ema",
            "newsapi",
            "congress",
            "biopharmadive",
            "fiercepharma",
            "fierce_pharma",
            "et_pharma",
        ]:
            return DataClassification.PUBLIC
        return DataClassification.UNKNOWN

