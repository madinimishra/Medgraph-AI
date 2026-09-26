from sqlalchemy.orm import Session

from app.models.ingestion.medical_record_doc import MedicalRecordDocument


class MedicalRecordDocumentRepository:

    @staticmethod
    def get_by_patient(db, patient_id):
        return (
            db.query(MedicalRecordDocument)
            .filter(MedicalRecordDocument.patient_id == patient_id)
            .first()
        )

    @staticmethod
    def create(db, record):
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_or_create(
        db,
        patient_id,
        doctor_id,
        diagnosis,
        symptoms,
        medicines,
        lab_tests,
        follow_up
    ):

        record = (
            db.query(MedicalRecordDocument)
            .filter(
                MedicalRecordDocument.patient_id == patient_id,
                MedicalRecordDocument.doctor_id == doctor_id
            )
            .first()
        )

        if record:
            return record

        record = MedicalRecordDocument(
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            symptoms=symptoms,
            medicines=medicines,
            lab_tests=lab_tests,
            follow_up=follow_up
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record