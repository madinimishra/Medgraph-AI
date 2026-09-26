from sqlalchemy.orm import Session

from app.models.medical_record import MedicalRecord

from app.repositories.medical_record_repository import (
    MedicalRecordRepository
)

from app.schemas.medical_record import (
    MedicalRecordCreate
)


class MedicalRecordService:

    @staticmethod
    def create_record(
        db: Session,
        record: MedicalRecordCreate
    ):

        new_record = MedicalRecord(
            **record.model_dump()
        )

        return MedicalRecordRepository.create(
            db,
            new_record
        )