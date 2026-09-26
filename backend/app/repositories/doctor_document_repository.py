from sqlalchemy.orm import Session

from app.models.ingestion.doctor_doc import DoctorDocument


class DoctorDocumentRepository:

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(DoctorDocument)
            .filter(
                DoctorDocument.name == name
            )
            .first()
        )

    @staticmethod
    def create(db: Session, doctor: DoctorDocument):
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        return doctor

    @staticmethod
    def get_or_create(
        db: Session,
        name: str,
        department_id: int
    ):

        doctor = DoctorDocumentRepository.get_by_name(
            db,
            name
        )

        if doctor:
            return doctor

        doctor = DoctorDocument(
            name=name,
            department_id=department_id
        )

        return DoctorDocumentRepository.create(
            db,
            doctor
        )