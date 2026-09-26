from sqlalchemy.orm import Session

from app.models.department import Department


class DepartmentRepository:

    @staticmethod
    def create(db: Session, department: Department):
        db.add(department)
        db.commit()
        db.refresh(department)
        return department

    @staticmethod
    def get_all(db: Session):
        return db.query(Department).all()

    @staticmethod
    def get_by_name(db: Session, name: str):
        return (
            db.query(Department)
            .filter(
                Department.department_name == name
            )
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, department_id: int):
        return (
            db.query(Department)
            .filter(
                Department.id == department_id
            )
            .first()
        )

    @staticmethod
    def get_or_create(
        db: Session,
        department_name: str,
        hospital_id: int
    ):

        department = DepartmentRepository.get_by_name(
            db,
            department_name
        )

        if department:
            return department

        department = Department(
            department_code="DEPT-" + department_name[:3].upper(),
            department_name=department_name,
            description="Imported from medical report",
            floor="Unknown",
            hod_name="Unknown",
            hospital_id=hospital_id
        )

        return DepartmentRepository.create(
            db,
            department
        )