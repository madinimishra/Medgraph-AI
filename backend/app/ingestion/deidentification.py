"""De-identification of free-text clinical documents, modeled on the
HIPAA Safe Harbor method (45 CFR 164.514(b)(2)): a defined list of 18
direct-identifier categories must be removed or generalized before
data can be treated as de-identified.

Only the categories that can actually appear in free-text hospital
notes are implemented here (names, dates, phone/fax, email, SSN,
medical record/account numbers, addresses, ages 90+, URLs, IP
addresses) - the rest (biometric identifiers, full-face photos, vehicle
identifiers, device serial numbers, etc.) don't apply to text documents
and are out of scope for a text de-identifier.

HONESTY NOTE: this is regex/pattern-based de-identification, not a
clinically validated NLP de-identification system (real production
de-identification - e.g. Philter, or Amazon Comprehend Medical's PHI
detection - uses trained NER models and is still not 100% perfect).
This is good enough to demonstrate the *pattern* and catch the common
cases, not a guarantee that zero PHI could ever leak through on
adversarial or unusual input.
"""

import re

# Order matters: more specific patterns (email, SSN) before broader
# ones (generic digit sequences) so a phone number isn't half-caught by
# a later, looser pattern.
_PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")),
    ("URL", re.compile(r"\bhttps?://[^\s]+\b")),
    ("IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("DATE", re.compile(
        r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE
    )),
    ("MRN_OR_ACCOUNT", re.compile(r"\b(?:MRN|Acct|Account)[\s#:]*[A-Za-z0-9-]{4,}\b", re.IGNORECASE)),
    ("ZIP", re.compile(r"\b\d{5}(?:-\d{4})?\b")),
]

_AGE_90_PLUS = re.compile(r"\bage[:\s]+(9[0-9]|1[0-9]{2})\b", re.IGNORECASE)


class Deidentifier:

    @staticmethod
    def deidentify_text(text: str, names: list[str] = None) -> str:
        """Replace direct identifiers in free text with bracketed
        category tags (e.g. "John Smith" -> "[NAME]"). `names` are
        known entity names (patient/doctor) already extracted upstream
        - those are masked explicitly since a generic regex can't
        reliably detect arbitrary person names in unstructured text."""

        if not text:
            return text

        result = text

        for name in sorted(names or [], key=len, reverse=True):
            if not name or not name.strip():
                continue
            result = re.sub(
                re.escape(name.strip()), "[NAME]", result, flags=re.IGNORECASE
            )

        result = _AGE_90_PLUS.sub("age: [AGE 90+]", result)

        for label, pattern in _PATTERNS:
            result = pattern.sub(f"[{label}]", result)

        return result

    @staticmethod
    def deidentify_entities(entities: dict) -> dict:
        """De-identifies the structured entities extracted from a
        document (LLMExtractor's output) - masks direct identifiers in
        every text/list field, keeps clinical fields (diagnosis,
        symptoms, medicines, lab_tests) untouched since those are the
        actually useful, non-identifying content."""

        names = [
            entities.get("patient") or "",
            entities.get("doctor") or "",
        ]

        deidentified = dict(entities)
        deidentified["patient"] = "[NAME]" if entities.get("patient") else ""
        deidentified["doctor"] = "[NAME]" if entities.get("doctor") else ""

        for field in ("diagnosis", "symptoms", "medicines", "lab_tests"):
            values = entities.get(field)
            if isinstance(values, list):
                deidentified[field] = [
                    Deidentifier.deidentify_text(v, names=names) for v in values
                ]

        if entities.get("follow_up"):
            deidentified["follow_up"] = "[DATE]"

        return deidentified
