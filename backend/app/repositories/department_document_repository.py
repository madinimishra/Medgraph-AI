from sqlalchemy.orm import Session

from app.models.ingestion.department_doc import DepartmentDocument


class DepartmentDocumentRepository:

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(DepartmentDocument)
            .filter(
                DepartmentDocument.name == name
            )
            .first()
        )

    @staticmethod
    def create(db: Session, department: DepartmentDocument):
        db.add(department)
        db.commit()
        db.refresh(department)
        return department

    @staticmethod
    def get_or_create(
        db: Session,
        name: str,
        hospital_id: int
    ):

        department = DepartmentDocumentRepository.get_by_name(
            db,
            name
        )

        if department:
            return department

        department = DepartmentDocument(
            name=name,
            hospital_id=hospital_id
        )

        return DepartmentDocumentRepository.create(
            db,
            department
        )