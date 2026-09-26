import json

from app.core.llm_client import generate_content


class LLMExtractor:

    @staticmethod
    def extract(text):

        prompt = f"""
Extract structured medical information from this hospital document.

Return ONLY valid JSON.

Format:

{{
    "hospital":"",
    "patient":"",
    "doctor":"",
    "department":"",
    "diagnosis":[],
    "symptoms":[],
    "medicines":[],
    "lab_tests":[],
    "follow_up":""
}}

Document:

{text}
"""

        output = generate_content(prompt, purpose="entity_extraction")

        if output.startswith("```json"):
            output = output.replace("```json", "").replace("```", "").strip()

        return json.loads(output)
