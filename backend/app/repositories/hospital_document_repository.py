from sqlalchemy.orm import Session

from app.models.ingestion.hospital_doc import HospitalDocument


class HospitalDocumentRepository:

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(HospitalDocument)
            .filter(HospitalDocument.name == name)
            .first()
        )

    @staticmethod
    def create(db: Session, hospital: HospitalDocument):
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
        return hospital

    @staticmethod
    def get_or_create(db: Session, name: str):

        hospital = HospitalDocumentRepository.get_by_name(
            db,
            name
        )

        if hospital:
            return hospital

        hospital = HospitalDocument(
            name=name
        )

        return HospitalDocumentRepository.create(
            db,
            hospital
        )