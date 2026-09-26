from sqlalchemy.orm import Session

from app.models.medical_record import MedicalRecord


class MedicalRecordRepository:

    @staticmethod
    def create(
        db: Session,
        record: MedicalRecord
    ):
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_all(db: Session):
        return db.query(MedicalRecord).all()

    @staticmethod
    def get_by_patient(
        db: Session,
        patient_id: int
    ):
        return (
            db.query(MedicalRecord)
            .filter(
                MedicalRecord.patient_id == patient_id
            )
            .all()
        )