from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.repositories.hospital_repository import HospitalRepository
from app.schemas.hospital import HospitalCreate


class HospitalService:

    @staticmethod
    def create_hospital(
        db: Session,
        hospital: HospitalCreate
    ):

        if HospitalRepository.get_by_code(
            db,
            hospital.hospital_code
        ):
            raise Exception("Hospital already exists")

        new_hospital = Hospital(**hospital.model_dump())

        return HospitalRepository.create(
            db,
            new_hospital
        )