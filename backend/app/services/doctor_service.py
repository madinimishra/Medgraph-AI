from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorCreate


class DoctorService:

    @staticmethod
    def create_doctor(
        db: Session,
        doctor: DoctorCreate
    ):

        if DoctorRepository.get_by_email(
            db,
            doctor.email
        ):
            raise Exception("Doctor already exists")

        new_doctor = Doctor(
            **doctor.model_dump()
        )

        return DoctorRepository.create(
            db,
            new_doctor
        )