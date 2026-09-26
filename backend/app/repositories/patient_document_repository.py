from sqlalchemy.orm import Session

from app.models.ingestion.patient_doc import PatientDocument


class PatientDocumentRepository:

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(PatientDocument)
            .filter(
                PatientDocument.name == name
            )
            .first()
        )

    @staticmethod
    def create(db: Session, patient: PatientDocument):
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def get_or_create(
        db: Session,
        name: str,
        hospital_id: int
    ):

        patient = PatientDocumentRepository.get_by_name(
            db,
            name
        )

        if patient:
            return patient

        patient = PatientDocument(
            name=name,
            hospital_id=hospital_id
        )

        return PatientDocumentRepository.create(
            db,
            patient
        )