from sqlalchemy.orm import Session

from app.models.hospital import Hospital


class HospitalRepository:

    @staticmethod
    def create(db: Session, hospital: Hospital):
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
        return hospital

    @staticmethod
    def get_all(db: Session):
        return db.query(Hospital).all()

    @staticmethod
    def get_by_code(db: Session, code: str):
        return (
            db.query(Hospital)
            .filter(Hospital.hospital_code == code)
            .first()
        )

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(Hospital)
            .filter(Hospital.hospital_name == name)
            .first()
        )

    @staticmethod
    def get_or_create(db: Session, name: str):

        hospital = HospitalRepository.get_by_name(db, name)

        if hospital:
            return hospital

        code = "HOSP-" + name[:3].upper()

        hospital = Hospital(
            hospital_code=code,
            hospital_name=name,
            address="Unknown",
            city="Unknown",
            state="Unknown",
            country="India"
        )

        return HospitalRepository.create(db, hospital)