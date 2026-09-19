import re
from typing import Dict, List, Optional, Tuple
from app.providers.base import DataClassification

PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "mrn": r"\b(?:MRN|Medical\s*Record\s*Number|Patient\s*ID|Chart\s*#)[:\s]*#?[A-Za-z0-9-]{5,12}\b",
    "patient_dob": r"\b(?:DOB|Date\s*of\s*Birth|Born)[:\s]*\d{1,4}[/-]\d{1,2}[/-]\d{2,4}\b",
    "national_id": r"\b(?:National\s*ID|NHS\s*#?|CPR\s*#?)[:\s]*\d{6,12}\b",
    "clinical_subject": r"\b(?:Subject|Participant|Volunteer)\s*ID[:\s]*#?[A-Za-z0-9-]{4,16}\b",
    "patient_name": r"\bPatient\s+Name\s*:\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
}

# Precompile patterns with targeted flags to avoid per-call compilation and case-insensitive over-matching (IN-02, WR-03)
COMPILED_PATTERNS = [
    ("email", re.compile(PATTERNS["email"], re.IGNORECASE)),
    ("phone", re.compile(PATTERNS["phone"])),
    ("ssn", re.compile(PATTERNS["ssn"])),
    ("mrn", re.compile(PATTERNS["mrn"], re.IGNORECASE)),
    ("patient_dob", re.compile(PATTERNS["patient_dob"], re.IGNORECASE)),
    ("national_id", re.compile(PATTERNS["national_id"], re.IGNORECASE)),
    ("clinical_subject", re.compile(PATTERNS["clinical_subject"], re.IGNORECASE)),
    ("patient_name", re.compile(PATTERNS["patient_name"])),  # Case-sensitive to preserve ordinary English
]

PUBLIC_SOURCES = {
    "pubmed",
    "clinical_trials",
    "fda",
    "ema",
    "newsapi",
    "biopharmadive",
    "fiercepharma",
    "fierce_pharma",
    "et_pharma",
}


class PIIPHIScrubber:
    @staticmethod
    def scrub(text: Optional[str]) -> Tuple[str, bool, Dict[str, int]]:
        """
        Scrubs PII/PHI patterns from text.
        Returns: (redacted_text, is_scrubbed, match_counts)
        """
        if not text:
            return "", False, {}

        redacted = text
        counts: Dict[str, int] = {}
        has_pii = False

        for name, compiled_regex in COMPILED_PATTERNS:
            matches = compiled_regex.findall(redacted)
            if matches:
                has_pii = True
                counts[name] = len(matches)
                redacted = compiled_regex.sub(f"[{name.upper()}_REDACTED]", redacted)

        return redacted, has_pii, counts

    @staticmethod
    def classify_payload(text: Optional[str], source_type: str = "unknown") -> DataClassification:
        """
        Determines classification for an incoming payload based on source & content checks.
        """
        _, has_pii, _ = PIIPHIScrubber.scrub(text)
        if has_pii:
            return DataClassification.CONFIDENTIAL
        src = source_type.lower().strip()
        if src in ["synthetic", "demo"]:
            return DataClassification.SYNTHETIC
        if src in PUBLIC_SOURCES:
            return DataClassification.PUBLIC
        return DataClassification.UNKNOWN

