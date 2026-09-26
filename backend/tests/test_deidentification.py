from app.ingestion.deidentification import Deidentifier


class TestDeidentifyText:

    def test_masks_a_known_name(self):
        result = Deidentifier.deidentify_text("Patient: Anjali Kapoor", names=["Anjali Kapoor"])
        assert "Anjali Kapoor" not in result
        assert "[NAME]" in result

    def test_masks_email_addresses(self):
        result = Deidentifier.deidentify_text("Contact: anjali.kapoor@email.com")
        assert "anjali.kapoor@email.com" not in result
        assert "[EMAIL]" in result

    def test_masks_phone_numbers(self):
        result = Deidentifier.deidentify_text("Phone: 555-123-4567")
        assert "555-123-4567" not in result
        assert "[PHONE]" in result

    def test_masks_ssn(self):
        result = Deidentifier.deidentify_text("SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "[SSN]" in result

    def test_masks_iso_dates(self):
        result = Deidentifier.deidentify_text("Follow up: 2026-11-02")
        assert "2026-11-02" not in result
        assert "[DATE]" in result

    def test_leaves_clinical_content_untouched(self):
        result = Deidentifier.deidentify_text("Diagnosis: Atrial Fibrillation")
        assert "Atrial Fibrillation" in result

    def test_empty_text_does_not_crash(self):
        assert Deidentifier.deidentify_text("") == ""
        assert Deidentifier.deidentify_text(None) is None

    def test_name_masking_is_case_insensitive(self):
        result = Deidentifier.deidentify_text("seen by anjali kapoor today", names=["Anjali Kapoor"])
        assert "anjali kapoor" not in result.lower()


class TestDeidentifyEntities:

    def test_masks_patient_and_doctor_names(self):
        entities = {
            "patient": "Anjali Kapoor",
            "doctor": "Dr. Vikram Nair",
            "diagnosis": ["Atrial Fibrillation"],
            "symptoms": ["Palpitations"],
            "medicines": ["Apixaban 5mg"],
            "lab_tests": ["ECG normal"],
            "follow_up": "2026-11-02",
        }

        result = Deidentifier.deidentify_entities(entities)

        assert result["patient"] == "[NAME]"
        assert result["doctor"] == "[NAME]"
        assert result["follow_up"] == "[DATE]"

    def test_clinical_fields_keep_their_medical_content(self):
        entities = {
            "patient": "Anjali Kapoor",
            "doctor": "Dr. Vikram Nair",
            "diagnosis": ["Atrial Fibrillation"],
            "symptoms": [],
            "medicines": [],
            "lab_tests": [],
            "follow_up": "",
        }

        result = Deidentifier.deidentify_entities(entities)

        assert "Atrial Fibrillation" in result["diagnosis"][0]

    def test_a_name_mentioned_inside_a_clinical_field_is_still_masked(self):
        entities = {
            "patient": "Anjali Kapoor",
            "doctor": "Dr. Vikram Nair",
            "diagnosis": ["Seen by Dr. Vikram Nair for Atrial Fibrillation"],
            "symptoms": [],
            "medicines": [],
            "lab_tests": [],
            "follow_up": "",
        }

        result = Deidentifier.deidentify_entities(entities)

        assert "Vikram Nair" not in result["diagnosis"][0]
        assert "Atrial Fibrillation" in result["diagnosis"][0]

    def test_missing_optional_fields_do_not_crash(self):
        result = Deidentifier.deidentify_entities({"patient": "", "doctor": ""})
        assert result["patient"] == ""
