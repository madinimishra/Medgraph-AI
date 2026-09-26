from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate
from app.repositories.patient_repository import PatientRepository


class PatientService:

    @staticmethod
    def create_patient(
        db: Session,
        patient: PatientCreate
    ):

        if PatientRepository.get_by_email(db, patient.email):
            raise Exception("Email already exists")

        if PatientRepository.get_by_phone(db, patient.phone):
            raise Exception("Phone already exists")

        patient_count = len(
            PatientRepository.get_all(db)
        ) + 1

        patient_code = f"PAT{patient_count:06d}"

        new_patient = Patient(
            patient_code=patient_code,
            **patient.model_dump()
        )

        return PatientRepository.create(
            db,
            new_patient
        )