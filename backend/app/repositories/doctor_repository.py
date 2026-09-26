from sqlalchemy.orm import Session

from app.models.doctor import Doctor


class DoctorRepository:

    @staticmethod
    def create(db: Session, doctor: Doctor):
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        return doctor

    @staticmethod
    def get_all(db: Session):
        return db.query(Doctor).all()

    @staticmethod
    def get_by_id(db: Session, doctor_id: int):
        return (
            db.query(Doctor)
            .filter(Doctor.id == doctor_id)
            .first()
        )

    @staticmethod
    def get_by_email(db: Session, email: str):
        return (
            db.query(Doctor)
            .filter(Doctor.email == email)
            .first()
        )

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(Doctor)
            .filter(Doctor.full_name == name)
            .first()
        )

    @staticmethod
    def get_or_create(
        db: Session,
        full_name: str,
        specialization: str,
        department_id: int
    ):

        doctor = DoctorRepository.get_by_name(
            db,
            full_name
        )

        if doctor:
            return doctor

        doctor = Doctor(
            doctor_code="DOC-" + full_name[:3].upper(),
            full_name=full_name,
            specialization=specialization,
            department_id=department_id,
            qualification="Unknown",
            experience=0,
            phone="0000000000",
            email=f"{full_name.lower().replace(' ','')}@hospital.com"
        )

        return DoctorRepository.create(
            db,
            doctor
        )